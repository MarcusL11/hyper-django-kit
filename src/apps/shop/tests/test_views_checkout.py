import pytest
import uuid
from unittest.mock import patch, MagicMock
from django.urls import reverse
from apps.shop.models import Basket, Order


@pytest.mark.django_db
class TestCreateCheckoutSession:
    """
    Tests for create_checkout_session view.
    POST /shop/checkout/create-session/
    @require_POST + @login_required
    """

    def test_requires_login(self, client):
        """Anonymous users are redirected to login page."""
        url = reverse("shop:create_checkout_session")
        response = client.post(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_requires_post_method(self, client, user):
        """GET requests are not allowed (405 Method Not Allowed)."""
        client.force_login(user)
        url = reverse("shop:create_checkout_session")
        response = client.get(url)
        assert response.status_code == 405

    def test_no_basket_redirects(self, client, user):
        """User with no basket shows error and redirects to view_basket."""
        client.force_login(user)
        url = reverse("shop:create_checkout_session")
        response = client.post(url)
        assert response.status_code == 302
        assert reverse("shop:view_basket") in response.url

    def test_empty_basket_redirects(self, client, user, basket):
        """Empty basket shows error and redirects to view_basket."""
        client.force_login(user)
        url = reverse("shop:create_checkout_session")
        response = client.post(url)
        assert response.status_code == 302
        assert reverse("shop:view_basket") in response.url

    def test_no_valid_line_items_redirects(self, client, user):
        """Basket with no valid line items redirects to view_basket."""
        client.force_login(user)

        # Mock basket with items but no valid prices
        mock_basket = MagicMock()
        mock_basket.is_empty = False
        mock_basket.items.all.return_value = [
            MagicMock(product=MagicMock(default_price=None), quantity=1)
        ]

        mock_customer = MagicMock()
        mock_customer.id = "cus_test123"

        with patch("apps.shop.views.Basket.objects.get", return_value=mock_basket), \
             patch("apps.shop.views.get_or_create_customer", return_value=(mock_customer, False)):
            url = reverse("shop:create_checkout_session")
            response = client.post(url)

        assert response.status_code == 302
        assert reverse("shop:view_basket") in response.url

    def test_redirects_to_stripe_on_success(self, client, user):
        """Successful checkout creation redirects to Stripe checkout URL."""
        client.force_login(user)

        # Mock basket with valid items
        mock_item = MagicMock()
        mock_item.product = MagicMock()
        mock_item.product.default_price = MagicMock()
        mock_item.product.default_price.id = "price_test123"
        mock_item.quantity = 1

        mock_basket = MagicMock()
        mock_basket.id = uuid.uuid4()
        mock_basket.is_empty = False
        mock_basket.items.all.return_value = [mock_item]

        mock_customer = MagicMock()
        mock_customer.id = "cus_test123"

        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_session.id = "cs_test123"

        with patch("apps.shop.views.Basket.objects.get", return_value=mock_basket), \
             patch("apps.shop.views.get_or_create_customer", return_value=(mock_customer, False)), \
             patch("apps.shop.views.stripe.checkout.Session.create", return_value=mock_session):
            url = reverse("shop:create_checkout_session")
            response = client.post(url)

        # Django test client returns 302 for redirects (HttpResponseRedirect)
        # The code=303 is only used in actual HTTP responses
        assert response.status_code == 302
        assert response.url == "https://checkout.stripe.com/test"

    def test_creates_stripe_session_with_correct_parameters(self, client, user):
        """Stripe session is created with correct customer, line_items, and metadata."""
        client.force_login(user)

        mock_item = MagicMock()
        mock_item.product = MagicMock()
        mock_item.product.default_price = MagicMock()
        mock_item.product.default_price.id = "price_test123"
        mock_item.quantity = 2

        mock_basket = MagicMock()
        mock_basket.id = uuid.uuid4()
        mock_basket.is_empty = False
        mock_basket.items.all.return_value = [mock_item]

        mock_customer = MagicMock()
        mock_customer.id = "cus_test123"

        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_session.id = "cs_test123"

        with patch("apps.shop.views.Basket.objects.get", return_value=mock_basket), \
             patch("apps.shop.views.get_or_create_customer", return_value=(mock_customer, False)), \
             patch("apps.shop.views.stripe.checkout.Session.create", return_value=mock_session) as mock_create:
            url = reverse("shop:create_checkout_session")
            response = client.post(url)

        # Verify Stripe session creation parameters
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["customer"] == "cus_test123"
        assert call_kwargs["line_items"] == [{"price": "price_test123", "quantity": 2}]
        assert call_kwargs["mode"] == "payment"
        assert call_kwargs["client_reference_id"] == str(user.id)
        assert call_kwargs["metadata"]["basket_id"] == str(mock_basket.id)
        assert call_kwargs["metadata"]["user_id"] == str(user.id)


@pytest.mark.django_db
class TestOrderConfirm:
    """
    Tests for order_confirm view.
    GET /shop/order/confirm/?session_id=<id>
    @login_required
    """

    def test_requires_login(self, client):
        """Anonymous users are redirected to login page."""
        url = reverse("shop:order_confirm")
        response = client.get(url, {"session_id": "cs_test"})
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_missing_session_id_redirects(self, client, user):
        """Missing session_id parameter shows error and redirects to product_list."""
        client.force_login(user)
        url = reverse("shop:order_confirm")
        response = client.get(url)
        assert response.status_code == 302
        assert reverse("shop:product_list") in response.url

    def test_user_mismatch_redirects(self, client, user):
        """Mismatched user ID in session.client_reference_id redirects with error."""
        client.force_login(user)

        mock_stripe_session = MagicMock()
        mock_stripe_session.client_reference_id = str(uuid.uuid4())  # Different user ID

        with patch("apps.shop.views.stripe.checkout.Session.retrieve", return_value=mock_stripe_session):
            url = reverse("shop:order_confirm")
            response = client.get(url, {"session_id": "cs_test123"})

        assert response.status_code == 302
        assert reverse("shop:product_list") in response.url

    def test_creates_order_on_success(self, client, user, basket):
        """Successful confirmation creates Order and marks basket as checked out."""
        client.force_login(user)

        mock_stripe_session = MagicMock()
        mock_stripe_session.client_reference_id = str(user.id)
        mock_stripe_session.metadata = {"basket_id": str(basket.id)}
        mock_stripe_session.line_items = MagicMock()
        mock_stripe_session.payment_intent = MagicMock()

        mock_djstripe_session = MagicMock()
        mock_djstripe_session.id = "cs_test123"

        mock_order = MagicMock()
        mock_order.id = uuid.uuid4()

        with patch("apps.shop.views.stripe.checkout.Session.retrieve", return_value=mock_stripe_session), \
             patch("apps.shop.views.StripeSession.sync_from_stripe_data", return_value=mock_djstripe_session), \
             patch("apps.shop.models.Order.objects.get_or_create") as mock_order_create:
            mock_order_create.return_value = (mock_order, True)

            url = reverse("shop:order_confirm")
            response = client.get(url, {"session_id": "cs_test123"})

        assert response.status_code == 200
        mock_order_create.assert_called_once()
        call_kwargs = mock_order_create.call_args.kwargs
        assert call_kwargs["session"] == mock_djstripe_session
        assert call_kwargs["defaults"]["user"] == user
        assert call_kwargs["defaults"]["basket"] == basket

        # Verify basket is marked as checked out
        basket.refresh_from_db()
        assert basket.checked_out is True

    def test_handles_missing_basket_gracefully(self, client, user):
        """Order confirmation works even if basket is not found."""
        client.force_login(user)

        mock_stripe_session = MagicMock()
        mock_stripe_session.client_reference_id = str(user.id)
        mock_stripe_session.metadata = {"basket_id": str(uuid.uuid4())}  # Non-existent basket
        mock_stripe_session.line_items = MagicMock()
        mock_stripe_session.payment_intent = MagicMock()

        mock_djstripe_session = MagicMock()
        mock_djstripe_session.id = "cs_test123"

        mock_order = MagicMock()

        with patch("apps.shop.views.stripe.checkout.Session.retrieve", return_value=mock_stripe_session), \
             patch("apps.shop.views.StripeSession.sync_from_stripe_data", return_value=mock_djstripe_session), \
             patch("apps.shop.models.Order.objects.get_or_create", return_value=(mock_order, True)):
            url = reverse("shop:order_confirm")
            response = client.get(url, {"session_id": "cs_test123"})

        assert response.status_code == 200

    def test_renders_order_success_template(self, client, user, basket):
        """Successful confirmation renders order_success.html with correct context."""
        client.force_login(user)

        mock_stripe_session = MagicMock()
        mock_stripe_session.client_reference_id = str(user.id)
        mock_stripe_session.metadata = {"basket_id": str(basket.id)}
        mock_stripe_session.line_items = MagicMock()
        mock_stripe_session.payment_intent = MagicMock()

        mock_djstripe_session = MagicMock()
        mock_djstripe_session.id = "cs_test123"

        mock_order = MagicMock()
        mock_order.id = uuid.uuid4()

        with patch("apps.shop.views.stripe.checkout.Session.retrieve", return_value=mock_stripe_session), \
             patch("apps.shop.views.StripeSession.sync_from_stripe_data", return_value=mock_djstripe_session), \
             patch("apps.shop.models.Order.objects.get_or_create", return_value=(mock_order, True)):
            url = reverse("shop:order_confirm")
            response = client.get(url, {"session_id": "cs_test123"})

        assert response.status_code == 200
        assert "shop/checkout/order_success.html" in [t.name for t in response.templates]
        assert "order" in response.context
        assert "primary_url" in response.context
        assert "secondary_url" in response.context

    def test_handles_duplicate_order_confirmation(self, client, user, basket):
        """Attempting to confirm the same order twice does not create duplicate."""
        client.force_login(user)

        mock_stripe_session = MagicMock()
        mock_stripe_session.client_reference_id = str(user.id)
        mock_stripe_session.metadata = {"basket_id": str(basket.id)}
        mock_stripe_session.line_items = MagicMock()
        mock_stripe_session.payment_intent = MagicMock()

        mock_djstripe_session = MagicMock()
        mock_djstripe_session.id = "cs_test123"

        mock_order = MagicMock()
        mock_order.id = uuid.uuid4()

        with patch("apps.shop.views.stripe.checkout.Session.retrieve", return_value=mock_stripe_session), \
             patch("apps.shop.views.StripeSession.sync_from_stripe_data", return_value=mock_djstripe_session), \
             patch("apps.shop.models.Order.objects.get_or_create") as mock_order_create:
            mock_order_create.return_value = (mock_order, False)  # created=False

            url = reverse("shop:order_confirm")
            response = client.get(url, {"session_id": "cs_test123"})

        assert response.status_code == 200
        mock_order_create.assert_called_once()


@pytest.mark.django_db
class TestCheckoutCanceled:
    """
    Tests for checkout_canceled view.
    GET /shop/checkout/canceled/
    @login_required
    """

    def test_requires_login(self, client):
        """Anonymous users are redirected to login page."""
        url = reverse("shop:checkout_canceled")
        response = client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_returns_200_for_authenticated_user(self, client, user):
        """Authenticated user can access canceled page."""
        client.force_login(user)
        url = reverse("shop:checkout_canceled")
        response = client.get(url)
        assert response.status_code == 200

    def test_renders_checkout_canceled_template(self, client, user):
        """Renders checkout_canceled.html template."""
        client.force_login(user)
        url = reverse("shop:checkout_canceled")
        response = client.get(url)
        assert response.status_code == 200
        assert "shop/checkout/checkout_canceled.html" in [t.name for t in response.templates]

    def test_contains_navigation_urls_in_context(self, client, user):
        """Context contains primary_url and secondary_url for navigation."""
        client.force_login(user)
        url = reverse("shop:checkout_canceled")
        response = client.get(url)
        assert response.status_code == 200
        assert "primary_url" in response.context
        assert "secondary_url" in response.context
        assert response.context["primary_url"] == reverse("shop:view_basket")
        assert response.context["secondary_url"] == reverse("shop:product_list")
