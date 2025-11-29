"""
Shared payment utilities for Stripe integration.

These utilities are used by both the subscriptions and shop apps
to interact with Stripe and dj-stripe.
"""

from typing import Optional, Tuple
from django.contrib.auth import get_user_model
from djstripe.models import Customer
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


# Delete
def get_or_create_customer(user: User) -> Tuple[Customer, bool]:
    """
    Get or create a dj-stripe Customer for a Django user.

    This function handles the customer creation and links it to the
    Django user (AUTH_USER_MODEL). dj-stripe automatically manages
    the relationship between Customer and the subscriber model.

    Args:
        user: Django user instance (AUTH_USER_MODEL)

    Returns:
        Tuple of (Customer instance, created boolean)

    Example:
        customer, created = get_or_create_customer(request.user)
        if created:
            logger.info(f"Created new customer for user {user.id}")
    """
    try:
        customer, created = Customer.get_or_create(subscriber=user)

        if created:
            logger.info(
                f"Created new Stripe customer for user {user.id} (username: {user.username})"
            )

        return customer, created

    except Exception as e:
        logger.error(f"Error creating/retrieving customer for user {user.id}: {e}")
        raise


def format_stripe_amount(amount_in_cents: int, currency: str = "usd") -> str:
    """
    Format a Stripe amount (in cents) to a human-readable string.

    Args:
        amount_in_cents: Amount in cents (e.g., 2999 for $29.99)
        currency: Currency code (default: "usd")

    Returns:
        Formatted amount string (e.g., "$29.99")

    Example:
        >>> format_stripe_amount(2999)
        '$29.99'
        >>> format_stripe_amount(5000)
        '$50.00'
    """
    if amount_in_cents is None:
        return "$0.00"

    amount_in_dollars = amount_in_cents / 100

    # Simple USD formatting for now
    # TODO: Add support for other currencies if needed
    if currency.lower() == "usd":
        return f"${amount_in_dollars:.2f}"

    return f"{amount_in_dollars:.2f} {currency.upper()}"


def get_customer_by_stripe_id(stripe_customer_id: str) -> Optional[Customer]:
    """
    Retrieve a dj-stripe Customer by their Stripe customer ID.

    Args:
        stripe_customer_id: Stripe customer ID (e.g., "cus_...")

    Returns:
        Customer instance or None if not found

    Example:
        customer = get_customer_by_stripe_id("cus_ABC123")
        if customer:
            user = customer.subscriber
    """
    try:
        return Customer.objects.get(id=stripe_customer_id)
    except Customer.DoesNotExist:
        logger.warning(f"Customer not found for Stripe ID: {stripe_customer_id}")
        return None


def get_customer_by_user(user: User) -> Optional[Customer]:
    """
    Retrieve a dj-stripe Customer by their Django user.

    Returns None if the customer doesn't exist (user has never made a purchase).
    This is useful for checking if a user has an existing Stripe Customer before
    creating checkout sessions, or for displaying billing information.

    Args:
        user: Django user instance

    Returns:
        Customer instance or None if not found

    Example:
        # Check before checkout
        customer = get_customer_by_user(request.user)
        if customer:
            # User has made purchases before - can use saved payment methods
            has_payment_methods = customer.payment_methods.exists()
        else:
            # First-time customer
            pass
    """
    try:
        return Customer.objects.get(subscriber=user)
    except Customer.DoesNotExist:
        logger.info(f"No Stripe customer found for user {user.id}")
        return None
