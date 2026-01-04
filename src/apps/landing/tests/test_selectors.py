"""
Tests for landing app selectors.
"""
import pytest
from django.contrib.auth.models import AnonymousUser
from unittest.mock import Mock, patch

from apps.landing.selectors import get_pricing_plans, get_user_subscription_context


@pytest.mark.django_db
class TestGetPricingPlans:
    """
    Test suite for get_pricing_plans selector.

    Source: pytest-django documentation - Use @pytest.mark.django_db for database access
    """

    def test_returns_dict_with_required_keys(self):
        """Should return dict with plans_monthly and plans_yearly keys."""
        with patch("apps.landing.selectors.Product") as MockProduct:
            MockProduct.objects.prefetch_related.return_value.filter.return_value = []

            result = get_pricing_plans()

            assert "plans_monthly" in result
            assert "plans_yearly" in result
            assert isinstance(result["plans_monthly"], list)
            assert isinstance(result["plans_yearly"], list)

    def test_returns_empty_lists_when_no_products(self):
        """Should return empty lists when no active products exist."""
        with patch("apps.landing.selectors.Product") as MockProduct:
            MockProduct.objects.prefetch_related.return_value.filter.return_value = []

            result = get_pricing_plans()

            assert result["plans_monthly"] == []
            assert result["plans_yearly"] == []

    def test_filters_products_without_subscription_metadata(self):
        """Should skip products without subscription_metadata."""
        with patch("apps.landing.selectors.Product") as MockProduct:
            mock_product = Mock()
            mock_product.subscription_metadata = None
            MockProduct.objects.prefetch_related.return_value.filter.return_value = [mock_product]

            result = get_pricing_plans()

            assert result["plans_monthly"] == []
            assert result["plans_yearly"] == []

    def test_filters_inactive_prices(self):
        """Should skip inactive prices."""
        with patch("apps.landing.selectors.Product") as MockProduct:
            mock_metadata = Mock()
            mock_metadata.order = 1

            mock_price = Mock()
            mock_price.active = False
            mock_price.recurring = {"interval": "month"}

            mock_product = Mock()
            mock_product.subscription_metadata = mock_metadata
            mock_product.prices.all.return_value = [mock_price]

            MockProduct.objects.prefetch_related.return_value.filter.return_value = [mock_product]

            result = get_pricing_plans()

            assert result["plans_monthly"] == []

    def test_filters_prices_without_recurring_interval(self):
        """Should skip prices without recurring interval."""
        with patch("apps.landing.selectors.Product") as MockProduct:
            mock_metadata = Mock()
            mock_metadata.order = 1

            mock_price = Mock()
            mock_price.active = True
            mock_price.recurring = None

            mock_product = Mock()
            mock_product.subscription_metadata = mock_metadata
            mock_product.prices.all.return_value = [mock_price]

            MockProduct.objects.prefetch_related.return_value.filter.return_value = [mock_product]

            result = get_pricing_plans()

            assert result["plans_monthly"] == []
            assert result["plans_yearly"] == []

    def test_filters_prices_with_invalid_interval(self):
        """Should skip prices with interval other than month or year."""
        with patch("apps.landing.selectors.Product") as MockProduct:
            mock_metadata = Mock()
            mock_metadata.order = 1

            mock_price = Mock()
            mock_price.active = True
            mock_price.recurring = {"interval": "week"}

            mock_product = Mock()
            mock_product.subscription_metadata = mock_metadata
            mock_product.prices.all.return_value = [mock_price]

            MockProduct.objects.prefetch_related.return_value.filter.return_value = [mock_product]

            result = get_pricing_plans()

            assert result["plans_monthly"] == []
            assert result["plans_yearly"] == []

    def test_separates_monthly_and_yearly_plans(self):
        """Should correctly separate monthly and yearly intervals."""
        with patch("apps.landing.selectors.Product") as MockProduct:
            mock_metadata = Mock()
            mock_metadata.order = 1

            mock_monthly_price = Mock()
            mock_monthly_price.active = True
            mock_monthly_price.recurring = {"interval": "month"}

            mock_yearly_price = Mock()
            mock_yearly_price.active = True
            mock_yearly_price.recurring = {"interval": "year"}

            mock_product = Mock()
            mock_product.subscription_metadata = mock_metadata
            mock_product.prices.all.return_value = [mock_monthly_price, mock_yearly_price]

            MockProduct.objects.prefetch_related.return_value.filter.return_value = [mock_product]

            result = get_pricing_plans()

            assert len(result["plans_monthly"]) == 1
            assert len(result["plans_yearly"]) == 1
            assert result["plans_monthly"][0]["price"] == mock_monthly_price
            assert result["plans_yearly"][0]["price"] == mock_yearly_price

    def test_sorts_plans_by_order(self):
        """Should sort plans by metadata.order field."""
        with patch("apps.landing.selectors.Product") as MockProduct:
            mock_metadata_1 = Mock()
            mock_metadata_1.order = 2

            mock_metadata_2 = Mock()
            mock_metadata_2.order = 1

            mock_price_1 = Mock()
            mock_price_1.active = True
            mock_price_1.recurring = {"interval": "month"}

            mock_price_2 = Mock()
            mock_price_2.active = True
            mock_price_2.recurring = {"interval": "month"}

            mock_product_1 = Mock()
            mock_product_1.subscription_metadata = mock_metadata_1
            mock_product_1.prices.all.return_value = [mock_price_1]

            mock_product_2 = Mock()
            mock_product_2.subscription_metadata = mock_metadata_2
            mock_product_2.prices.all.return_value = [mock_price_2]

            MockProduct.objects.prefetch_related.return_value.filter.return_value = [
                mock_product_1, mock_product_2
            ]

            result = get_pricing_plans()

            assert result["plans_monthly"][0]["order"] == 1
            assert result["plans_monthly"][1]["order"] == 2

    def test_includes_correct_plan_data_structure(self):
        """Should include order, price, and metadata in plan dictionaries."""
        with patch("apps.landing.selectors.Product") as MockProduct:
            mock_metadata = Mock()
            mock_metadata.order = 1

            mock_price = Mock()
            mock_price.active = True
            mock_price.recurring = {"interval": "month"}

            mock_product = Mock()
            mock_product.subscription_metadata = mock_metadata
            mock_product.prices.all.return_value = [mock_price]

            MockProduct.objects.prefetch_related.return_value.filter.return_value = [mock_product]

            result = get_pricing_plans()

            assert len(result["plans_monthly"]) == 1
            plan = result["plans_monthly"][0]
            assert "order" in plan
            assert "price" in plan
            assert "metadata" in plan
            assert plan["order"] == 1
            assert plan["price"] == mock_price
            assert plan["metadata"] == mock_metadata

    def test_handles_multiple_products_with_multiple_prices(self):
        """Should correctly handle multiple products each with multiple prices."""
        with patch("apps.landing.selectors.Product") as MockProduct:
            # Product 1: Starter plan
            mock_metadata_1 = Mock()
            mock_metadata_1.order = 1

            mock_price_1_monthly = Mock()
            mock_price_1_monthly.active = True
            mock_price_1_monthly.recurring = {"interval": "month"}

            mock_price_1_yearly = Mock()
            mock_price_1_yearly.active = True
            mock_price_1_yearly.recurring = {"interval": "year"}

            mock_product_1 = Mock()
            mock_product_1.subscription_metadata = mock_metadata_1
            mock_product_1.prices.all.return_value = [mock_price_1_monthly, mock_price_1_yearly]

            # Product 2: Premium plan
            mock_metadata_2 = Mock()
            mock_metadata_2.order = 2

            mock_price_2_monthly = Mock()
            mock_price_2_monthly.active = True
            mock_price_2_monthly.recurring = {"interval": "month"}

            mock_price_2_yearly = Mock()
            mock_price_2_yearly.active = True
            mock_price_2_yearly.recurring = {"interval": "year"}

            mock_product_2 = Mock()
            mock_product_2.subscription_metadata = mock_metadata_2
            mock_product_2.prices.all.return_value = [mock_price_2_monthly, mock_price_2_yearly]

            MockProduct.objects.prefetch_related.return_value.filter.return_value = [
                mock_product_1, mock_product_2
            ]

            result = get_pricing_plans()

            assert len(result["plans_monthly"]) == 2
            assert len(result["plans_yearly"]) == 2
            assert result["plans_monthly"][0]["order"] == 1
            assert result["plans_monthly"][1]["order"] == 2
            assert result["plans_yearly"][0]["order"] == 1
            assert result["plans_yearly"][1]["order"] == 2


@pytest.mark.django_db
class TestGetUserSubscriptionContext:
    """
    Test suite for get_user_subscription_context selector.

    Source: pytest-django documentation - Use @pytest.mark.django_db for database access
    """

    def test_returns_none_for_anonymous_user(self):
        """Should return None values for unauthenticated users."""
        anonymous_user = AnonymousUser()

        result = get_user_subscription_context(anonymous_user)

        assert result["user_subscription"] is None
        assert result["user_product_id"] is None

    def test_returns_dict_with_required_keys(self):
        """Should always return dict with user_subscription and user_product_id keys."""
        anonymous_user = AnonymousUser()

        result = get_user_subscription_context(anonymous_user)

        assert "user_subscription" in result
        assert "user_product_id" in result

    def test_returns_none_when_user_has_no_active_subscription(self):
        """Should return None when authenticated user has no active subscription."""
        with patch("djstripe.models.Subscription") as MockSubscription:
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.customer = Mock()

            # Mock the query chain to return None
            MockSubscription.objects.filter.return_value.select_related.return_value.order_by.return_value.first.return_value = None

            result = get_user_subscription_context(mock_user)

            assert result["user_subscription"] is None
            assert result["user_product_id"] is None

    def test_returns_subscription_for_authenticated_user_with_active_subscription(self):
        """Should return active subscription for authenticated user."""
        with patch("djstripe.models.Subscription") as MockSubscription:
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.customer = Mock()

            mock_product = Mock()
            mock_product.id = "prod_123"

            mock_subscription = Mock()
            mock_subscription.product = mock_product

            # Mock the query chain to return the subscription
            MockSubscription.objects.filter.return_value.select_related.return_value.order_by.return_value.first.return_value = mock_subscription

            result = get_user_subscription_context(mock_user)

            assert result["user_subscription"] == mock_subscription
            assert result["user_product_id"] == "prod_123"

    def test_returns_none_product_id_when_subscription_has_no_product(self):
        """Should return None product_id when subscription exists but has no product."""
        with patch("djstripe.models.Subscription") as MockSubscription:
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.customer = Mock()

            mock_subscription = Mock()
            mock_subscription.product = None

            # Mock the query chain to return the subscription
            MockSubscription.objects.filter.return_value.select_related.return_value.order_by.return_value.first.return_value = mock_subscription

            result = get_user_subscription_context(mock_user)

            assert result["user_subscription"] == mock_subscription
            assert result["user_product_id"] is None

    def test_returns_none_when_user_has_no_customer(self):
        """Should return None when authenticated user has no customer."""
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.customer = None

        result = get_user_subscription_context(mock_user)

        assert result["user_subscription"] is None
        assert result["user_product_id"] is None

    def test_returns_none_when_user_has_no_customer_attribute(self):
        """Should return None when user object has no customer attribute."""
        mock_user = Mock()
        mock_user.is_authenticated = True
        # Remove customer attribute
        del mock_user.customer

        result = get_user_subscription_context(mock_user)

        assert result["user_subscription"] is None
        assert result["user_product_id"] is None

    def test_handles_unauthenticated_user_flag(self):
        """Should check is_authenticated flag correctly."""
        mock_user = Mock()
        mock_user.is_authenticated = False
        mock_user.customer = Mock()  # Should be ignored

        result = get_user_subscription_context(mock_user)

        assert result["user_subscription"] is None
        assert result["user_product_id"] is None

    def test_queries_subscription_with_correct_filters(self):
        """Should query Subscription with correct customer and status filters."""
        with patch("djstripe.models.Subscription") as MockSubscription:
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_customer = Mock()
            mock_user.customer = mock_customer

            mock_subscription = Mock()
            mock_subscription.product = None

            # Setup the mock chain
            mock_filter = MockSubscription.objects.filter.return_value
            mock_select = mock_filter.select_related.return_value
            mock_order = mock_select.order_by.return_value
            mock_order.first.return_value = mock_subscription

            result = get_user_subscription_context(mock_user)

            # Verify the query chain was called correctly
            MockSubscription.objects.filter.assert_called_once_with(
                customer=mock_customer,
                status__in=["active", "trialing"]
            )
            mock_filter.select_related.assert_called_once_with("product")
            mock_select.order_by.assert_called_once_with("-created")
            mock_order.first.assert_called_once()
