import pytest
from unittest.mock import patch, MagicMock
from apps.shop.models import ShopCategory, ShopProduct, Basket, BasketItem, Order


@pytest.mark.django_db
class TestShopCategory:

    def test_str(self, shop_category):
        assert str(shop_category) == "Books"

    def test_ordering(self, db):
        cat_b = ShopCategory.objects.create(name="Zulu", slug="zulu", sort_order=2)
        cat_a = ShopCategory.objects.create(name="Alpha", slug="alpha", sort_order=1)
        cat_c = ShopCategory.objects.create(name="Beta", slug="beta", sort_order=1)
        results = list(ShopCategory.objects.all())
        assert results == [cat_a, cat_c, cat_b]


@pytest.mark.django_db
class TestShopProduct:

    def test_str(self, shop_product):
        assert str(shop_product) == "Test Book (prod_test123)"

    def test_stripe_product_found(self, shop_product):
        mock_product = MagicMock()
        with patch("djstripe.models.Product.objects.get", return_value=mock_product):
            result = shop_product.stripe_product
            assert result == mock_product

    def test_stripe_product_not_found(self, shop_product):
        from djstripe.models import Product as StripeProduct
        with patch("djstripe.models.Product.objects.get", side_effect=StripeProduct.DoesNotExist):
            result = shop_product.stripe_product
            assert result is None

    def test_primary_image(self, shop_product_with_images):
        image = shop_product_with_images.primary_image
        assert image is not None
        assert image.sort_order == 0
        assert image.alt_text == "Front cover"

    def test_primary_image_none_when_no_images(self, shop_product):
        assert shop_product.primary_image is None

    def test_all_images_ordered(self, shop_product_with_images):
        images = list(shop_product_with_images.all_images)
        assert len(images) == 2
        assert images[0].sort_order == 0
        assert images[1].sort_order == 1


@pytest.mark.django_db
class TestBasket:

    def test_is_empty_true(self, basket):
        assert basket.is_empty is True

    def test_total_items_zero_when_empty(self, basket):
        assert basket.total_items == 0

    def test_str(self, basket):
        assert "test@example.com" in str(basket)


@pytest.mark.django_db
class TestBasketItem:

    def test_line_total(self):
        item = MagicMock(spec=BasketItem)
        item.product = MagicMock()
        item.product.default_price = MagicMock()
        item.product.default_price.unit_amount = 2999
        item.quantity = 2
        result = BasketItem.line_total.fget(item)
        assert result == 5998

    def test_line_total_no_price(self):
        item = MagicMock(spec=BasketItem)
        item.product = MagicMock()
        item.product.default_price = None
        item.quantity = 1
        result = BasketItem.line_total.fget(item)
        assert result == 0

    def test_line_total_dollars(self):
        item = MagicMock(spec=BasketItem)
        # line_total_dollars calls self.line_total / 100
        # We must set line_total directly since it's also a property
        item.line_total = 2999
        result = BasketItem.line_total_dollars.fget(item)
        assert result == 29.99


@pytest.mark.django_db
class TestOrder:

    def test_status_succeeded(self, user, mock_stripe_session):
        order = MagicMock(spec=Order)
        order.session = mock_stripe_session
        result = Order.status.fget(order)
        assert result == "paid"

    def test_status_unknown_no_session(self):
        order = MagicMock(spec=Order)
        order.session = None
        result = Order.status.fget(order)
        assert result == "unknown"

    def test_status_unknown_no_payment_intent(self, mock_stripe_session):
        mock_stripe_session.payment_intent = None
        order = MagicMock(spec=Order)
        order.session = mock_stripe_session
        result = Order.status.fget(order)
        assert result == "unknown"

    def test_amount_dollars(self, mock_stripe_session):
        order = MagicMock(spec=Order)
        # amount_dollars calls self.amount / 100
        # We must set amount directly since it's also a property
        order.amount = 2999
        result = Order.amount_dollars.fget(order)
        assert result == 29.99
