from datetime import datetime, timezone

import pytest
from unittest.mock import patch, PropertyMock, MagicMock
from django.urls import reverse


@pytest.mark.django_db
class TestSubscriptionManagement:
    """Tests for subscription_management view."""

    def test_requires_login(self, client):
        """Anonymous user should be redirected to login."""
        url = reverse("user_dashboard:subscription_management")
        response = client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_returns_200(self, client, user):
        """Authenticated user should get 200 response."""
        client.force_login(user)
        url = reverse("user_dashboard:subscription_management")
        response = client.get(url)
        assert response.status_code == 200

    def test_context_with_subscription(self, client, user):
        """Context should contain subscription data when user has active subscription."""
        mock_subscription = MagicMock()
        mock_subscription.product.name = "Pro Plan"
        mock_subscription.cancel_at_period_end = False
        mock_subscription.status = "active"
        mock_subscription.current_period_end = datetime(2025, 12, 31, tzinfo=timezone.utc)
        mock_subscription.plan.interval = "month"
        mock_subscription.plan.amount = 999
        # Prevent Django template from using dict-style lookup on the mock
        mock_subscription.__getitem__ = MagicMock(side_effect=TypeError)
        mock_subscription.plan.__getitem__ = MagicMock(side_effect=TypeError)

        with patch.object(
            type(user), "active_subscription", new_callable=PropertyMock, return_value=mock_subscription
        ):
            client.force_login(user)
            url = reverse("user_dashboard:subscription_management")
            response = client.get(url)

        assert response.status_code == 200
        assert response.context["has_subscription"] is True
        assert response.context["plan_name"] == "Pro Plan"
        assert response.context["subscription"] == mock_subscription
        assert response.context["user"] == user

    def test_context_without_subscription(self, client, user):
        """Context should reflect no subscription when user has no active subscription."""
        with patch.object(type(user), "active_subscription", new_callable=PropertyMock, return_value=None):
            client.force_login(user)
            url = reverse("user_dashboard:subscription_management")
            response = client.get(url)

        assert response.status_code == 200
        assert response.context["has_subscription"] is False
        assert response.context["plan_name"] == ""
        assert response.context["subscription"] == ""
        assert response.context["user"] == user


@pytest.mark.django_db
class TestSubscriptionInvoices:
    """Tests for subscription_invoices view."""

    def test_requires_login(self, client):
        """Anonymous user should be redirected to login."""
        url = reverse("user_dashboard:subscription_invoices")
        response = client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_returns_200(self, client, user):
        """Authenticated user should get 200 response."""
        client.force_login(user)
        url = reverse("user_dashboard:subscription_invoices")
        response = client.get(url)
        assert response.status_code == 200

    def test_context_with_customer_invoices(self, client, user):
        """Context should contain invoices when user has a customer with invoices."""
        mock_invoice = MagicMock()
        mock_invoice.id = "inv_123"
        mock_invoice.created = datetime(2025, 6, 15, tzinfo=timezone.utc)
        mock_invoice.status = "paid"
        mock_invoice.hosted_invoice_url = None
        mock_invoice.invoice_pdf = None
        # Prevent Django template from using dict-style lookup on the mock
        mock_invoice.__getitem__ = MagicMock(side_effect=TypeError)

        mock_customer = MagicMock()
        # Mock the chained calls: invoices.all().order_by("-created")[:20]
        mock_customer.invoices.all.return_value.order_by.return_value.__getitem__.return_value = [mock_invoice]

        with patch.object(type(user), "customer", new_callable=PropertyMock, return_value=mock_customer):
            client.force_login(user)
            url = reverse("user_dashboard:subscription_invoices")
            response = client.get(url)

        assert response.status_code == 200
        assert response.context["user"] == user
        assert len(response.context["invoices"]) == 1
        assert response.context["invoices"][0] == mock_invoice
        # Verify the correct method chain was called
        mock_customer.invoices.all.assert_called_once()
        mock_customer.invoices.all.return_value.order_by.assert_called_once_with("-created")

    def test_context_without_customer(self, client, user):
        """Context should contain empty invoices list when user has no customer."""
        with patch.object(type(user), "customer", new_callable=PropertyMock, return_value=None):
            client.force_login(user)
            url = reverse("user_dashboard:subscription_invoices")
            response = client.get(url)

        assert response.status_code == 200
        assert response.context["user"] == user
        assert response.context["invoices"] == []


@pytest.mark.django_db
class TestSubscriptionPlans:
    """Tests for subscription_plans view."""

    def test_requires_login(self, client):
        """Anonymous user should be redirected to login."""
        url = reverse("user_dashboard:subscription_plans")
        response = client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_returns_200(self, client, user):
        """Authenticated user should get 200 response."""
        client.force_login(user)
        with patch("apps.user_dashboard.views.Product.objects.prefetch_related") as mock_prefetch:
            mock_prefetch.return_value.filter.return_value = []
            url = reverse("user_dashboard:subscription_plans")
            response = client.get(url)
        assert response.status_code == 200

    def test_plans_with_active_products(self, client, user):
        """Context should contain sorted plans for active products with metadata."""
        # Create mock monthly price
        mock_price_monthly = MagicMock()
        mock_price_monthly.active = True
        mock_price_monthly.recurring = {"interval": "month"}

        # Create mock yearly price
        mock_price_yearly = MagicMock()
        mock_price_yearly.active = True
        mock_price_yearly.recurring = {"interval": "year"}

        # Create mock metadata
        mock_metadata_1 = MagicMock()
        mock_metadata_1.order = 1

        mock_metadata_2 = MagicMock()
        mock_metadata_2.order = 2

        # Create mock products
        mock_product_1 = MagicMock()
        mock_product_1.id = "prod_1"
        mock_product_1.subscription_metadata = mock_metadata_1
        mock_product_1.prices.all.return_value = [mock_price_monthly]

        mock_product_2 = MagicMock()
        mock_product_2.id = "prod_2"
        mock_product_2.subscription_metadata = mock_metadata_2
        mock_product_2.prices.all.return_value = [mock_price_yearly]

        with patch("apps.user_dashboard.views.Product.objects.prefetch_related") as mock_prefetch:
            mock_prefetch.return_value.filter.return_value = [mock_product_1, mock_product_2]
            with patch.object(type(user), "active_subscription", new_callable=PropertyMock, return_value=None):
                client.force_login(user)
                url = reverse("user_dashboard:subscription_plans")
                response = client.get(url)

        assert response.status_code == 200
        assert len(response.context["plans_monthly"]) == 1
        assert len(response.context["plans_yearly"]) == 1
        assert response.context["plans_monthly"][0]["price"] == mock_price_monthly
        assert response.context["plans_monthly"][0]["metadata"] == mock_metadata_1
        assert response.context["plans_monthly"][0]["order"] == 1
        assert response.context["plans_yearly"][0]["price"] == mock_price_yearly
        assert response.context["plans_yearly"][0]["metadata"] == mock_metadata_2
        assert response.context["plans_yearly"][0]["order"] == 2

    def test_plans_skips_products_without_metadata(self, client, user):
        """Products without subscription_metadata should be skipped."""
        mock_price = MagicMock()
        mock_price.active = True
        mock_price.recurring = {"interval": "month"}

        mock_product = MagicMock()
        mock_product.subscription_metadata = None
        mock_product.prices.all.return_value = [mock_price]

        with patch("apps.user_dashboard.views.Product.objects.prefetch_related") as mock_prefetch:
            mock_prefetch.return_value.filter.return_value = [mock_product]
            with patch.object(type(user), "active_subscription", new_callable=PropertyMock, return_value=None):
                client.force_login(user)
                url = reverse("user_dashboard:subscription_plans")
                response = client.get(url)

        assert response.status_code == 200
        assert len(response.context["plans_monthly"]) == 0
        assert len(response.context["plans_yearly"]) == 0

    def test_plans_skips_inactive_prices(self, client, user):
        """Inactive prices should be skipped."""
        mock_price_inactive = MagicMock()
        mock_price_inactive.active = False
        mock_price_inactive.recurring = {"interval": "month"}

        mock_metadata = MagicMock()
        mock_metadata.order = 1

        mock_product = MagicMock()
        mock_product.subscription_metadata = mock_metadata
        mock_product.prices.all.return_value = [mock_price_inactive]

        with patch("apps.user_dashboard.views.Product.objects.prefetch_related") as mock_prefetch:
            mock_prefetch.return_value.filter.return_value = [mock_product]
            with patch.object(type(user), "active_subscription", new_callable=PropertyMock, return_value=None):
                client.force_login(user)
                url = reverse("user_dashboard:subscription_plans")
                response = client.get(url)

        assert response.status_code == 200
        assert len(response.context["plans_monthly"]) == 0
        assert len(response.context["plans_yearly"]) == 0

    def test_user_product_id_with_subscription(self, client, user):
        """Context should contain user_product_id when user has active subscription."""
        mock_product = MagicMock()
        mock_product.id = "prod_123"

        mock_subscription = MagicMock()
        mock_subscription.product = mock_product

        with patch("apps.user_dashboard.views.Product.objects.prefetch_related") as mock_prefetch:
            mock_prefetch.return_value.filter.return_value = []
            with patch.object(
                type(user), "active_subscription", new_callable=PropertyMock, return_value=mock_subscription
            ):
                client.force_login(user)
                url = reverse("user_dashboard:subscription_plans")
                response = client.get(url)

        assert response.status_code == 200
        assert response.context["user_product_id"] == "prod_123"
        assert response.context["user_subscription"] == mock_subscription

    def test_user_product_id_none_without_subscription(self, client, user):
        """Context should have user_product_id as None when user has no subscription."""
        with patch("apps.user_dashboard.views.Product.objects.prefetch_related") as mock_prefetch:
            mock_prefetch.return_value.filter.return_value = []
            with patch.object(type(user), "active_subscription", new_callable=PropertyMock, return_value=None):
                client.force_login(user)
                url = reverse("user_dashboard:subscription_plans")
                response = client.get(url)

        assert response.status_code == 200
        assert response.context["user_product_id"] is None
        assert response.context["user_subscription"] is None
