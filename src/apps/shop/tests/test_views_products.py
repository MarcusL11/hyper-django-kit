"""
Tests for shop product views (product_list and product_detail).

These tests verify the public-facing product browsing functionality,
including filtering, sorting, and product detail pages.
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from django.urls import reverse
from apps.shop.models import ShopProduct, ShopCategory


@pytest.mark.django_db
class TestProductListView:
    """Tests for the product_list view (GET /shop/products/)."""

    def test_returns_200(self, client, shop_product):
        """Product list page loads successfully."""
        url = reverse("shop:product_list")
        response = client.get(url)
        assert response.status_code == 200

    def test_shows_active_products(self, client, shop_product, inactive_product):
        """Only active products appear in the list."""
        url = reverse("shop:product_list")
        response = client.get(url)
        assert shop_product.name.encode() in response.content
        assert inactive_product.name.encode() not in response.content

    def test_filters_by_category(self, client, shop_product, shop_category, db):
        """Category filter shows only matching products."""
        # Create a product in a different category
        other_cat = ShopCategory.objects.create(name="Toys", slug="toys", is_active=True)
        other_product = ShopProduct.objects.create(
            product_id="prod_other",
            name="Other Product",
            slug="other-product",
            category=other_cat,
            is_active=True,
        )
        url = reverse("shop:product_list")
        response = client.get(url, {"category": "books"})
        assert shop_product.name.encode() in response.content
        assert other_product.name.encode() not in response.content

    def test_excludes_inactive_categories_from_filter(self, client, shop_category, inactive_category):
        """Inactive categories don't appear in category filter list."""
        url = reverse("shop:product_list")
        response = client.get(url)
        # The view passes categories = ShopCategory.objects.filter(is_active=True)
        categories = response.context["categories"]
        assert shop_category in categories
        assert inactive_category not in categories

    def test_sort_by_date_new(self, client, shop_product, shop_category, db):
        """Products can be sorted by newest first."""
        # Create an older product
        older_product = ShopProduct.objects.create(
            product_id="prod_old",
            name="Older Product",
            slug="older-product",
            category=shop_category,
            is_active=True,
        )
        # Make the older product actually older by updating the created_at
        older_product.created_at = "2023-01-01T00:00:00Z"
        older_product.save()

        url = reverse("shop:product_list")
        response = client.get(url, {"sort": "date_new"})

        # The newer product should appear first in the page_obj
        products = list(response.context["page_obj"])
        assert products[0].id == shop_product.id

    def test_sort_by_date_old(self, client, shop_product, shop_category, db):
        """Products can be sorted by oldest first."""
        # Create an older product
        older_product = ShopProduct.objects.create(
            product_id="prod_old",
            name="Older Product",
            slug="older-product",
            category=shop_category,
            is_active=True,
        )
        # Make the older product actually older
        older_product.created_at = "2023-01-01T00:00:00Z"
        older_product.save()

        url = reverse("shop:product_list")
        response = client.get(url, {"sort": "date_old"})

        # The older product should appear first
        products = list(response.context["page_obj"])
        assert products[0].id == older_product.id

    def test_pagination(self, client, shop_category, db, settings):
        """Products are paginated according to settings."""
        # Create more products than the per-page limit
        per_page = settings.SHOP_PRODUCTS_PER_PAGE
        for i in range(per_page + 2):
            ShopProduct.objects.create(
                product_id=f"prod_{i}",
                name=f"Product {i}",
                slug=f"product-{i}",
                category=shop_category,
                is_active=True,
            )

        url = reverse("shop:product_list")
        response = client.get(url)

        # First page should have exactly per_page items
        assert len(response.context["page_obj"]) == per_page

        # Second page should have the remaining items
        response = client.get(url, {"page": 2})
        assert len(response.context["page_obj"]) == 2

    def test_context_data(self, client, shop_product, shop_category):
        """View provides correct context data."""
        url = reverse("shop:product_list")
        response = client.get(url, {"category": "books", "sort": "date_new"})

        assert "products" in response.context
        assert "page_obj" in response.context
        assert "categories" in response.context
        assert response.context["selected_category"] == "books"
        assert response.context["selected_sort"] == "date_new"


@pytest.mark.django_db
class TestProductDetailView:
    """Tests for the product_detail view (GET /shop/products/<slug>/)."""

    def test_returns_200_with_stripe_product(self, client, shop_product):
        """Product detail loads when Stripe product is synced."""
        mock_price = MagicMock()
        mock_price.id = "price_test123"
        mock_price.unit_amount = 2999
        mock_price.currency = "usd"

        mock_stripe = MagicMock()
        mock_stripe.id = "prod_test123"
        mock_stripe.default_price = mock_price

        with patch.object(
            ShopProduct, "stripe_product", new_callable=PropertyMock, return_value=mock_stripe
        ):
            url = reverse("shop:product_detail", kwargs={"slug": shop_product.slug})
            response = client.get(url)
            assert response.status_code == 200

    def test_redirects_when_stripe_product_missing(self, client, shop_product):
        """Redirects to product list when Stripe product not synced."""
        with patch.object(
            ShopProduct, "stripe_product", new_callable=PropertyMock, return_value=None
        ):
            url = reverse("shop:product_detail", kwargs={"slug": shop_product.slug})
            response = client.get(url)
            assert response.status_code == 302
            assert reverse("shop:product_list") in response.url

    def test_redirects_when_no_default_price(self, client, shop_product):
        """Redirects when Stripe product has no default price."""
        mock_stripe = MagicMock()
        mock_stripe.id = "prod_test123"
        mock_stripe.default_price = None

        with patch.object(
            ShopProduct, "stripe_product", new_callable=PropertyMock, return_value=mock_stripe
        ):
            url = reverse("shop:product_detail", kwargs={"slug": shop_product.slug})
            response = client.get(url)
            assert response.status_code == 302
            assert reverse("shop:product_list") in response.url

    def test_inactive_product_returns_404(self, client, inactive_product):
        """Inactive products return 404."""
        url = reverse("shop:product_detail", kwargs={"slug": inactive_product.slug})
        response = client.get(url)
        assert response.status_code == 404

    def test_nonexistent_product_returns_404(self, client):
        """Non-existent products return 404."""
        url = reverse("shop:product_detail", kwargs={"slug": "nonexistent-product"})
        response = client.get(url)
        assert response.status_code == 404

    def test_product_context_data(self, client, shop_product):
        """Product detail provides correct context with product data."""
        mock_price = MagicMock()
        mock_price.id = "price_test123"
        mock_price.unit_amount = 2999
        mock_price.currency = "usd"

        mock_stripe = MagicMock()
        mock_stripe.id = "prod_test123"
        mock_stripe.default_price = mock_price

        with patch.object(
            ShopProduct, "stripe_product", new_callable=PropertyMock, return_value=mock_stripe
        ):
            url = reverse("shop:product_detail", kwargs={"slug": shop_product.slug})
            response = client.get(url)

            assert "product" in response.context
            product = response.context["product"]
            assert product["name"] == shop_product.name
            assert product["slug"] == shop_product.slug
            assert product["stripe_product_id"] == "prod_test123"
            assert product["price_id"] == "price_test123"
            assert product["price"] == 29.99
            assert product["currency"] == "USD"

    def test_product_with_images(self, client, shop_product_with_images):
        """Product detail shows uploaded images."""
        mock_price = MagicMock()
        mock_price.id = "price_test123"
        mock_price.unit_amount = 2999
        mock_price.currency = "usd"

        mock_stripe = MagicMock()
        mock_stripe.id = "prod_test123"
        mock_stripe.default_price = mock_price

        with patch.object(
            ShopProduct, "stripe_product", new_callable=PropertyMock, return_value=mock_stripe
        ):
            url = reverse("shop:product_detail", kwargs={"slug": shop_product_with_images.slug})
            response = client.get(url)

            product = response.context["product"]
            assert "images" in product
            assert len(product["images"]) > 0

    def test_error_message_on_missing_stripe_product(self, client, shop_product):
        """Error message is displayed when Stripe product is missing."""
        with patch.object(
            ShopProduct, "stripe_product", new_callable=PropertyMock, return_value=None
        ):
            url = reverse("shop:product_detail", kwargs={"slug": shop_product.slug})
            response = client.get(url, follow=True)

            # Check that error message appears in messages
            messages = list(response.context["messages"])
            assert len(messages) == 1
            assert "not available" in str(messages[0]).lower()

    def test_error_message_on_missing_default_price(self, client, shop_product):
        """Error message is displayed when default price is missing."""
        mock_stripe = MagicMock()
        mock_stripe.id = "prod_test123"
        mock_stripe.default_price = None

        with patch.object(
            ShopProduct, "stripe_product", new_callable=PropertyMock, return_value=mock_stripe
        ):
            url = reverse("shop:product_detail", kwargs={"slug": shop_product.slug})
            response = client.get(url, follow=True)

            # Check that error message appears in messages
            messages = list(response.context["messages"])
            assert len(messages) == 1
            assert "pricing not available" in str(messages[0]).lower()
