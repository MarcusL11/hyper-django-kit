import logging

from django.shortcuts import render
from django.http import HttpRequest

from .selectors import get_pricing_plans, get_user_subscription_context

logger = logging.getLogger(__name__)


def index(request: HttpRequest):
    """
    Landing page with pricing plans.
    Displays active subscription plans and user's current subscription status.
    """
    try:
        pricing_plans = get_pricing_plans()
    except Exception as e:
        logger.error(
            "[landing:index] Error loading pricing plans: %s",
            str(e),
            exc_info=True
        )
        pricing_plans = {"plans_monthly": [], "plans_yearly": []}

    try:
        subscription_context = get_user_subscription_context(request.user)
    except Exception as e:
        logger.error(
            "[landing:index] Error loading subscription context: %s",
            str(e),
            exc_info=True
        )
        subscription_context = {"user_subscription": None, "user_product_id": None}

    context = {
        **pricing_plans,
        **subscription_context,
    }

    return render(request, "landing/index.html", context)
