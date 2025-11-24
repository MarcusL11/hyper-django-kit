from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from djstripe.models import Product
from apps.shop.models import Order
import logging
from allauth.account.models import EmailAddress
from allauth.account.forms import AddEmailForm, ChangePasswordForm
from allauth.usersessions.models import UserSession
from allauth.usersessions.forms import ManageUserSessionsForm
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import redirect
from datastar_py.consts import ElementPatchMode
from datastar_py.django import (
    DatastarResponse,
    ServerSentEventGenerator as SSE,
    read_signals,
)
from apps.user_dashboard.forms import UserProfileForm  # type: ignore
from django.core.paginator import Paginator
from django.conf import settings


logger = logging.getLogger(__name__)


@login_required
def index(request: HttpRequest):
    # Context processor now handles details_account and details_subscription
    return render(request, "user_dashboard/index.html")


@login_required
@require_POST
def store_user_sidebar_state(request: HttpRequest):
    """
    Stores the state of the sidebar details element component.
    """
    signals = read_signals(request)
    request.session["user_sidebar_state"] = signals
    return HttpResponse(status=204)


@login_required
def subscription_management(request: HttpRequest):
    user = request.user
    has_subscription = False
    if user.active_subscription:  # type: ignore
        subscription = user.active_subscription  # type: ignore
        plan_name = user.active_subscription.product.name
        has_subscription = True
    else:
        subscription = ""

    context = {
        "user": user,
        "subscription": subscription,
        "plan_name": plan_name if has_subscription else "",
        "has_subscription": has_subscription,
    }
    return render(
        request, "user_dashboard/subscription/subscription_management.html", context
    )


@login_required
def subscription_invoices(request: HttpRequest):
    user = request.user
    invoices = []
    if user.customer:  # type: ignore
        invoices = user.customer.invoices.all().order_by("-created")[:20]  # type: ignore

    context = {
        "user": user,
        "invoices": invoices,
    }

    return render(
        request, "user_dashboard/subscription/subscription_invoices.html", context
    )


@login_required
def subscription_plans(request: HttpRequest):
    user = request.user
    plans_monthly = []
    plans_yearly = []
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

    # Sort by order
    plans_monthly.sort(key=lambda x: x["order"])
    plans_yearly.sort(key=lambda x: x["order"])

    # Get user's subscription context
    user_subscription = user.active_subscription  # type: ignore
    user_product_id = (
        user_subscription.product.id  # type: ignore
        if user_subscription and user_subscription.product  # type: ignore
        else None
    )

    context = {
        "user": user,
        "plans_monthly": plans_monthly,
        "plans_yearly": plans_yearly,
        "user_subscription": user_subscription,
        "user_product_id": user_product_id,
    }

    return render(
        request, "user_dashboard/subscription/subscription_plans.html", context
    )


@login_required
@require_http_methods(["GET", "POST"])
def account_profile(request: HttpRequest):
    """
    Handle user profile updates including profile image upload.
    Uses traditional form submission (not Datastar).
    """
    user = request.user

    if request.method == "POST":
        # Handle traditional form submission with FILES
        profile_form = UserProfileForm(
            data=request.POST, files=request.FILES, instance=user
        )

        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Your profile has been updated successfully.")
            # Redirect to prevent form resubmission
            return redirect("user_dashboard:account_profile")
        else:
            # Form has errors - will be displayed in template
            logger.warning(
                f"Profile update failed - User: {user.id} ({user.username}), "  # type: ignore
                f"Errors: {profile_form.errors.as_json()}"
            )

            # Add generic error message
            if profile_form.non_field_errors():
                messages.error(request, str(profile_form.non_field_errors()[0]))
            else:
                messages.error(
                    request, "Failed to update profile. Please check the errors below."
                )

    # GET request or failed POST - show form
    else:
        profile_form = UserProfileForm(instance=user)

    context = {
        "user": user,
        "profile_form": profile_form,
        # Context processor now handles details_account and details_subscription
    }
    return render(request, "user_dashboard/account/account_profile.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def account_email(request: HttpRequest):
    user = request.user
    email_addresses = EmailAddress.objects.filter(user=user).order_by("id")
    add_form = None
    context = {}

    if request.method == "POST":
        add_form = AddEmailForm(data=request.POST, user=user)

        if add_form.is_valid():
            add_form.save(request)
            add_form = AddEmailForm()

            return render(
                request,
                "user_dashboard/account/account_email.html",
                {
                    "user": user,
                    "email_addresses": EmailAddress.objects.filter(user=user).order_by(
                        "id"
                    ),
                    "add_form": add_form,
                },
            )

        else:
            context = {
                "user": user,
                "email_addresses": email_addresses,
                "add_form": add_form,
            }
            return render(
                request,
                "user_dashboard/account/account_email.html",
                context,
            )

    # GET request - normal full page load (Refresh Case)
    else:
        add_form = AddEmailForm()
        context = {
            "user": user,
            "email_addresses": email_addresses,
            "add_form": add_form,
        }
        return render(request, "user_dashboard/account/account_email.html", context)


@login_required
@require_POST
def account_email_make_primary(request: HttpRequest):
    user = request.user
    email_id = request.POST.get("email_id")
    email_addresses = EmailAddress.objects.filter(user=user).order_by("id")
    email = get_object_or_404(email_addresses, pk=email_id)
    email.set_as_primary()

    return DatastarResponse(
        [
            SSE.patch_elements(  # type: ignore
                mode=ElementPatchMode.OUTER,
                selector="#email-info-container",
                elements=render_to_string(
                    template_name="user_dashboard/account/account_email.html#email-info-partial",
                    request=request,
                    context=dict(
                        email_addresses=email_addresses,
                        user=user,
                    ),
                ),
            )
        ]
    )


@login_required
@require_POST
def account_email_remove(request: HttpRequest):
    user = request.user
    email_id = request.POST.get("email_id")
    # Use django message for feedback

    try:
        email = EmailAddress.objects.get(pk=email_id, user=user)

        if email.primary:
            message = "You cannot remove your primary email address."
            messages.error(request, message)
            logger.warning(
                f"User {user.id} attempted to remove primary email {email.email}"  # type: ignore
            )
        else:
            message = f"Email address {email.email} has been removed."
            messages.success(request, message)
            logger.info(f"User {user.id} removed email {email.email}")  # type: ignore
            email.delete()

    except EmailAddress.DoesNotExist:
        # use Django Message framework for feedback
        logger.warning(f"User {user.id} attempted to remove non-existent email")  # type: ignore
        message = "Email address not found."
        messages.error(request, message)

    # Render updated email list
    email_addresses = EmailAddress.objects.filter(user=user).order_by("id")
    context = {"email_addresses": email_addresses, "user": user}
    return render(request, "user_dashboard/account/account_email.html", context)


@login_required
@require_POST
def account_email_resend_verification(request: HttpRequest):
    """
    Resend verification email for an email address.
    Demonstrates toast notification pattern with Datastar.
    """

    user = request.user
    email_id = request.POST.get("email_id")

    # Determine message based on validation and action result
    try:
        email = EmailAddress.objects.get(pk=email_id, user=user)

        if email.verified:
            message = "This email address is already verified."
            messages.info(request, message)
            logger.info(
                f"User {user.id} attempted to resend verification for already verified email"  # type: ignore
            )
        else:
            message = f"A verification email has been sent to {email.email}."
            messages.success(request, message)
            logger.info(
                f"User {user.id} resent verification email to {email.email}"  # type: ignore
            )
            email.send_confirmation(request)

    except EmailAddress.DoesNotExist:
        message = "Email address not found."
        messages.error(request, message)
        logger.warning(
            f"User {user.id} attempted to resend verification for non-existent email"
        )

    # Render updated email list
    email_addresses = EmailAddress.objects.filter(user=user).order_by("id")
    context = {"email_addresses": email_addresses, "user": user}

    # Return both patches: update content + replace toast (INNER mode shows latest only)
    return render(request, "user_dashboard/account/account_email.html", context)


@login_required
def account_password(request: HttpRequest):
    user = request.user

    if request.method == "POST":
        password_form = ChangePasswordForm(data=request.POST, user=user)

        if password_form.is_valid():
            password_form.save()
            password_form = ChangePasswordForm(user=user)
            message = "Your password has been changed successfully."
            messages.success(request, message)
            # redirect user to login page after password change
            return redirect(reverse("account_login"))
        else:
            # return errors to user
            logger.warning(
                f"Password change failed - User: {user.id} ({user.username}), "  # type: ignore
                f"Errors: {password_form.errors.as_json()}"
            )
            message = "Failed to change password. Please correct the errors below."
            messages.error(request, message)

        # Render updated form (with errors or cleared)
        context = {"password_form": password_form, "user": user}

        return render(request, "user_dashboard/account/account_password.html", context)

    else:
        password_form = ChangePasswordForm(user=user)
        context = {
            "user": user,
            "password_form": password_form,
        }
        return render(request, "user_dashboard/account/account_password.html", context)


@login_required
def account_sessions(request: HttpRequest):
    user = request.user

    if request.method == "POST":
        # Use Django-Allauth's ManageUserSessionsForm for proper validation and session handling
        form = ManageUserSessionsForm(data=request.POST, request=request)

        if form.is_valid():
            try:
                # django message for feedback
                messages.success(
                    request, "Other sessions have been signed out successfully."
                )
                logger.info(f"User {user.id} signed out other sessions")  # type: ignore
                # This calls flows.sessions.end_other_sessions(request, request.user)
                form.save(request)
            except Exception as e:
                messages.error(
                    request,
                    "An error occurred while signing out other sessions. Please try again.",
                )
                logger.error(
                    f"Error signing out other sessions for user {user.id}: {e}"  # type: ignore
                )
        else:
            messages.error(
                request,
                "Invalid request to manage sessions. Please try again.",
            )
            error = form.errors.as_json()
            logger.warning(
                f"Invalid ManageUserSessionsForm for user {user.id}: {error}"  # type: ignore
            )

        # Get updated session list (purge_and_list removes expired sessions)
        sessions = UserSession.objects.purge_and_list(user)

        return render(
            request,
            "user_dashboard/account/account_sessions.html",
            {"user": user, "sessions": sessions},
        )

    # GET request - normal full page load (Refresh Case)
    else:
        # Use purge_and_list to automatically remove expired sessions
        sessions = UserSession.objects.purge_and_list(user)
        context = {
            "user": user,
            "sessions": sessions,
        }
        return render(request, "user_dashboard/account/account_sessions.html", context)


# Orders Management Views
@login_required
def orders_list(request: HttpRequest):
    """
    Display list of all shop orders for the logged-in user.
    Optimized query to include invoice access via session.payment_intent.
    """

    orders = (
        Order.objects.filter(user=request.user)
        .select_related(
            "session",
            "session__payment_intent",
        )
        .order_by("-created_at")
    )

    paginator = Paginator(orders, settings.ORDER_LIST_ITEM_PER_PAGE)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)  # type: ignore

    context = {"page_obj": page_obj}
    return render(request, "user_dashboard/orders/orders_list.html", context)


@login_required
def order_detail(request: HttpRequest, order_id: str):
    """
    Display detailed view of a single order including all products purchased.

    Args:
        order_id: UUID of the order
    """
    order = get_object_or_404(
        Order.objects.select_related(
            "session",
            "session__payment_intent",
            "basket",
        ).prefetch_related("basket__items__product"),
        id=order_id,
        user=request.user,  # Security: ensure order belongs to user
    )

    # Get products from basket if available
    products = []
    if order.basket:
        for item in order.basket.items.all():
            products.append(
                {
                    "basket_item": item,
                    "shop_product": item.shop_product,  # Access via shop_metadata
                    "quantity": item.quantity,
                    "line_total_dollars": item.line_total_dollars,
                }
            )

    context = {
        "order": order,
        "products": products,
    }
    return render(request, "user_dashboard/orders/order_detail.html", context)


@login_required
@require_POST
def account_profile_delete_image(request: HttpRequest):
    """
    Delete user's profile image.
    """
    user = request.user

    if user.profile_image:  # type: ignore
        user.profile_image.delete(save=True)  # type: ignore
        messages.success(request, "Profile picture removed successfully.")
        logger.info(f"User {user.id} deleted profile image")  # type: ignore
        return redirect("user_dashboard:account_profile")

    else:
        messages.info(request, "No profile picture to remove.")

    return redirect("user_dashboard:account_profile")
