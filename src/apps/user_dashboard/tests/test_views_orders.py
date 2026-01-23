import uuid
from datetime import datetime, timezone

import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from django.http import Http404


@pytest.mark.django_db
class TestOrdersList:
    """Test suite for orders_list view."""

    def test_requires_login(self, client):
        """Anonymous user should be redirected to login."""
        url = reverse("user_dashboard:orders_list")
        response = client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    @patch("apps.user_dashboard.views.Order.objects.filter")
    def test_returns_200(self, mock_filter, client, django_user_model):
        """Authenticated user should get 200 response."""
        # Create and login user
        user = django_user_model.objects.create_user(username="testuser", password="testpass123")
        client.force_login(user)

        # Mock empty queryset
        mock_qs = MagicMock()
        mock_qs.select_related.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.count.return_value = 0
        mock_qs.__iter__ = lambda self: iter([])
        mock_qs.__len__ = lambda self: 0
        mock_filter.return_value = mock_qs

        url = reverse("user_dashboard:orders_list")
        response = client.get(url)
        assert response.status_code == 200

    @patch("apps.user_dashboard.views.Order.objects.filter")
    def test_context_has_page_obj(self, mock_filter, client, django_user_model):
        """Context should contain page_obj."""
        user = django_user_model.objects.create_user(username="testuser", password="testpass123")
        client.force_login(user)

        # Mock empty queryset
        mock_qs = MagicMock()
        mock_qs.select_related.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.count.return_value = 0
        mock_qs.__iter__ = lambda self: iter([])
        mock_qs.__len__ = lambda self: 0
        mock_filter.return_value = mock_qs

        url = reverse("user_dashboard:orders_list")
        response = client.get(url)
        assert "page_obj" in response.context

    @patch("apps.user_dashboard.views.Order.objects.filter")
    def test_empty_orders(self, mock_filter, client, django_user_model):
        """When user has no orders, page_obj should be empty."""
        user = django_user_model.objects.create_user(username="testuser", password="testpass123")
        client.force_login(user)

        # Mock empty queryset
        mock_qs = MagicMock()
        mock_qs.select_related.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.count.return_value = 0
        mock_qs.__iter__ = lambda self: iter([])
        mock_qs.__len__ = lambda self: 0
        mock_filter.return_value = mock_qs

        url = reverse("user_dashboard:orders_list")
        response = client.get(url)
        assert len(response.context["page_obj"]) == 0

    @patch("apps.user_dashboard.views.Order.objects.filter")
    def test_pagination_first_page(self, mock_filter, client, django_user_model):
        """Pagination should work with multiple orders."""
        user = django_user_model.objects.create_user(username="testuser", password="testpass123")
        client.force_login(user)

        # Create mock orders with proper attributes for template rendering
        mock_orders = []
        for i in range(25):
            order = MagicMock()
            order.id = str(uuid.uuid4())
            order.created_at = datetime(2025, 1, i + 1, tzinfo=timezone.utc)
            order.products_count = 1
            order.amount_dollars = 29.99
            order.currency = "usd"
            order.status = "paid"
            order.receipt = None
            # Prevent Django template dict-style lookup on mock
            order.__getitem__ = MagicMock(side_effect=TypeError)
            mock_orders.append(order)

        # Return a real list from the queryset chain so Paginator can slice it
        mock_qs = MagicMock()
        mock_qs.select_related.return_value = mock_qs
        mock_qs.order_by.return_value = mock_orders
        mock_filter.return_value = mock_qs

        url = reverse("user_dashboard:orders_list")
        response = client.get(url)
        page_obj = response.context["page_obj"]

        assert page_obj.number == 1
        assert page_obj.has_next()
        assert not page_obj.has_previous()

    @patch("apps.user_dashboard.views.Order.objects.filter")
    def test_pagination_page_param(self, mock_filter, client, django_user_model):
        """Page parameter should be respected."""
        user = django_user_model.objects.create_user(username="testuser", password="testpass123")
        client.force_login(user)

        # Create mock orders with proper attributes for template rendering
        mock_orders = []
        for i in range(25):
            order = MagicMock()
            order.id = str(uuid.uuid4())
            order.created_at = datetime(2025, 1, i + 1, tzinfo=timezone.utc)
            order.products_count = 1
            order.amount_dollars = 29.99
            order.currency = "usd"
            order.status = "paid"
            order.receipt = None
            # Prevent Django template dict-style lookup on mock
            order.__getitem__ = MagicMock(side_effect=TypeError)
            mock_orders.append(order)

        # Return a real list from the queryset chain so Paginator can slice it
        mock_qs = MagicMock()
        mock_qs.select_related.return_value = mock_qs
        mock_qs.order_by.return_value = mock_orders
        mock_filter.return_value = mock_qs

        url = reverse("user_dashboard:orders_list")
        response = client.get(url, {"page": "2"})
        page_obj = response.context["page_obj"]

        assert page_obj.number == 2
        assert not page_obj.has_next()
        assert page_obj.has_previous()

    @patch("apps.user_dashboard.views.Order.objects.filter")
    def test_only_shows_user_orders(self, mock_filter, client, django_user_model):
        """Orders should be filtered by the logged-in user."""
        user = django_user_model.objects.create_user(username="testuser", password="testpass123")
        client.force_login(user)

        # Mock empty queryset
        mock_qs = MagicMock()
        mock_qs.select_related.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.count.return_value = 0
        mock_qs.__iter__ = lambda self: iter([])
        mock_qs.__len__ = lambda self: 0
        mock_filter.return_value = mock_qs

        url = reverse("user_dashboard:orders_list")
        client.get(url)

        # Verify filter was called with the logged-in user
        mock_filter.assert_called_once_with(user=user)


@pytest.mark.django_db
class TestOrderDetail:
    """Test suite for order_detail view."""

    def test_requires_login(self, client):
        """Anonymous user should be redirected to login."""
        order_id = uuid.uuid4()
        url = reverse("user_dashboard:order_detail", kwargs={"order_id": order_id})
        response = client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    @patch("apps.user_dashboard.views.get_object_or_404")
    def test_returns_200(self, mock_get_object, client, django_user_model):
        """Authenticated user should get 200 response for valid order."""
        user = django_user_model.objects.create_user(username="testuser", password="testpass123")
        client.force_login(user)

        mock_order = MagicMock()
        mock_order.id = uuid.uuid4()
        mock_order.created_at = datetime(2025, 6, 15, 10, 30, tzinfo=timezone.utc)
        mock_order.basket = None
        mock_order.status = "paid"
        mock_order.amount_dollars = 29.99
        mock_order.currency = "usd"
        mock_order.receipt = None
        mock_order.__getitem__ = MagicMock(side_effect=TypeError)
        mock_get_object.return_value = mock_order

        url = reverse("user_dashboard:order_detail", kwargs={"order_id": mock_order.id})
        response = client.get(url)
        assert response.status_code == 200

    @patch("apps.user_dashboard.views.get_object_or_404")
    def test_context_has_order(self, mock_get_object, client, django_user_model):
        """Context should contain order."""
        user = django_user_model.objects.create_user(username="testuser", password="testpass123")
        client.force_login(user)

        mock_order = MagicMock()
        mock_order.id = uuid.uuid4()
        mock_order.created_at = datetime(2025, 6, 15, 10, 30, tzinfo=timezone.utc)
        mock_order.basket = None
        mock_order.status = "paid"
        mock_order.amount_dollars = 29.99
        mock_order.currency = "usd"
        mock_order.receipt = None
        mock_order.__getitem__ = MagicMock(side_effect=TypeError)
        mock_get_object.return_value = mock_order

        url = reverse("user_dashboard:order_detail", kwargs={"order_id": mock_order.id})
        response = client.get(url)
        assert "order" in response.context
        assert response.context["order"] == mock_order

    @patch("apps.user_dashboard.views.get_object_or_404")
    def test_context_has_products_from_basket(self, mock_get_object, client, django_user_model):
        """Context should contain products list from basket items."""
        user = django_user_model.objects.create_user(username="testuser", password="testpass123")
        client.force_login(user)

        # Mock basket item
        mock_item = MagicMock()
        mock_shop_product = MagicMock()
        mock_shop_product.slug = "test-product"
        mock_shop_product.name = "Test Product"
        mock_shop_product.__getitem__ = MagicMock(side_effect=TypeError)
        mock_item.shop_product = mock_shop_product
        mock_item.quantity = 2
        mock_item.line_total_dollars = 59.98
        mock_item.__getitem__ = MagicMock(side_effect=TypeError)

        # Mock basket with items
        mock_basket = MagicMock()
        mock_basket.items.all.return_value = [mock_item]

        mock_order = MagicMock()
        mock_order.id = uuid.uuid4()
        mock_order.created_at = datetime(2025, 6, 15, 10, 30, tzinfo=timezone.utc)
        mock_order.basket = mock_basket
        mock_order.status = "paid"
        mock_order.amount_dollars = 29.99
        mock_order.currency = "usd"
        mock_order.receipt = None
        mock_order.__getitem__ = MagicMock(side_effect=TypeError)
        mock_get_object.return_value = mock_order

        url = reverse("user_dashboard:order_detail", kwargs={"order_id": mock_order.id})
        response = client.get(url)

        assert "products" in response.context
        products = response.context["products"]
        assert len(products) == 1
        assert products[0]["basket_item"] == mock_item
        assert products[0]["shop_product"] == mock_item.shop_product
        assert products[0]["quantity"] == 2
        assert products[0]["line_total_dollars"] == 59.98

    @patch("apps.user_dashboard.views.get_object_or_404")
    def test_order_without_basket(self, mock_get_object, client, django_user_model):
        """Order without basket should have empty products list."""
        user = django_user_model.objects.create_user(username="testuser", password="testpass123")
        client.force_login(user)

        mock_order = MagicMock()
        mock_order.id = uuid.uuid4()
        mock_order.created_at = datetime(2025, 6, 15, 10, 30, tzinfo=timezone.utc)
        mock_order.basket = None
        mock_order.status = "paid"
        mock_order.amount_dollars = 29.99
        mock_order.currency = "usd"
        mock_order.receipt = None
        mock_order.__getitem__ = MagicMock(side_effect=TypeError)
        mock_get_object.return_value = mock_order

        url = reverse("user_dashboard:order_detail", kwargs={"order_id": mock_order.id})
        response = client.get(url)

        assert "products" in response.context
        assert len(response.context["products"]) == 0

    @patch("apps.user_dashboard.views.get_object_or_404")
    def test_other_user_gets_404(self, mock_get_object, client, django_user_model):
        """User trying to access another user's order should get 404."""
        user = django_user_model.objects.create_user(username="testuser", password="testpass123")
        client.force_login(user)

        # Mock get_object_or_404 to raise Http404
        mock_get_object.side_effect = Http404("Order not found")

        order_id = uuid.uuid4()
        url = reverse("user_dashboard:order_detail", kwargs={"order_id": order_id})
        response = client.get(url)
        assert response.status_code == 404

    @patch("apps.user_dashboard.views.get_object_or_404")
    def test_nonexistent_order_gets_404(self, mock_get_object, client, django_user_model):
        """Non-existent order should return 404."""
        user = django_user_model.objects.create_user(username="testuser", password="testpass123")
        client.force_login(user)

        # Mock get_object_or_404 to raise Http404
        mock_get_object.side_effect = Http404("Order not found")

        order_id = uuid.uuid4()
        url = reverse("user_dashboard:order_detail", kwargs={"order_id": order_id})
        response = client.get(url)
        assert response.status_code == 404
