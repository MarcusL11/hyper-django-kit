from dataclasses import dataclass
from typing import List
from apps.subscriptions import features


@dataclass
class SubscriptionProductMetadata(object):
    """
    Metadata for a Stripe product.
    """

    stripe_id: str
    order: int
    features: List[str]
    description: str = ""
    is_popular: bool = False


PREMIUM = SubscriptionProductMetadata(
    stripe_id="prod_THltnX3hll17Wp",
    order=3,
    description="For small businesses and teams",
    is_popular=False,
    features=[
        features.UNLIMITED_WIDGETS,
        features.LUDICROUS_MODE,
        features.PRIORITY_SUPPORT,
    ],
)

STANDARD = SubscriptionProductMetadata(
    stripe_id="prod_THlvv4H2DsGKlo",
    order=2,
    description="For growing businesses",
    is_popular=True,
    features=[
        features.UNLIMITED_WIDGETS,
        features.PRIORITY_SUPPORT,
    ],
)

STARTER = SubscriptionProductMetadata(
    stripe_id="prod_THlqKyB01JLmKC",
    order=1,
    description="For individuals and small teams",
    is_popular=False,
    features=[
        features.UNLIMITED_WIDGETS,
    ],
)

# Consolidate all metadata objects into a single mapping for easy lookup
METADATA_MAP = {
    PREMIUM.stripe_id: PREMIUM,
    STARTER.stripe_id: STARTER,
    STANDARD.stripe_id: STANDARD,
    # Add other products here
}
