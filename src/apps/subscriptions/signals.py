"""
dj-stripe signal handlers for keeping CustomUser subscription FK synchronized.

Uses dj-stripe's @djstripe_receiver decorator to listen for Stripe webhook
events and automatically sync the CustomUser.subscription field.
"""

import logging
from djstripe.event_handlers import djstripe_receiver
from djstripe.models import Event

logger = logging.getLogger(__name__)


@djstripe_receiver("customer.subscription.created")
@djstripe_receiver("customer.subscription.updated")
def sync_user_subscription(sender, event: Event, **kwargs):
    """
    Sync CustomUser.subscription FK when subscription is created/updated.

    This keeps the FK field up-to-date for performance, allowing use of
    user.subscription for cached access instead of always querying
    user.active_subscription.

    Args:
        sender: The signal sender (not used)
        event: The dj-stripe Event object
        **kwargs: Additional signal kwargs
    """
    try:
        # Extract subscription data from event
        subscription_data = event.data.get("object")
        if not subscription_data:
            logger.warning(f"Event {event.id} has no subscription data")
            return

        # Get the subscription ID from event data
        subscription_id = subscription_data.get("id")
        if not subscription_id:
            logger.warning(f"Event {event.id} has no subscription ID")
            return

        # Import here to avoid circular imports
        from djstripe.models import Subscription
        from apps.accounts.models import CustomUser

        # Get the subscription object (should already be synced by dj-stripe)
        try:
            subscription = Subscription.objects.get(id=subscription_id)
        except Subscription.DoesNotExist:
            logger.warning(f"Subscription {subscription_id} not found in database")
            return

        # Find user with this Stripe Customer
        if not subscription.customer:
            logger.warning(f"Subscription {subscription_id} has no customer")
            return

        try:
            user = CustomUser.objects.get(customer=subscription.customer)
        except CustomUser.DoesNotExist:
            logger.info(f"No user linked to customer {subscription.customer.id}")
            return
        except CustomUser.MultipleObjectsReturned:
            logger.error(
                f"Multiple users found for customer {subscription.customer.id}"
            )
            return

        # Update FK based on subscription status
        # Note: subscription.status is a property (not DB field) that reads from stripe_data
        status = subscription.status

        if status in ["active", "trialing"]:
            # Set as active subscription
            user.subscription = subscription
            user.save(update_fields=["subscription"])
            logger.info(
                f"Synced active subscription {subscription_id} to user {user.id} (status: {status})"
            )

        elif status in ["canceled", "incomplete_expired", "unpaid"]:
            # Clear FK if this is the user's current subscription
            if user.subscription_id == subscription.id:
                user.subscription = None
                user.save(update_fields=["subscription"])
                logger.info(
                    f"Cleared subscription {subscription_id} from user {user.id} (status: {status})"
                )

    except Exception as e:
        # Log error but don't break webhook processing
        logger.error(
            f"Error syncing user subscription for event {event.id}: {e}", exc_info=True
        )


@djstripe_receiver("customer.subscription.deleted")
def clear_user_subscription(sender, event: Event, **kwargs):
    """
    Clear CustomUser.subscription FK when subscription is deleted.

    Args:
        sender: The signal sender (not used)
        event: The dj-stripe Event object
        **kwargs: Additional signal kwargs
    """
    try:
        # Extract subscription data from event
        subscription_data = event.data.get("object")
        if not subscription_data:
            return

        subscription_id = subscription_data.get("id")
        if not subscription_id:
            return

        # Import here to avoid circular imports
        from apps.accounts.models import CustomUser

        # Find user with this subscription and clear it
        try:
            user = CustomUser.objects.get(subscription__id=subscription_id)
            user.subscription = None
            user.save(update_fields=["subscription"])
            logger.info(
                f"Cleared deleted subscription {subscription_id} from user {user.id}"
            )
        except CustomUser.DoesNotExist:
            logger.info(f"No user found with subscription {subscription_id}")
        except CustomUser.MultipleObjectsReturned:
            logger.error(f"Multiple users found with subscription {subscription_id}")

    except Exception as e:
        logger.error(
            f"Error clearing user subscription for event {event.id}: {e}", exc_info=True
        )


@djstripe_receiver("customer.created")
@djstripe_receiver("customer.updated")
def link_customer_to_user(sender, event: Event, **kwargs):
    """
    Link dj-stripe Customer to CustomUser.

    This serves as a backup to ensure the customer FK is set even if:
    - User closes browser before reaching subscription_confirm view
    - Direct API subscription creation bypasses view layer
    - Network issues prevent success page from loading

    Args:
        sender: The signal sender (not used)
        event: The dj-stripe Event object
        **kwargs: Additional signal kwargs
    """
    try:
        # Extract customer data from event
        customer_data = event.data.get("object")
        if not customer_data:
            return

        customer_id = customer_data.get("id")
        if not customer_id:
            return

        # Import here to avoid circular imports
        from djstripe.models import Customer
        from apps.accounts.models import CustomUser

        # Get the customer object
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            logger.warning(f"Customer {customer_id} not found in database")
            return

        # Check if customer has subscriber (dj-stripe's built-in relation)
        if not customer.subscriber:
            logger.info(f"Customer {customer_id} has no subscriber linked yet")
            return

        # Find user by subscriber (assumes subscriber is CustomUser)
        try:
            user = CustomUser.objects.get(id=customer.subscriber.id)
        except CustomUser.DoesNotExist:
            logger.warning(f"User {customer.subscriber.id} not found")
            return

        # Link customer to user if not already linked
        if user.customer_id != customer.id:
            user.customer = customer
            user.save(update_fields=["customer"])
            logger.info(f"Linked customer {customer_id} to user {user.id}")
        else:
            logger.debug(f"Customer {customer_id} already linked to user {user.id}")

    except Exception as e:
        logger.error(
            f"Error linking customer to user for event {event.id}: {e}", exc_info=True
        )
