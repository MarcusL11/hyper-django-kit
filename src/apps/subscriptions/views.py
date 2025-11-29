from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpRequest
from django.contrib.auth import get_user_model
from django.urls import reverse
import stripe
from apps.core.payments.utils import get_or_create_customer
import logging
from djstripe.settings import djstripe_settings
from djstripe.models import Subscription, Product
import uuid

logger = logging.getLogger(__name__)


def index(request: HttpRequest):
    """
    Subscription landing page with pricing plans.
    Fetches all active products with their prices for client-side toggle.

    Uses Product-first approach:
    1. Query active Products with prefetched prices
    2. Attach custom metadata from METADATA_MAP
    3. Create plan_data for each Product+Price combination
    4. Separate into monthly and yearly lists
    5. Include user's subscription context for UI awareness
    """
    plans_monthly = []
    plans_yearly = []

    # Fetch active products with their prices in one query
    products = Product.objects.prefetch_related("prices").filter(active=True)

    for product in products:
        # Use subscription_metadata instead of app_metadata
        metadata = product.subscription_metadata

        # Skip products without subscription metadata (e.g., shop products)
        if not metadata:
            continue

        for price in product.prices.all():
            if not price.active:
                continue

            interval = price.recurring.get("interval") if price.recurring else None
            if interval not in ["month", "year"]:
                continue

            plan_data = {
                "order": metadata.order,
                "price": price,
                "metadata": metadata,
            }

            if interval == "month":
                plans_monthly.append(plan_data)
            elif interval == "year":
                plans_yearly.append(plan_data)

    # Sort by order (Starter=1, Standard=2, Premium=3)
    plans_monthly.sort(key=lambda x: x["order"])
    plans_yearly.sort(key=lambda x: x["order"])

    # Get user's current subscription context for UI awareness
    user_subscription = None
    user_product_id = None

    if request.user.is_authenticated:
        user_subscription = request.user.active_subscription  # type: ignore
        if user_subscription and user_subscription.product:
            user_product_id = user_subscription.product.id

    context = {
        "plans_monthly": plans_monthly,
        "plans_yearly": plans_yearly,
        "user_subscription": user_subscription,
        "user_product_id": user_product_id,
    }

    return render(request, "subscriptions/landing/index.html", context)


@require_POST
@login_required
def create_checkout_session(request: HttpRequest):
    """
    Create a Stripe Checkout Session for subscription purchase.

    This view handles the creation of a Stripe Checkout Session
    and redirects the user to Stripe's hosted checkout page.

    If user already has an active subscription, redirects to billing portal instead.

    Note: dj-stripe automatically links Customer to AUTH_USER_MODEL (CustomUser)
    via Customer.get_or_create(subscriber=request.user)
    """
    # Check if user already has active subscription
    if request.user.active_subscription:  # type: ignore
        return redirect("subscriptions:billing_portal")

    price_id = request.POST.get("price_id")

    if not price_id:
        logger.warning(
            f"create_checkout_session called without price_id by user {request.user.id}"  # type: ignore
        )
        return redirect("subscriptions:index")

    try:
        customer, created = get_or_create_customer(request.user)

        if created:
            logger.info(
                f"Created new customer {customer.id} for user {request.user.id}"  # type: ignore
            )

        stripe.api_key = djstripe_settings.STRIPE_SECRET_KEY

        # Create Stripe Checkout Session
        checkout_session = stripe.checkout.Session.create(
            customer=customer.id,
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                },
            ],
            mode="subscription",
            success_url=request.build_absolute_uri(
                reverse("subscriptions:subscription_confirm")
            )
            + "?session_id={CHECKOUT_SESSION_ID}",
            client_reference_id=str(request.user.id),  # type: ignore
            cancel_url=request.build_absolute_uri(
                reverse("subscriptions:subscription_canceled")
            ),
            metadata={},
        )

        logger.info(
            f"Created checkout session {checkout_session.id} for user {request.user.id}"  # type: ignore
        )

        return redirect(checkout_session.url, code=303)

    except Exception as e:
        logger.error(
            f"Unexpected error creating checkout session for user {request.user.id}: {e}"  # type: ignore
        )
        return redirect("subscriptions:index")


@login_required
def subscription_confirm(request: HttpRequest):
    """
    Display success message after successful checkout.

    Processes the Stripe session and links subscription to user.
    """
    session_id = request.GET.get("session_id")

    if not session_id:
        logger.error("subscription_confirm called without session_id")
        return redirect("subscriptions:index")

    try:
        # Retrieve the session ID from query parameters and fetch the session and its values
        stripe.api_key = djstripe_settings.STRIPE_SECRET_KEY
        session = stripe.checkout.Session.retrieve(session_id)

        if not session.client_reference_id:
            logger.error(f"Session {session_id} missing client_reference_id")
            return redirect("subscriptions:index")

        client_reference_id = uuid.UUID(session.client_reference_id)
        subscription_holder = get_user_model().objects.get(id=client_reference_id)

        # Ensure the subscription holder is the logged-in user
        if subscription_holder != request.user:
            logger.error(
                f"User {request.user.id} attempted to access session for user {subscription_holder.id}"  # type: ignore
            )
            return redirect("subscriptions:index")

        # Retrieve the subscription and sync it to the database
        subscription = stripe.Subscription.retrieve(session.subscription)
        djstripe_subscription = Subscription.sync_from_stripe_data(subscription)
        subscription_holder.subscription = djstripe_subscription
        subscription_holder.customer = djstripe_subscription.customer  # type: ignore
        subscription_holder.save()
        logger.info(f"User {request.user.id} completed checkout session {session_id}")  # type: ignore

        context = {
            "result_type": "success",
            "heading": "Subscription Successful!",
            "message": 'Thank you for subscribing to <span class="text-primary font-semibold">BookIDs</span>',
            "submessage": "Your subscription is now active. You can manage your subscription from your dashboard.",
            "primary_url": reverse("user_dashboard:index"),
            "primary_text": "Go to Dashboard",
        }

        return render(
            request, "subscriptions/checkout/subscription_success.html", context
        )

    except stripe.error.StripeError as e:
        logger.error(
            f"Stripe error in subscription_confirm for user {request.user.id}: {e}"
        )  # type: ignore
        return redirect("subscriptions:index")
    except (ValueError, get_user_model().DoesNotExist) as e:
        logger.error(f"Error processing session {session_id}: {e}")
        return redirect("subscriptions:index")
    except Exception as e:
        logger.error(
            f"Unexpected error in subscription_confirm for user {request.user.id}: {e}"
        )  # type: ignore
        return redirect("subscriptions:index")


@login_required
def subscription_canceled(request: HttpRequest):
    """
    Display cancellation message when user abandons checkout.

    User canceled the checkout process on Stripe's checkout page
    and was redirected back to this view.
    """
    logger.info(f"User {request.user.id} canceled checkout")  # type: ignore

    context = {
        "result_type": "warning",
        "heading": "Checkout Canceled",
        "message": "No worries! Your checkout was canceled.",
        "submessage": "You can return to our pricing page anytime to complete your subscription.",
        "primary_url": reverse("subscriptions:index") + "#pricing",
        "primary_text": "View Pricing",
        "secondary_url": reverse("user_dashboard:index"),
        "secondary_text": "Go to Dashboard",
    }

    return render(request, "subscriptions/checkout/subscription_canceled.html", context)


@login_required
def billing_portal(request: HttpRequest):
    """
    Redirect user to Stripe Customer Portal for subscription management.

    The Customer Portal allows users to:
    - Cancel subscription
    - Update payment method
    - View invoices
    - Update billing details
    - Change plans (if configured in Stripe Dashboard)

    This is the secure, Stripe-hosted way to manage subscriptions.
    """
    customer = request.user.customer  # type: ignore

    if not customer:
        logger.warning(
            f"User {request.user.id} attempted to access billing portal without customer"  # type: ignore
        )
        return redirect("subscriptions:index")

    stripe.api_key = djstripe_settings.STRIPE_SECRET_KEY

    try:
        # Create billing portal session
        portal_session = stripe.billing_portal.Session.create(
            customer=customer.id,
            return_url=request.build_absolute_uri(
                reverse("user_dashboard:subscription_management")
            ),
        )

        logger.info(
            f"Created billing portal session for user {request.user.id}"  # type: ignore
        )
        return redirect(portal_session.url, code=303)

    except Exception as e:
        logger.error(
            f"Error creating billing portal session for user {request.user.id}: {e}"  # type: ignore
        )
        # TODO: Return an error template
        return redirect("user_dashboard:subscription_management")
