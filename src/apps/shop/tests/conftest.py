import pytest
from unittest.mock import MagicMock
from django.contrib.auth import get_user_model
from apps.shop.models import ShopCategory, ShopProduct, ShopProductImage, Basket

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )


@pytest.fixture
def other_user(db):
    """Create a second test user for ownership tests."""
    return User.objects.create_user(
        username="otheruser",
        email="other@example.com",
        password="testpass123",
    )


@pytest.fixture
def shop_category(db):
    """Create an active shop category."""
    return ShopCategory.objects.create(
        name="Books",
        slug="books",
        description="Children's books",
        sort_order=1,
        is_active=True,
    )


@pytest.fixture
def inactive_category(db):
    """Create an inactive shop category."""
    return ShopCategory.objects.create(
        name="Archived",
        slug="archived",
        description="Archived items",
        sort_order=99,
        is_active=False,
    )


@pytest.fixture
def shop_product(db, shop_category):
    """Create an active shop product."""
    return ShopProduct.objects.create(
        product_id="prod_test123",
        name="Test Book",
        slug="test-book",
        description="A test product",
        category=shop_category,
        is_new=True,
        is_popular=False,
        sort_order=1,
        is_active=True,
    )


@pytest.fixture
def inactive_product(db, shop_category):
    """Create an inactive shop product."""
    return ShopProduct.objects.create(
        product_id="prod_inactive",
        name="Inactive Book",
        slug="inactive-book",
        category=shop_category,
        is_active=False,
    )


@pytest.fixture
def shop_product_with_images(db, shop_product):
    """Add images to the shop product and return it."""
    ShopProductImage.objects.create(
        product=shop_product,
        image="shop/products/2024/01/image1.jpg",
        alt_text="Front cover",
        sort_order=0,
    )
    ShopProductImage.objects.create(
        product=shop_product,
        image="shop/products/2024/01/image2.jpg",
        alt_text="Back cover",
        sort_order=1,
    )
    return shop_product


@pytest.fixture
def mock_stripe_product():
    """Create a mock djstripe.Product with default_price."""
    product = MagicMock()
    product.id = "prod_test123"
    product.name = "Test Book"
    product.default_price = MagicMock()
    product.default_price.id = "price_test123"
    product.default_price.unit_amount = 2999  # $29.99
    product.default_price.currency = "usd"
    return product


@pytest.fixture
def mock_stripe_session():
    """Create a mock djstripe.Session for Order tests."""
    session = MagicMock()
    session.amount_total = 2999
    session.currency = "usd"
    session.payment_intent = MagicMock()
    session.payment_intent.stripe_data = {"status": "succeeded"}
    session.payment_intent.charges = MagicMock()
    session.stripe_data = {"line_items": {"data": [{"id": "li_test"}]}}
    return session


@pytest.fixture
def basket(db, user):
    """Create a basket for the test user."""
    return Basket.objects.create(user=user, checked_out=False)
