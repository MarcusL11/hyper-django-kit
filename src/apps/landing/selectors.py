"""
Selectors for landing app.

Selectors are functions that fetch data from the database.
They encapsulate query logic and keep views thin.
"""
from typing import Dict, Any, Optional, List
from djstripe.models import Product


def get_pricing_plans() -> Dict[str, List[Dict[str, Any]]]:
    """
    Fetch and organize pricing plans for display.

    Queries active Products with prefetched prices from djstripe.
    Filters products that have subscription_metadata.
    Separates active prices into monthly and yearly plans.
    Sorts by metadata.order.

    Returns:
        Dict with keys 'plans_monthly' and 'plans_yearly', each containing
        a list of plan dictionaries with 'order', 'price', and 'metadata' keys.
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

    return {
        "plans_monthly": plans_monthly,
        "plans_yearly": plans_yearly,
    }


def get_user_subscription_context(user) -> Dict[str, Optional[Any]]:
    """
    Get user's subscription context for UI awareness.

    Args:
        user: Django User object or AnonymousUser

    Returns:
        Dict with keys 'user_subscription' and 'user_product_id'.
        Returns None values for unauthenticated users.
    """
    from djstripe.models import Subscription

    user_subscription = None
    user_product_id = None

    if user.is_authenticated and hasattr(user, "customer") and user.customer:
        # Single optimized query instead of using the property
        user_subscription = (
            Subscription.objects
            .filter(customer=user.customer, status__in=["active", "trialing"])
            .select_related("product")
            .order_by("-created")
            .first()
        )

        if user_subscription and user_subscription.product:
            user_product_id = user_subscription.product.id

    return {
        "user_subscription": user_subscription,
        "user_product_id": user_product_id,
    }
