import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        username="otheruser",
        email="other@example.com",
        password="testpass123",
    )


@pytest.fixture
def mock_stripe_customer():
    """Mock dj-stripe Customer object."""
    customer = MagicMock()
    customer.id = "cus_test123"
    return customer


@pytest.fixture
def user_with_customer(user, mock_stripe_customer):
    """User with a linked Stripe customer."""
    user.customer = mock_stripe_customer
    user.save = MagicMock()  # Don't actually save to DB with mock FK
    return user


@pytest.fixture
def mock_subscription():
    """Mock dj-stripe Subscription object."""
    sub = MagicMock()
    sub.id = "sub_test123"
    sub.status = "active"
    sub.customer = MagicMock()
    sub.customer.id = "cus_test123"
    return sub


@pytest.fixture
def user_with_subscription(user, mock_subscription):
    """User with an active subscription (mocked)."""
    user.subscription = mock_subscription
    # Mock active_subscription property to return the subscription
    with patch.object(type(user), "active_subscription", new_callable=PropertyMock, return_value=mock_subscription):
        yield user


@pytest.fixture
def mock_checkout_session():
    """Mock Stripe checkout.Session object."""
    session = MagicMock()
    session.id = "cs_test_123"
    session.url = "https://checkout.stripe.com/pay/cs_test_123"
    session.client_reference_id = None  # Will be set per test
    session.subscription = "sub_test123"
    return session


@pytest.fixture
def mock_event():
    """Mock dj-stripe Event object for signal testing."""
    event = MagicMock()
    event.id = "evt_test123"
    event.data = {
        "object": {
            "id": "sub_test123",
            "status": "active",
            "customer": "cus_test123",
        }
    }
    return event


@pytest.fixture
def mock_customer_event():
    """Mock dj-stripe Event for customer.created/updated signals."""
    event = MagicMock()
    event.id = "evt_cust123"
    event.data = {
        "object": {
            "id": "cus_test123",
        }
    }
    return event
