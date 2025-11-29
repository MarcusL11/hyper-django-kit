from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.conf import settings
import logging
import stripe
from djstripe.settings import djstripe_settings
from djstripe.models import (
    Product as StripeProduct,
    Price as StripePrice,
    Session as StripeSession,
)
from apps.core.payments.utils import get_or_create_customer
from apps.shop.models import ShopProduct, ShopCategory, Basket, BasketItem, Order

logger = logging.getLogger(__name__)


def product_list(request: HttpRequest) -> HttpResponse:
    page_number = request.GET.get("page", 1)
    category_slug = request.GET.get("category", "")
    sort_option = request.GET.get("sort", "")

    queryset = (
        ShopProduct.objects.filter(is_active=True)
        .prefetch_related("images")
        .select_related("category")
    )

    categories = ShopCategory.objects.filter(is_active=True)

    # Apply category filter
    if category_slug:
        queryset = queryset.filter(category__slug=category_slug)

    # Apply sorting
    if sort_option == "date_new":
        queryset = queryset.order_by("-created_at", "name")
    elif sort_option == "date_old":
        queryset = queryset.order_by("created_at", "name")
    elif sort_option in ["price_asc", "price_desc"]:
        # For price sorting, fetch products and sort in Python
        # because price is stored in Stripe's Product.default_price
        products_list = list(queryset)

        def get_price(product):
            if product.stripe_product and product.stripe_product.default_price:
                return product.stripe_product.default_price.unit_amount or 0
            return 0

        products_list.sort(key=get_price, reverse=(sort_option == "price_desc"))
        queryset = products_list
    else:
        # Default: sort by sort_order, then name
        queryset = queryset.order_by("sort_order", "name")

    # Pagination
    paginator = Paginator(queryset, settings.SHOP_PRODUCTS_PER_PAGE)
    page_obj = paginator.get_page(page_number)  # type: ignore

    # Attach cover images to products
    for product in page_obj:
        if product.images.exists():
            # Set first image as cover in a temporary attribute cover_image
            product.cover_image = product.images.first().image
        else:
            product.cover_image = settings.DEFAULT_PRODUCT_IMAGE

    # Context for templates
    context = {
        "products": page_obj,
        "page_obj": page_obj,
        "categories": categories,
        "selected_category": category_slug,
        "selected_sort": sort_option,
    }

    return render(request, "shop/products/product_list.html", context)


def product_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """
    Product detail page using ShopProduct + djstripe.Product.

    Data flow:
    1. Look up ShopProduct by slug
    2. Get djstripe.Product via shop_product.stripe_product
    3. Use ShopProduct for UI (name, images, category)
    4. Use djstripe.Product for pricing
    """
    shop_product = get_object_or_404(
        ShopProduct.objects.prefetch_related("images"), slug=slug, is_active=True
    )

    # Get associated Stripe product
    stripe_product = shop_product.stripe_product
    if not stripe_product:
        logger.error(f"Stripe product {shop_product.product_id} not synced")
        # TODO: Use toast notification with Datastar for dynamic notification without page reload
        messages.error(request, "Product not available")
        return redirect("shop:product_list")

    # Get default price from djstripe
    stripe_price = stripe_product.default_price
    if not stripe_price:
        logger.error(f"No default price for {stripe_product.id}")
        # TODO: Use toast notification with Datastar for dynamic notification without page reload
        messages.error(request, "Product pricing not available")
        return redirect("shop:product_list")

    # Build images list from ShopProduct
    images = []
    for img in shop_product.images.all():
        if img.image:
            images.append(img.image.url)

    # Fallback to mock images if no uploads yet
    if not images:
        images = [
            "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=600&h=600&fit=crop",
            "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=600&h=600&fit=crop",
            "https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?w=600&h=600&fit=crop",
        ]

    # Build context mixing both sources
    product = {
        # From ShopProduct (UI/admin data)
        "name": shop_product.name,
        "slug": shop_product.slug,
        "description": shop_product.description
        or "This search-and-find story is bursting with brightly-colored adventure. Is that your child at the beach? Exploring the fire station? Full of things to count, discover, and enjoy, your child will love spotting themselves on every page of this book.",
        "category": shop_product.category.name if shop_product.category else "",
        "is_new": shop_product.is_new,
        "is_popular": shop_product.is_popular,
        "images": images,
        # From djstripe.Product (Stripe source of truth)
        "stripe_product_id": stripe_product.id,
        "price_id": stripe_price.id,
        "price": stripe_price.unit_amount / 100,
        "currency": stripe_price.currency.upper(),
        # Template compatibility
        "languages": ["English (US)", "Spanish (ES)"],
        "personalization": "Upload a special photo",
        "accordions": [
            {
                "title": "How is the book personalized?",
                "content": "You can upload a photo of your child that will be incorporated into the illustrations throughout the book. The photo will be professionally edited to match the book's artistic style.",
            },
            {
                "title": "What's the story?",
                "content": "Join your little one on exciting adventures across different locations! From bustling city streets to peaceful beach scenes, each page is packed with colorful details to discover. Children will delight in finding themselves hidden in each beautifully illustrated scene.",
            },
            {
                "title": "Size & quality",
                "content": "Hardcover book measuring 8.5 x 11 inches with 34 full-color pages. Printed on premium 150gsm paper with a glossy finish. Professional binding ensures durability for years of reading enjoyment.",
            },
        ],
    }

    return render(
        request, "shop/product_detail/product_detail.html", {"product": product}
    )


# Basket Management Views


@require_POST
@login_required
def add_to_basket(request: HttpRequest):
    """
    Add product to user's basket.
    Creates basket if it doesn't exist, updates quantity if product already in basket.
    """
    price_id = request.POST.get("price_id")
    stripe_product_id = request.POST.get("stripe_product_id")
    quantity = int(request.POST.get("quantity", 1))

    if not price_id or not stripe_product_id:
        logger.error("Missing price_id or stripe_product_id in add_to_basket")
        # TODO: Use toast notification with Datastar for dynamic notification without page reload
        messages.error(request, "Could not add product to basket.")
        return redirect("shop:product_list")

    try:
        # Get or create active basket for user
        basket, _ = Basket.objects.get_or_create(user=request.user, checked_out=False)

        # Get djstripe.Product directly (BasketItem links to djstripe.Product)
        try:
            stripe_product = StripeProduct.objects.get(id=stripe_product_id)
        except StripeProduct.DoesNotExist:
            logger.error(f"StripeProduct {stripe_product_id} not found")
            # TODO: Use toast notification with Datastar for dynamic notification without page reload
            messages.error(request, "Product not found. Please contact support.")
            return redirect("shop:product_list")

        # Check if this product is already in basket
        basket_item, item_created = BasketItem.objects.get_or_create(
            basket=basket,
            product=stripe_product,  # FK to djstripe.Product
            defaults={"quantity": quantity},
        )

        if not item_created:
            # Product already in basket, update quantity
            basket_item.quantity += quantity
            basket_item.save()
            messages.success(request, "Updated quantity in your basket.")
        else:
            messages.success(request, "Added to your basket!")

        logger.info(
            f"Added product {stripe_product.id} to basket {basket.id} for user {request.user.id}"
        )
        return redirect("shop:view_basket")

    except Exception as e:
        logger.error(f"Error adding to basket: {e}")
        # TODO: Use toast notification with Datastar for dynamic notification without page reload
        messages.error(request, "Could not add product to basket.")
        return redirect("shop:product_list")


@login_required
def view_basket(request: HttpRequest):
    """Display user's basket with all items"""
    try:
        basket = Basket.objects.get(user=request.user, checked_out=False)
    except Basket.DoesNotExist:
        basket = None

    context = {
        "basket": basket,
    }

    return render(request, "shop/basket/basket.html", context)


@require_POST
@login_required
def update_basket_item(request: HttpRequest, item_id: str):
    """Update quantity of a basket item"""
    quantity = int(request.POST.get("quantity", 1))

    if quantity < 1:
        # TODO: Use toast notification with Datastar for dynamic notification without page reload
        messages.error(request, "Quantity must be at least 1.")
        return redirect("shop:view_basket")

    try:
        basket_item = get_object_or_404(
            BasketItem, id=item_id, basket__user=request.user, basket__checked_out=False
        )

        basket_item.quantity = quantity
        basket_item.save()

        messages.success(request, "Updated quantity.")
        logger.info(f"Updated basket item {item_id} quantity to {quantity}")

    except Exception as e:
        logger.error(f"Error updating basket item: {e}")
        # TODO: Use toast notification with Datastar for dynamic notification without page reload
        messages.error(request, "Could not update item.")

    return redirect("shop:view_basket")


@require_POST
@login_required
def remove_basket_item(request: HttpRequest, item_id: str):
    """Remove item from basket"""
    try:
        basket_item = get_object_or_404(
            BasketItem, id=item_id, basket__user=request.user, basket__checked_out=False
        )

        basket_item.delete()
        messages.success(request, "Removed from basket.")
        logger.info(f"Removed basket item {item_id}")

    except Exception as e:
        logger.error(f"Error removing basket item: {e}")
        # TODO: Use toast notification with Datastar for dynamic notification without page reload
        messages.error(request, "Could not remove item.")

    return redirect("shop:view_basket")


# Checkout Flow Views


@require_POST
@login_required
def create_checkout_session(request: HttpRequest):
    """
    Create Stripe Checkout Session from user's basket.
    Reads all items from basket and creates line_items for Stripe.
    """
    try:
        # Get user's active basket
        basket = Basket.objects.get(user=request.user, checked_out=False)

        if basket.is_empty:
            # TODO: Use toast notification with Datastar for dynamic notification without page reload
            messages.error(request, "Your basket is empty.")
            return redirect("shop:view_basket")

        # Get or create Stripe customer
        customer, created = get_or_create_customer(request.user)

        if created:
            logger.info(
                f"Created new customer {customer.id} for user {request.user.id}"  # type: ignore
            )

        stripe.api_key = djstripe_settings.STRIPE_SECRET_KEY

        # Build line_items from basket
        line_items = []
        for item in basket.items.all():
            if item.product.default_price:
                line_items.append(
                    {"price": item.product.default_price.id, "quantity": item.quantity}
                )

        if not line_items:
            # TODO: Use toast notification with Datastar for dynamic notification without page reload
            messages.error(request, "No valid items in basket.")
            return redirect("shop:view_basket")

        # Create Stripe Checkout Session
        checkout_session = stripe.checkout.Session.create(
            customer=customer.id,
            line_items=line_items,
            mode="payment",  # One-time payment
            success_url=request.build_absolute_uri(reverse("shop:order_confirm"))
            + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.build_absolute_uri(reverse("shop:checkout_canceled")),
            client_reference_id=str(request.user.id),
            metadata={
                "basket_id": str(basket.id),
                "user_id": str(request.user.id),
            },
        )

        logger.info(
            f"Created checkout session {checkout_session.id} for basket {basket.id}"
        )
        return redirect(checkout_session.url, code=303)

    except Basket.DoesNotExist:
        # TODO: Use toast notification with Datastar for dynamic notification without page reload
        messages.error(request, "Your basket is empty.")
        return redirect("shop:view_basket")
    except Exception as e:
        logger.error(f"Checkout session creation failed: {e}")
        # TODO: Use toast notification with Datastar for dynamic notification without page reload
        messages.error(request, "Could not start checkout. Please try again.")
        return redirect("shop:view_basket")


@login_required
def order_confirm(request: HttpRequest):
    """
    Success page after payment.
    Creates Order record and marks basket as checked out.
    """
    session_id = request.GET.get("session_id")

    if not session_id:
        logger.error("No session_id in order_confirm")
        # TODO: Use toast notification with Datastar for dynamic notification without page reload
        messages.error(request, "Invalid order confirmation.")
        return redirect("shop:product_list")

    try:
        # Retrieve session with expanded data
        stripe.api_key = djstripe_settings.STRIPE_SECRET_KEY
        session = stripe.checkout.Session.retrieve(
            session_id, expand=["line_items", "payment_intent"]
        )

        # Security: verify user
        if str(request.user.id) != session.client_reference_id:
            logger.error(
                f"User mismatch in order_confirm: {request.user.id} != {session.client_reference_id}"
            )
            # TODO: Use toast notification with Datastar for dynamic notification without page reload
            messages.error(request, "Invalid order confirmation.")
            return redirect("shop:product_list")

        # Get or sync djstripe Session
        djstripe_session = StripeSession.sync_from_stripe_data(session)

        # Get basket from metadata
        basket_id = session.metadata.get("basket_id")
        basket = None
        if basket_id:
            try:
                basket = Basket.objects.get(id=basket_id, user=request.user)
            except Basket.DoesNotExist:
                logger.warning(f"Basket {basket_id} not found for order")

        # Create Order (with get_or_create to prevent duplicates)
        # NO primary_product field per user feedback
        order, created = Order.objects.get_or_create(
            session=djstripe_session,
            defaults={
                "user": request.user,
                "basket": basket,
            },
        )

        # Mark basket as checked out
        if basket and not basket.checked_out:
            basket.checked_out = True
            basket.save()
            logger.info(f"Marked basket {basket.id} as checked out")

        if created:
            logger.info(f"Created order {order.id} for session {session_id}")
        else:
            logger.info(f"Order {order.id} already exists for session {session_id}")

        context = {
            "order": order,
            "primary_url": reverse("user_dashboard:index"),
            "secondary_url": reverse("shop:product_list"),
        }

        return render(request, "shop/checkout/order_success.html", context)

    except Exception as e:
        logger.error(f"Order confirm error: {e}")
        # TODO: Use toast notification with Datastar for dynamic notification without page reload
        messages.error(request, "Could not confirm order. Please contact support.")
        return redirect("shop:product_list")


@login_required
def checkout_canceled(request: HttpRequest):
    """Checkout was canceled by user"""
    messages.info(request, "Checkout was canceled. Your basket is still available.")

    context = {
        "primary_url": reverse("shop:view_basket"),
        "secondary_url": reverse("shop:product_list"),
    }

    return render(request, "shop/checkout/checkout_canceled.html", context)
