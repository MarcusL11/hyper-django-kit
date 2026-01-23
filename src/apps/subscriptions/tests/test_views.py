import uuid
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestCreateCheckoutSession:
    """Tests for create_checkout_session view."""

    def test_requires_login(self, client):
        url = reverse("subscriptions:create_checkout_session")
        response = client.post(url, {"price_id": "price_x"})
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_requires_post(self, client, user):
        client.force_login(user)
        url = reverse("subscriptions:create_checkout_session")
        response = client.get(url)
        assert response.status_code == 405

    def test_redirects_if_user_has_active_subscription(self, client, user):
        client.force_login(user)
        url = reverse("subscriptions:create_checkout_session")
        with patch.object(type(user), "active_subscription", new_callable=PropertyMock, return_value=MagicMock()):
            response = client.post(url, {"price_id": "price_test"})
        assert response.status_code == 302
        assert reverse("subscriptions:billing_portal") in response.url

    def test_missing_price_id_redirects(self, client, user):
        client.force_login(user)
        url = reverse("subscriptions:create_checkout_session")
        with patch.object(type(user), "active_subscription", new_callable=PropertyMock, return_value=None):
            response = client.post(url, {})
        assert response.status_code == 302
        assert reverse("landing:index") in response.url

    def test_creates_session_and_redirects(self, client, user):
        client.force_login(user)
        url = reverse("subscriptions:create_checkout_session")
        mock_session = MagicMock()
        mock_session.id = "cs_test_123"
        mock_session.url = "https://checkout.stripe.com/pay/cs_test_123"
        mock_customer = MagicMock()
        mock_customer.id = "cus_test123"

        with patch.object(type(user), "active_subscription", new_callable=PropertyMock, return_value=None), \
             patch("apps.subscriptions.views.get_or_create_customer", return_value=(mock_customer, False)), \
             patch("apps.subscriptions.views.stripe.checkout.Session.create", return_value=mock_session):
            response = client.post(url, {"price_id": "price_test123"})

        assert response.status_code == 302
        assert response.url == mock_session.url

    def test_stripe_error_redirects_to_landing(self, client, user):
        client.force_login(user)
        url = reverse("subscriptions:create_checkout_session")
        mock_customer = MagicMock()

        with patch.object(type(user), "active_subscription", new_callable=PropertyMock, return_value=None), \
             patch("apps.subscriptions.views.get_or_create_customer", return_value=(mock_customer, False)), \
             patch("apps.subscriptions.views.stripe.checkout.Session.create", side_effect=Exception("Stripe error")):
            response = client.post(url, {"price_id": "price_test123"})

        assert response.status_code == 302
        assert reverse("landing:index") in response.url


@pytest.mark.django_db
class TestSubscriptionConfirm:
    """Tests for subscription_confirm view."""

    def test_requires_login(self, client):
        url = reverse("subscriptions:subscription_confirm")
        response = client.get(url, {"session_id": "cs_test"})
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_missing_session_id_redirects(self, client, user):
        client.force_login(user)
        url = reverse("subscriptions:subscription_confirm")
        response = client.get(url)
        assert response.status_code == 302
        assert reverse("landing:index") in response.url

    def test_user_mismatch_redirects(self, client, user, other_user):
        client.force_login(user)
        url = reverse("subscriptions:subscription_confirm")
        mock_session = MagicMock()
        mock_session.client_reference_id = str(other_user.id)
        mock_session.subscription = "sub_test"

        with patch("apps.subscriptions.views.stripe.checkout.Session.retrieve", return_value=mock_session):
            response = client.get(url, {"session_id": "cs_test"})

        assert response.status_code == 302
        assert reverse("landing:index") in response.url

    def test_successful_confirmation(self, client, user):
        client.force_login(user)
        url = reverse("subscriptions:subscription_confirm")
        mock_session = MagicMock()
        mock_session.client_reference_id = str(user.id)
        mock_session.subscription = "sub_test123"

        mock_subscription = MagicMock()
        mock_djstripe_sub = MagicMock()
        mock_djstripe_sub.customer = MagicMock()

        # Create a mock user that will be returned by the queryset
        # This avoids FK constraint issues when assigning mock objects
        mock_subscription_holder = MagicMock()
        mock_subscription_holder.id = user.id
        mock_subscription_holder.save = MagicMock()
        # Make comparison work: mock_user == request.user should return True
        mock_subscription_holder.__eq__ = lambda self, other: True
        mock_subscription_holder.__ne__ = lambda self, other: False

        with patch("apps.subscriptions.views.stripe.checkout.Session.retrieve", return_value=mock_session), \
             patch("apps.subscriptions.views.stripe.Subscription.retrieve", return_value=mock_subscription), \
             patch("apps.subscriptions.views.Subscription.sync_from_stripe_data", return_value=mock_djstripe_sub), \
             patch("apps.subscriptions.views.get_user_model") as mock_get_user_model:
            mock_get_user_model.return_value.objects.get.return_value = mock_subscription_holder
            response = client.get(url, {"session_id": "cs_test"})

        assert response.status_code == 200

    def test_missing_client_reference_id_redirects(self, client, user):
        client.force_login(user)
        url = reverse("subscriptions:subscription_confirm")
        mock_session = MagicMock()
        mock_session.client_reference_id = None

        with patch("apps.subscriptions.views.stripe.checkout.Session.retrieve", return_value=mock_session):
            response = client.get(url, {"session_id": "cs_test"})

        assert response.status_code == 302
        assert reverse("landing:index") in response.url

    def test_stripe_error_redirects(self, client, user):
        client.force_login(user)
        url = reverse("subscriptions:subscription_confirm")

        with patch("apps.subscriptions.views.stripe.checkout.Session.retrieve", side_effect=Exception("Stripe error")):
            response = client.get(url, {"session_id": "cs_test"})

        assert response.status_code == 302
        assert reverse("landing:index") in response.url


@pytest.mark.django_db
class TestSubscriptionCanceled:
    """Tests for subscription_canceled view."""

    def test_requires_login(self, client):
        url = reverse("subscriptions:subscription_canceled")
        response = client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_returns_200(self, client, user):
        client.force_login(user)
        url = reverse("subscriptions:subscription_canceled")
        response = client.get(url)
        assert response.status_code == 200

    def test_context_data(self, client, user):
        client.force_login(user)
        url = reverse("subscriptions:subscription_canceled")
        response = client.get(url)
        assert response.context["result_type"] == "warning"
        assert response.context["heading"] == "Checkout Canceled"


@pytest.mark.django_db
class TestBillingPortal:
    """Tests for billing_portal view."""

    def test_requires_login(self, client):
        url = reverse("subscriptions:billing_portal")
        response = client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_no_customer_redirects(self, client, user):
        client.force_login(user)
        url = reverse("subscriptions:billing_portal")
        # user.customer is None by default (FK field)
        response = client.get(url)
        assert response.status_code == 302
        assert reverse("landing:index") in response.url

    def test_creates_portal_and_redirects(self, client, user):
        client.force_login(user)
        url = reverse("subscriptions:billing_portal")
        mock_customer = MagicMock()
        mock_customer.id = "cus_test123"
        mock_portal = MagicMock()
        mock_portal.url = "https://billing.stripe.com/session/test"

        with patch.object(type(user), "customer", new_callable=PropertyMock, return_value=mock_customer), \
             patch("apps.subscriptions.views.stripe.billing_portal.Session.create", return_value=mock_portal):
            response = client.get(url)

        assert response.status_code == 302
        assert response.url == mock_portal.url

    def test_stripe_error_redirects_to_management(self, client, user):
        client.force_login(user)
        url = reverse("subscriptions:billing_portal")
        mock_customer = MagicMock()
        mock_customer.id = "cus_test123"

        with patch.object(type(user), "customer", new_callable=PropertyMock, return_value=mock_customer), \
             patch("apps.subscriptions.views.stripe.billing_portal.Session.create", side_effect=Exception("Error")):
            response = client.get(url)

        assert response.status_code == 302
        assert reverse("user_dashboard:subscription_management") in response.url
