from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from django.contrib.auth import get_user_model

from apps.subscriptions import features
from apps.subscriptions.metadata import PREMIUM, STARTER

User = get_user_model()


@pytest.mark.django_db
class TestCustomUserStr:
    """Tests for CustomUser __str__."""

    def test_str_returns_username(self, user):
        assert str(user) == "testuser"


@pytest.mark.django_db
class TestActiveSubscription:
    """Tests for active_subscription property."""

    def test_returns_none_when_no_customer(self, user):
        """No customer means no subscription."""
        assert user.active_subscription is None

    def test_returns_none_when_no_subscriptions(self, user):
        """Customer with no subscriptions returns None."""
        mock_customer = MagicMock()
        mock_customer.pk = 999
        mock_customer.subscriptions.all.return_value.order_by.return_value = []

        # Set the FK id and cache the mock customer
        user.customer_id = mock_customer.pk
        user._state.fields_cache["customer"] = mock_customer

        result = user.active_subscription
        assert result is None

    def test_returns_active_subscription(self, user):
        """Active subscription is returned."""
        mock_sub = MagicMock()
        mock_sub.status = "active"

        mock_customer = MagicMock()
        mock_customer.pk = 999
        mock_customer.subscriptions.all.return_value.order_by.return_value = [mock_sub]

        # Set the FK id and cache the mock customer
        user.customer_id = mock_customer.pk
        user._state.fields_cache["customer"] = mock_customer

        result = user.active_subscription
        assert result == mock_sub

    def test_returns_trialing_subscription(self, user):
        """Trialing subscription is returned."""
        mock_sub = MagicMock()
        mock_sub.status = "trialing"

        mock_customer = MagicMock()
        mock_customer.pk = 999
        mock_customer.subscriptions.all.return_value.order_by.return_value = [mock_sub]

        # Set the FK id and cache the mock customer
        user.customer_id = mock_customer.pk
        user._state.fields_cache["customer"] = mock_customer

        result = user.active_subscription
        assert result == mock_sub

    def test_skips_canceled_subscription(self, user):
        """Canceled subscription is not returned."""
        mock_sub = MagicMock()
        mock_sub.status = "canceled"

        mock_customer = MagicMock()
        mock_customer.pk = 999
        mock_customer.subscriptions.all.return_value.order_by.return_value = [mock_sub]

        # Set the FK id and cache the mock customer
        user.customer_id = mock_customer.pk
        user._state.fields_cache["customer"] = mock_customer

        result = user.active_subscription
        assert result is None


@pytest.mark.django_db
class TestSubscriptionStatus:
    """Tests for subscription_status property."""

    def test_returns_none_when_no_active_subscription(self, user):
        """No active subscription returns None status."""
        with patch.object(type(user), "active_subscription", new_callable=PropertyMock, return_value=None):
            result = user.subscription_status
        assert result is None

    def test_returns_status_string(self, user):
        """Active subscription returns its status string."""
        mock_sub = MagicMock()
        mock_sub.status = "active"
        with patch.object(type(user), "active_subscription", new_callable=PropertyMock, return_value=mock_sub):
            result = user.subscription_status
        assert result == "active"


@pytest.mark.django_db
class TestHasFeature:
    """Tests for has_feature method."""

    def test_returns_false_no_subscription(self, user):
        """No subscription means no features."""
        with patch.object(type(user), "active_subscription", new_callable=PropertyMock, return_value=None):
            assert user.has_feature(features.LUDICROUS_MODE) is False

    def test_returns_true_for_included_feature(self, user):
        """Feature included in subscription metadata returns True."""
        mock_sub = MagicMock()
        mock_product = MagicMock()
        mock_product.subscription_metadata = PREMIUM
        mock_sub.product = mock_product

        with patch.object(type(user), "active_subscription", new_callable=PropertyMock, return_value=mock_sub):
            assert user.has_feature(features.LUDICROUS_MODE) is True

    def test_returns_false_for_excluded_feature(self, user):
        """Feature not in subscription metadata returns False."""
        mock_sub = MagicMock()
        mock_product = MagicMock()
        mock_product.subscription_metadata = STARTER  # Only has UNLIMITED_WIDGETS
        mock_sub.product = mock_product

        with patch.object(type(user), "active_subscription", new_callable=PropertyMock, return_value=mock_sub):
            assert user.has_feature(features.LUDICROUS_MODE) is False

    def test_returns_false_when_no_product(self, user):
        """Subscription without product returns False."""
        mock_sub = MagicMock()
        mock_sub.product = None

        with patch.object(type(user), "active_subscription", new_callable=PropertyMock, return_value=mock_sub):
            assert user.has_feature(features.UNLIMITED_WIDGETS) is False


@pytest.mark.django_db
class TestGetSubscriptionFeatures:
    """Tests for get_subscription_features method."""

    def test_returns_empty_list_no_subscription(self, user):
        """No subscription returns empty list."""
        with patch.object(type(user), "active_subscription", new_callable=PropertyMock, return_value=None):
            assert user.get_subscription_features() == []

    def test_returns_features_list(self, user):
        """Returns feature list from subscription metadata."""
        mock_sub = MagicMock()
        mock_product = MagicMock()
        mock_product.subscription_metadata = PREMIUM
        mock_sub.product = mock_product

        with patch.object(type(user), "active_subscription", new_callable=PropertyMock, return_value=mock_sub):
            result = user.get_subscription_features()
        assert features.UNLIMITED_WIDGETS in result
        assert features.LUDICROUS_MODE in result
        assert features.PRIORITY_SUPPORT in result

    def test_returns_empty_when_no_metadata(self, user):
        """Subscription without metadata returns empty list."""
        mock_sub = MagicMock()
        mock_product = MagicMock()
        mock_product.subscription_metadata = None
        mock_sub.product = mock_product

        with patch.object(type(user), "active_subscription", new_callable=PropertyMock, return_value=mock_sub):
            assert user.get_subscription_features() == []
