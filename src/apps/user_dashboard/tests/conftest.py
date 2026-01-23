import uuid
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123"
    )


@pytest.fixture
def other_user(db):
    """Create a second user for permission tests."""
    return User.objects.create_user(
        username="otheruser",
        email="other@example.com",
        password="testpass123"
    )


@pytest.fixture
def mock_invoice():
    """Create a mock Stripe invoice."""
    invoice = MagicMock()
    invoice.id = "in_test123"
    invoice.status = "paid"
    invoice.amount_paid = 2999
    invoice.currency = "usd"
    invoice.created = 1234567890
    return invoice


@pytest.fixture
def mock_active_subscription(mock_invoice):
    """Create a mock active Stripe subscription."""
    subscription = MagicMock()
    subscription.product.name = "Pro Plan"
    subscription.product.id = "prod_sub123"
    subscription.status = "active"
    return subscription


@pytest.fixture
def mock_customer(mock_invoice):
    """Create a mock Stripe customer with invoices."""
    customer = MagicMock()
    customer.id = "cus_test123"

    # Create two mock invoices
    mock_invoice1 = MagicMock()
    mock_invoice1.id = "in_test001"
    mock_invoice1.status = "paid"
    mock_invoice1.amount_paid = 2999
    mock_invoice1.currency = "usd"
    mock_invoice1.created = 1234567890

    mock_invoice2 = MagicMock()
    mock_invoice2.id = "in_test002"
    mock_invoice2.status = "paid"
    mock_invoice2.amount_paid = 2999
    mock_invoice2.currency = "usd"
    mock_invoice2.created = 1234567800

    # Setup the invoice chain
    invoices_mock = MagicMock()
    invoices_all_mock = MagicMock()
    order_by_mock = MagicMock()

    order_by_mock.__getitem__ = MagicMock(return_value=[mock_invoice1, mock_invoice2])
    invoices_all_mock.order_by.return_value = order_by_mock
    invoices_mock.all.return_value = invoices_all_mock
    customer.invoices = invoices_mock

    return customer


@pytest.fixture
def user_with_subscription(user, mock_active_subscription):
    """Create a user with an active subscription."""
    with patch.object(
        type(user),
        "active_subscription",
        new_callable=PropertyMock,
        return_value=mock_active_subscription
    ):
        yield user


@pytest.fixture
def user_with_customer(user, mock_customer):
    """Create a user with a Stripe customer."""
    user.customer = mock_customer
    with patch.object(
        type(user),
        "active_subscription",
        new_callable=PropertyMock,
        return_value=None
    ):
        yield user


@pytest.fixture
def mock_order(user):
    """Create a mock order object."""
    order = MagicMock()
    order.id = uuid.uuid4()
    order.user = user
    order.created_at = "2024-01-15T10:00:00Z"

    # Mock session with payment intent
    session = MagicMock()
    session.payment_intent = MagicMock()
    session.payment_intent.id = "pi_test123"
    session.payment_intent.status = "succeeded"
    order.session = session

    # Mock basket with items
    basket = MagicMock()
    basket_item = MagicMock()
    basket_item.product.name = "Test Product"
    basket_item.quantity = 1
    basket_item.price = 2999
    basket.items.all.return_value = [basket_item]
    order.basket = basket

    return order


@pytest.fixture
def email_address(db, user):
    """Create a primary verified email address for the user."""
    return EmailAddress.objects.create(
        user=user,
        email="test@example.com",
        verified=True,
        primary=True
    )


@pytest.fixture
def secondary_email(db, user):
    """Create a secondary unverified email address for the user."""
    return EmailAddress.objects.create(
        user=user,
        email="secondary@example.com",
        verified=False,
        primary=False
    )
