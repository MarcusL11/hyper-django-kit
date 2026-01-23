import uuid
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.http import Http404
from django.urls import reverse

from apps.shop.models import Basket, BasketItem

User = get_user_model()


@pytest.mark.django_db
class TestViewBasket:
    """Tests for the view_basket view."""

    def test_requires_login(self, client):
        """Anonymous users are redirected to login."""
        url = reverse("shop:view_basket")
        response = client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_returns_200_for_authenticated_user(self, client, user):
        """Logged-in user can view basket page."""
        client.force_login(user)
        url = reverse("shop:view_basket")
        response = client.get(url)
        assert response.status_code == 200

    def test_context_contains_basket(self, client, user, basket):
        """Basket is passed in context when user has a basket."""
        client.force_login(user)
        url = reverse("shop:view_basket")
        response = client.get(url)
        assert response.context["basket"] == basket

    def test_context_basket_none_when_no_basket(self, client, user):
        """Context basket is None when user has no basket."""
        client.force_login(user)
        url = reverse("shop:view_basket")
        response = client.get(url)
        assert response.context["basket"] is None


@pytest.mark.django_db
class TestAddToBasket:
    """Tests for the add_to_basket view."""

    def test_requires_login(self, client):
        """Anonymous users are redirected to login."""
        url = reverse("shop:add_to_basket")
        response = client.post(url, {"price_id": "price_x", "stripe_product_id": "prod_x"})
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_requires_post(self, client, user):
        """GET requests are rejected with 405 Method Not Allowed."""
        client.force_login(user)
        url = reverse("shop:add_to_basket")
        response = client.get(url)
        assert response.status_code == 405

    def test_creates_basket_and_item(self, client, user, mock_stripe_product):
        """Adding a product creates basket and basket item."""
        client.force_login(user)
        url = reverse("shop:add_to_basket")

        mock_basket_item = MagicMock()
        with patch("apps.shop.views.StripeProduct.objects.get", return_value=mock_stripe_product), \
             patch("apps.shop.views.BasketItem.objects.get_or_create", return_value=(mock_basket_item, True)):
            response = client.post(url, {
                "price_id": "price_test123",
                "stripe_product_id": "prod_test123",
                "quantity": "1",
            })

        assert response.status_code == 302
        assert response.url == reverse("shop:view_basket")
        assert Basket.objects.filter(user=user, checked_out=False).exists()

    def test_increments_quantity_when_item_exists(self, client, user, basket, mock_stripe_product):
        """Adding an existing product increments its quantity."""
        client.force_login(user)
        url = reverse("shop:add_to_basket")

        mock_basket_item = MagicMock()
        mock_basket_item.quantity = 2

        with patch("apps.shop.views.StripeProduct.objects.get", return_value=mock_stripe_product), \
             patch("apps.shop.views.BasketItem.objects.get_or_create", return_value=(mock_basket_item, False)):
            response = client.post(url, {
                "price_id": "price_test123",
                "stripe_product_id": "prod_test123",
                "quantity": "3",
            })

        assert response.status_code == 302
        assert response.url == reverse("shop:view_basket")
        # When item already exists (created=False), quantity is incremented
        assert mock_basket_item.quantity == 5  # 2 + 3
        mock_basket_item.save.assert_called_once()

    def test_missing_price_id_redirects_with_error(self, client, user):
        """Missing price_id shows error and redirects to product list."""
        client.force_login(user)
        url = reverse("shop:add_to_basket")
        response = client.post(url, {"stripe_product_id": "prod_x"})
        assert response.status_code == 302
        assert reverse("shop:product_list") in response.url

    def test_missing_stripe_product_id_redirects_with_error(self, client, user):
        """Missing stripe_product_id shows error and redirects to product list."""
        client.force_login(user)
        url = reverse("shop:add_to_basket")
        response = client.post(url, {"price_id": "price_x"})
        assert response.status_code == 302
        assert reverse("shop:product_list") in response.url

    def test_missing_all_params_redirects_with_error(self, client, user):
        """Missing all required parameters shows error and redirects to product list."""
        client.force_login(user)
        url = reverse("shop:add_to_basket")
        response = client.post(url, {})
        assert response.status_code == 302
        assert reverse("shop:product_list") in response.url

    def test_stripe_product_not_found_shows_error(self, client, user):
        """Non-existent Stripe product shows error message and redirects."""
        client.force_login(user)
        url = reverse("shop:add_to_basket")

        from djstripe.models import Product as StripeProduct
        with patch("apps.shop.views.StripeProduct.objects.get", side_effect=StripeProduct.DoesNotExist):
            response = client.post(url, {
                "price_id": "price_fake",
                "stripe_product_id": "prod_fake",
                "quantity": "1",
            })

        assert response.status_code == 302
        assert reverse("shop:product_list") in response.url


@pytest.mark.django_db
class TestUpdateBasketItem:
    """Tests for the update_basket_item view."""

    def test_requires_login(self, client):
        """Anonymous users are redirected to login."""
        url = reverse("shop:update_basket_item", kwargs={"item_id": uuid.uuid4()})
        response = client.post(url, {"quantity": "2"})
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_requires_post(self, client, user):
        """GET requests are rejected with 405 Method Not Allowed."""
        client.force_login(user)
        url = reverse("shop:update_basket_item", kwargs={"item_id": uuid.uuid4()})
        response = client.get(url)
        assert response.status_code == 405

    def test_updates_quantity(self, client, user, basket):
        """Quantity is updated for valid request."""
        client.force_login(user)
        mock_item = MagicMock()
        mock_item.quantity = 1

        with patch("apps.shop.views.get_object_or_404", return_value=mock_item):
            url = reverse("shop:update_basket_item", kwargs={"item_id": uuid.uuid4()})
            response = client.post(url, {"quantity": "3"})

        assert response.status_code == 302
        assert response.url == reverse("shop:view_basket")
        assert mock_item.quantity == 3
        mock_item.save.assert_called_once()

    def test_quantity_below_1_rejected(self, client, user):
        """Quantity less than 1 shows error and redirects."""
        client.force_login(user)
        url = reverse("shop:update_basket_item", kwargs={"item_id": uuid.uuid4()})
        response = client.post(url, {"quantity": "0"})
        assert response.status_code == 302
        assert response.url == reverse("shop:view_basket")

    def test_negative_quantity_rejected(self, client, user):
        """Negative quantity shows error and redirects."""
        client.force_login(user)
        url = reverse("shop:update_basket_item", kwargs={"item_id": uuid.uuid4()})
        response = client.post(url, {"quantity": "-1"})
        assert response.status_code == 302
        assert response.url == reverse("shop:view_basket")

    def test_missing_quantity_parameter(self, client, user):
        """Missing quantity parameter is handled gracefully."""
        client.force_login(user)
        url = reverse("shop:update_basket_item", kwargs={"item_id": uuid.uuid4()})
        response = client.post(url, {})
        assert response.status_code == 302

    def test_other_user_cannot_update(self, client, other_user):
        """Users cannot update items from another user's basket (caught as error, redirects)."""
        client.force_login(other_user)
        with patch("apps.shop.views.get_object_or_404", side_effect=Http404):
            url = reverse("shop:update_basket_item", kwargs={"item_id": uuid.uuid4()})
            response = client.post(url, {"quantity": "5"})
        # View catches Http404 in try/except and redirects with error message
        assert response.status_code == 302
        assert response.url == reverse("shop:view_basket")

    def test_cannot_update_checked_out_basket_item(self, client, user):
        """Users cannot update items in a checked out basket (caught as error, redirects)."""
        client.force_login(user)
        with patch("apps.shop.views.get_object_or_404", side_effect=Http404):
            url = reverse("shop:update_basket_item", kwargs={"item_id": uuid.uuid4()})
            response = client.post(url, {"quantity": "2"})
        assert response.status_code == 302
        assert response.url == reverse("shop:view_basket")


@pytest.mark.django_db
class TestRemoveBasketItem:
    """Tests for the remove_basket_item view."""

    def test_requires_login(self, client):
        """Anonymous users are redirected to login."""
        url = reverse("shop:remove_basket_item", kwargs={"item_id": uuid.uuid4()})
        response = client.post(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_requires_post(self, client, user):
        """GET requests are rejected with 405 Method Not Allowed."""
        client.force_login(user)
        url = reverse("shop:remove_basket_item", kwargs={"item_id": uuid.uuid4()})
        response = client.get(url)
        assert response.status_code == 405

    def test_deletes_item(self, client, user):
        """Item is deleted on valid request."""
        client.force_login(user)
        mock_item = MagicMock()

        with patch("apps.shop.views.get_object_or_404", return_value=mock_item):
            url = reverse("shop:remove_basket_item", kwargs={"item_id": uuid.uuid4()})
            response = client.post(url)

        assert response.status_code == 302
        assert response.url == reverse("shop:view_basket")
        mock_item.delete.assert_called_once()

    def test_other_user_cannot_remove(self, client, other_user):
        """Users cannot remove items from another user's basket (caught as error, redirects)."""
        client.force_login(other_user)
        with patch("apps.shop.views.get_object_or_404", side_effect=Http404):
            url = reverse("shop:remove_basket_item", kwargs={"item_id": uuid.uuid4()})
            response = client.post(url)
        # View catches Http404 in try/except and redirects with error message
        assert response.status_code == 302
        assert response.url == reverse("shop:view_basket")

    def test_cannot_remove_from_checked_out_basket(self, client, user):
        """Users cannot remove items from a checked out basket (caught as error, redirects)."""
        client.force_login(user)
        with patch("apps.shop.views.get_object_or_404", side_effect=Http404):
            url = reverse("shop:remove_basket_item", kwargs={"item_id": uuid.uuid4()})
            response = client.post(url)
        assert response.status_code == 302
        assert response.url == reverse("shop:view_basket")

    def test_nonexistent_item_redirects_with_error(self, client, user):
        """Attempting to remove a non-existent item redirects with error."""
        client.force_login(user)
        with patch("apps.shop.views.get_object_or_404", side_effect=Http404):
            url = reverse("shop:remove_basket_item", kwargs={"item_id": uuid.uuid4()})
            response = client.post(url)
        assert response.status_code == 302
        assert response.url == reverse("shop:view_basket")
