import logging
from djstripe.event_handlers import djstripe_receiver
from djstripe.models import Event

logger = logging.getLogger(__name__)


@djstripe_receiver("payment_intent.succeeded")
def handle_successful_payment(sender, event: Event, **kwargs):
    """
    Handle successful payment webhook.
    Order status is automatically updated via property (reads from PaymentIntent).
    No manual status update needed since Order.status is a property.
    """
    payment_intent_data = event.data.get("object")
    payment_intent_id = payment_intent_data.get("id")

    logger.info(f"Shop payment succeeded: {payment_intent_id}")
    # Order.status property automatically reflects updated PaymentIntent status


@djstripe_receiver("payment_intent.payment_failed")
def handle_failed_payment(sender, event: Event, **kwargs):
    """Handle failed payment webhook"""
    payment_intent_data = event.data.get("object")
    payment_intent_id = payment_intent_data.get("id")

    logger.warning(f"Shop payment failed: {payment_intent_id}")
    # Could send notification email to user here


@djstripe_receiver("charge.refunded")
def handle_refund(sender, event: Event, **kwargs):
    """Handle refund webhook"""
    charge_data = event.data.get("object")
    charge_id = charge_data.get("id")

    logger.info(f"Shop charge refunded: {charge_id}")
    # Could update order status or send refund confirmation email here
