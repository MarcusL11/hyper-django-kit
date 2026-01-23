from unittest.mock import MagicMock, patch

import pytest

from apps.subscriptions.metadata import (
    SubscriptionProductMetadata,
    PREMIUM,
    STANDARD,
    STARTER,
    METADATA_MAP,
)
from apps.subscriptions import features


class TestSubscriptionProductMetadata:
    """Tests for SubscriptionProductMetadata dataclass."""

    def test_premium_has_all_features(self):
        assert features.UNLIMITED_WIDGETS in PREMIUM.features
        assert features.LUDICROUS_MODE in PREMIUM.features
        assert features.PRIORITY_SUPPORT in PREMIUM.features

    def test_standard_features(self):
        assert features.UNLIMITED_WIDGETS in STANDARD.features
        assert features.PRIORITY_SUPPORT in STANDARD.features
        assert features.LUDICROUS_MODE not in STANDARD.features

    def test_starter_features(self):
        assert features.UNLIMITED_WIDGETS in STARTER.features
        assert features.LUDICROUS_MODE not in STARTER.features
        assert features.PRIORITY_SUPPORT not in STARTER.features

    def test_ordering(self):
        assert STARTER.order < STANDARD.order < PREMIUM.order

    def test_standard_is_popular(self):
        assert STANDARD.is_popular is True
        assert STARTER.is_popular is False
        assert PREMIUM.is_popular is False

    def test_metadata_map_contains_all_products(self):
        assert PREMIUM.stripe_id in METADATA_MAP
        assert STANDARD.stripe_id in METADATA_MAP
        assert STARTER.stripe_id in METADATA_MAP

    def test_metadata_map_lookup(self):
        assert METADATA_MAP[PREMIUM.stripe_id] is PREMIUM
        assert METADATA_MAP[STANDARD.stripe_id] is STANDARD
        assert METADATA_MAP[STARTER.stripe_id] is STARTER

    def test_unknown_product_not_in_map(self):
        assert METADATA_MAP.get("prod_unknown") is None


class TestMonkeyPatchedProperties:
    """Tests for properties added to djstripe models in apps.py."""

    def test_subscription_product_property(self):
        """Subscription.product returns first item's price's product."""
        mock_subscription = MagicMock()
        mock_item = MagicMock()
        mock_price = MagicMock()
        mock_product = MagicMock()

        mock_price.product = mock_product
        mock_item.price = mock_price
        mock_subscription.items.first.return_value = mock_item

        # Import the property from apps.py (it's already attached to Subscription)
        from djstripe.models import Subscription
        result = Subscription.product.fget(mock_subscription)
        assert result == mock_product

    def test_subscription_product_no_items(self):
        """Subscription.product returns None when no items."""
        mock_subscription = MagicMock()
        mock_subscription.items.first.return_value = None

        from djstripe.models import Subscription
        result = Subscription.product.fget(mock_subscription)
        assert result is None

    def test_subscription_product_no_price(self):
        """Subscription.product returns None when item has no price."""
        mock_subscription = MagicMock()
        mock_item = MagicMock()
        mock_item.price = None
        mock_subscription.items.first.return_value = mock_item

        from djstripe.models import Subscription
        result = Subscription.product.fget(mock_subscription)
        assert result is None

    def test_product_subscription_metadata_found(self):
        """Product.subscription_metadata returns metadata for known product."""
        mock_product = MagicMock()
        mock_product.id = PREMIUM.stripe_id

        from djstripe.models import Product
        result = Product.subscription_metadata.fget(mock_product)
        assert result is PREMIUM

    def test_product_subscription_metadata_not_found(self):
        """Product.subscription_metadata returns None for unknown product."""
        mock_product = MagicMock()
        mock_product.id = "prod_unknown"

        from djstripe.models import Product
        result = Product.subscription_metadata.fget(mock_product)
        assert result is None
