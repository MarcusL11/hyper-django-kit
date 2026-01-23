"""
Tests for subscriptions signal handlers.

These tests verify that the signal handlers properly sync Stripe webhook events
with the CustomUser model's subscription and customer foreign keys.
"""

import logging
from unittest.mock import MagicMock, patch

import pytest

from apps.subscriptions.signals import (
    clear_user_subscription,
    link_customer_to_user,
    sync_user_subscription,
)


@pytest.mark.django_db
class TestSyncUserSubscription:
    """Tests for sync_user_subscription signal handler."""

    def test_sets_active_subscription(self):
        """Active subscription is linked to user."""
        mock_event = MagicMock()
        mock_event.id = "evt_test"
        mock_event.data = {"object": {"id": "sub_123", "status": "active"}}

        mock_subscription = MagicMock()
        mock_subscription.id = "sub_123"
        mock_subscription.status = "active"
        mock_subscription.customer = MagicMock()
        mock_subscription.customer.id = "cus_123"

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.subscription_id = None

        with patch("djstripe.models.Subscription.objects.get", return_value=mock_subscription), \
             patch("apps.accounts.models.CustomUser.objects.get", return_value=mock_user):
            sync_user_subscription(sender=None, event=mock_event)

        assert mock_user.subscription == mock_subscription
        mock_user.save.assert_called_once_with(update_fields=["subscription"])

    def test_sets_trialing_subscription(self):
        """Trialing subscription is linked to user."""
        mock_event = MagicMock()
        mock_event.id = "evt_test"
        mock_event.data = {"object": {"id": "sub_123"}}

        mock_subscription = MagicMock()
        mock_subscription.id = "sub_123"
        mock_subscription.status = "trialing"
        mock_subscription.customer = MagicMock()

        mock_user = MagicMock()
        mock_user.subscription_id = None

        with patch("djstripe.models.Subscription.objects.get", return_value=mock_subscription), \
             patch("apps.accounts.models.CustomUser.objects.get", return_value=mock_user):
            sync_user_subscription(sender=None, event=mock_event)

        assert mock_user.subscription == mock_subscription
        mock_user.save.assert_called_once_with(update_fields=["subscription"])

    def test_clears_canceled_subscription(self):
        """Canceled subscription is cleared from user."""
        mock_event = MagicMock()
        mock_event.id = "evt_test"
        mock_event.data = {"object": {"id": "sub_123"}}

        mock_subscription = MagicMock()
        mock_subscription.id = "sub_123"
        mock_subscription.status = "canceled"
        mock_subscription.customer = MagicMock()

        mock_user = MagicMock()
        mock_user.subscription_id = "sub_123"

        with patch("djstripe.models.Subscription.objects.get", return_value=mock_subscription), \
             patch("apps.accounts.models.CustomUser.objects.get", return_value=mock_user):
            sync_user_subscription(sender=None, event=mock_event)

        assert mock_user.subscription is None
        mock_user.save.assert_called_once_with(update_fields=["subscription"])

    def test_clears_incomplete_expired_subscription(self):
        """Incomplete_expired subscription is cleared from user."""
        mock_event = MagicMock()
        mock_event.id = "evt_test"
        mock_event.data = {"object": {"id": "sub_123"}}

        mock_subscription = MagicMock()
        mock_subscription.id = "sub_123"
        mock_subscription.status = "incomplete_expired"
        mock_subscription.customer = MagicMock()

        mock_user = MagicMock()
        mock_user.subscription_id = "sub_123"

        with patch("djstripe.models.Subscription.objects.get", return_value=mock_subscription), \
             patch("apps.accounts.models.CustomUser.objects.get", return_value=mock_user):
            sync_user_subscription(sender=None, event=mock_event)

        assert mock_user.subscription is None
        mock_user.save.assert_called_once_with(update_fields=["subscription"])

    def test_clears_unpaid_subscription(self):
        """Unpaid subscription is cleared from user."""
        mock_event = MagicMock()
        mock_event.id = "evt_test"
        mock_event.data = {"object": {"id": "sub_123"}}

        mock_subscription = MagicMock()
        mock_subscription.id = "sub_123"
        mock_subscription.status = "unpaid"
        mock_subscription.customer = MagicMock()

        mock_user = MagicMock()
        mock_user.subscription_id = "sub_123"

        with patch("djstripe.models.Subscription.objects.get", return_value=mock_subscription), \
             patch("apps.accounts.models.CustomUser.objects.get", return_value=mock_user):
            sync_user_subscription(sender=None, event=mock_event)

        assert mock_user.subscription is None
        mock_user.save.assert_called_once_with(update_fields=["subscription"])

    def test_does_not_clear_if_different_subscription(self):
        """Canceled subscription does not clear if user has different subscription."""
        mock_event = MagicMock()
        mock_event.id = "evt_test"
        mock_event.data = {"object": {"id": "sub_123"}}

        mock_subscription = MagicMock()
        mock_subscription.id = "sub_123"
        mock_subscription.status = "canceled"
        mock_subscription.customer = MagicMock()

        mock_user = MagicMock()
        mock_user.subscription_id = "sub_different"  # Different subscription

        with patch("djstripe.models.Subscription.objects.get", return_value=mock_subscription), \
             patch("apps.accounts.models.CustomUser.objects.get", return_value=mock_user):
            sync_user_subscription(sender=None, event=mock_event)

        # User's subscription should not be modified
        mock_user.save.assert_not_called()

    def test_no_event_data_returns_early(self, caplog):
        """Missing event data logs warning and returns."""
        mock_event = MagicMock()
        mock_event.id = "evt_test"
        mock_event.data = {"object": None}

        with caplog.at_level(logging.WARNING):
            sync_user_subscription(sender=None, event=mock_event)

        assert "has no subscription data" in caplog.text

    def test_no_subscription_id_logs_warning(self, caplog):
        """Missing subscription ID logs warning."""
        mock_event = MagicMock()
        mock_event.id = "evt_test"
        mock_event.data = {"object": {"status": "active"}}  # Has object data but no ID

        with caplog.at_level(logging.WARNING):
            sync_user_subscription(sender=None, event=mock_event)

        assert "has no subscription ID" in caplog.text

    def test_subscription_not_found_logs_warning(self, caplog):
        """Non-existent subscription logs warning."""
        mock_event = MagicMock()
        mock_event.id = "evt_test"
        mock_event.data = {"object": {"id": "sub_missing"}}

        from djstripe.models import Subscription

        with patch("djstripe.models.Subscription.objects.get", side_effect=Subscription.DoesNotExist), \
             caplog.at_level(logging.WARNING):
            sync_user_subscription(sender=None, event=mock_event)

        assert "not found in database" in caplog.text

    def test_no_customer_logs_warning(self, caplog):
        """Subscription without customer logs warning."""
        mock_event = MagicMock()
        mock_event.id = "evt_test"
        mock_event.data = {"object": {"id": "sub_123"}}

        mock_subscription = MagicMock()
        mock_subscription.id = "sub_123"
        mock_subscription.customer = None

        with patch("djstripe.models.Subscription.objects.get", return_value=mock_subscription), \
             caplog.at_level(logging.WARNING):
            sync_user_subscription(sender=None, event=mock_event)

        assert "has no customer" in caplog.text

    def test_user_not_found_logs_info(self, caplog):
        """No user for customer logs info."""
        mock_event = MagicMock()
        mock_event.id = "evt_test"
        mock_event.data = {"object": {"id": "sub_123"}}

        mock_subscription = MagicMock()
        mock_subscription.id = "sub_123"
        mock_subscription.customer = MagicMock()
        mock_subscription.customer.id = "cus_123"

        from apps.accounts.models import CustomUser

        with patch("djstripe.models.Subscription.objects.get", return_value=mock_subscription), \
             patch("apps.accounts.models.CustomUser.objects.get", side_effect=CustomUser.DoesNotExist), \
             caplog.at_level(logging.INFO):
            sync_user_subscription(sender=None, event=mock_event)

        assert "No user linked to customer" in caplog.text

    def test_multiple_users_logs_error(self, caplog):
        """Multiple users for customer logs error."""
        mock_event = MagicMock()
        mock_event.id = "evt_test"
        mock_event.data = {"object": {"id": "sub_123"}}

        mock_subscription = MagicMock()
        mock_subscription.id = "sub_123"
        mock_subscription.customer = MagicMock()
        mock_subscription.customer.id = "cus_123"

        from apps.accounts.models import CustomUser

        with patch("djstripe.models.Subscription.objects.get", return_value=mock_subscription), \
             patch("apps.accounts.models.CustomUser.objects.get",
                   side_effect=CustomUser.MultipleObjectsReturned), \
             caplog.at_level(logging.ERROR):
            sync_user_subscription(sender=None, event=mock_event)

        assert "Multiple users found for customer" in caplog.text

    def test_unexpected_exception_logged(self, caplog):
        """Unexpected exceptions are logged but don't break webhook processing."""
        mock_event = MagicMock()
        mock_event.id = "evt_test"
        mock_event.data = {"object": {"id": "sub_123"}}

        with patch("djstripe.models.Subscription.objects.get",
                   side_effect=Exception("Unexpected error")), \
             caplog.at_level(logging.ERROR):
            sync_user_subscription(sender=None, event=mock_event)

        assert "Error syncing user subscription" in caplog.text


@pytest.mark.django_db
class TestClearUserSubscription:
    """Tests for clear_user_subscription signal handler."""

    def test_clears_subscription_from_user(self):
        """Deleted subscription is cleared from user."""
        mock_event = MagicMock()
        mock_event.id = "evt_test"
        mock_event.data = {"object": {"id": "sub_123"}}

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.subscription_id = "sub_123"

        from apps.accounts.models import CustomUser

        with patch("apps.accounts.models.CustomUser.objects.get", return_value=mock_user):
            clear_user_subscription(sender=None, event=mock_event)

        assert mock_user.subscription is None
        mock_user.save.assert_called_once_with(update_fields=["subscription"])

    def test_no_event_data_returns_early(self):
        """Missing event data returns without error."""
        mock_event = MagicMock()
        mock_event.id = "evt_test"
        mock_event.data = {"object": None}

        # Should not raise any exception
        clear_user_subscription(sender=None, event=mock_event)

    def test_no_subscription_id_returns_early(self):
        """Missing subscription ID returns without error."""
        mock_event = MagicMock()
        mock_event.id = "evt_test"
        mock_event.data = {"object": {}}

        # Should not raise any exception
        clear_user_subscription(sender=None, event=mock_event)

    def test_user_not_found_logs_info(self, caplog):
        """No user with subscription logs info."""
        mock_event = MagicMock()
        mock_event.id = "evt_test"
        mock_event.data = {"object": {"id": "sub_orphan"}}

        from apps.accounts.models import CustomUser

        with patch("apps.accounts.models.CustomUser.objects.get", side_effect=CustomUser.DoesNotExist), \
             caplog.at_level(logging.INFO):
            clear_user_subscription(sender=None, event=mock_event)

        assert "No user found with subscription" in caplog.text

    def test_multiple_users_logs_error(self, caplog):
        """Multiple users with subscription logs error."""
        mock_event = MagicMock()
        mock_event.id = "evt_test"
        mock_event.data = {"object": {"id": "sub_123"}}

        from apps.accounts.models import CustomUser

        with patch("apps.accounts.models.CustomUser.objects.get",
                   side_effect=CustomUser.MultipleObjectsReturned), \
             caplog.at_level(logging.ERROR):
            clear_user_subscription(sender=None, event=mock_event)

        assert "Multiple users found with subscription" in caplog.text

    def test_unexpected_exception_logged(self, caplog):
        """Unexpected exceptions are logged but don't break webhook processing."""
        mock_event = MagicMock()
        mock_event.id = "evt_test"
        mock_event.data = {"object": {"id": "sub_123"}}

        with patch("apps.accounts.models.CustomUser.objects.get",
                   side_effect=Exception("Unexpected error")), \
             caplog.at_level(logging.ERROR):
            clear_user_subscription(sender=None, event=mock_event)

        assert "Error clearing user subscription" in caplog.text


@pytest.mark.django_db
class TestLinkCustomerToUser:
    """Tests for link_customer_to_user signal handler."""

    def test_links_customer_to_user(self):
        """Customer is linked to user when not already linked."""
        mock_event = MagicMock()
        mock_event.id = "evt_cust"
        mock_event.data = {"object": {"id": "cus_123"}}

        mock_customer = MagicMock()
        mock_customer.id = "cus_123"
        mock_customer.subscriber = MagicMock()
        mock_customer.subscriber.id = 1

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.customer_id = None  # Not yet linked

        from djstripe.models import Customer

        with patch("djstripe.models.Customer.objects.get", return_value=mock_customer), \
             patch("apps.accounts.models.CustomUser.objects.get", return_value=mock_user):
            link_customer_to_user(sender=None, event=mock_event)

        assert mock_user.customer == mock_customer
        mock_user.save.assert_called_once_with(update_fields=["customer"])

    def test_already_linked_does_not_save(self):
        """Already linked customer does not trigger save."""
        mock_event = MagicMock()
        mock_event.id = "evt_cust"
        mock_event.data = {"object": {"id": "cus_123"}}

        mock_customer = MagicMock()
        mock_customer.id = "cus_123"
        mock_customer.subscriber = MagicMock()
        mock_customer.subscriber.id = 1

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.customer_id = "cus_123"  # Already linked

        from djstripe.models import Customer

        with patch("djstripe.models.Customer.objects.get", return_value=mock_customer), \
             patch("apps.accounts.models.CustomUser.objects.get", return_value=mock_user):
            link_customer_to_user(sender=None, event=mock_event)

        mock_user.save.assert_not_called()

    def test_no_event_data_returns_early(self):
        """Missing event data returns without error."""
        mock_event = MagicMock()
        mock_event.id = "evt_cust"
        mock_event.data = {"object": None}

        # Should not raise any exception
        link_customer_to_user(sender=None, event=mock_event)

    def test_no_customer_id_returns_early(self):
        """Missing customer ID returns without error."""
        mock_event = MagicMock()
        mock_event.id = "evt_cust"
        mock_event.data = {"object": {}}

        # Should not raise any exception
        link_customer_to_user(sender=None, event=mock_event)

    def test_customer_not_found_logs_warning(self, caplog):
        """Non-existent customer logs warning."""
        mock_event = MagicMock()
        mock_event.id = "evt_cust"
        mock_event.data = {"object": {"id": "cus_missing"}}

        from djstripe.models import Customer

        with patch("djstripe.models.Customer.objects.get", side_effect=Customer.DoesNotExist), \
             caplog.at_level(logging.WARNING):
            link_customer_to_user(sender=None, event=mock_event)

        assert "not found in database" in caplog.text

    def test_no_subscriber_logs_info(self, caplog):
        """Customer without subscriber logs info."""
        mock_event = MagicMock()
        mock_event.id = "evt_cust"
        mock_event.data = {"object": {"id": "cus_123"}}

        mock_customer = MagicMock()
        mock_customer.id = "cus_123"
        mock_customer.subscriber = None

        from djstripe.models import Customer

        with patch("djstripe.models.Customer.objects.get", return_value=mock_customer), \
             caplog.at_level(logging.INFO):
            link_customer_to_user(sender=None, event=mock_event)

        assert "has no subscriber linked yet" in caplog.text

    def test_user_not_found_logs_warning(self, caplog):
        """User not found logs warning."""
        mock_event = MagicMock()
        mock_event.id = "evt_cust"
        mock_event.data = {"object": {"id": "cus_123"}}

        mock_customer = MagicMock()
        mock_customer.id = "cus_123"
        mock_customer.subscriber = MagicMock()
        mock_customer.subscriber.id = 1

        from djstripe.models import Customer
        from apps.accounts.models import CustomUser

        with patch("djstripe.models.Customer.objects.get", return_value=mock_customer), \
             patch("apps.accounts.models.CustomUser.objects.get", side_effect=CustomUser.DoesNotExist), \
             caplog.at_level(logging.WARNING):
            link_customer_to_user(sender=None, event=mock_event)

        assert "User 1 not found" in caplog.text

    def test_unexpected_exception_logged(self, caplog):
        """Unexpected exceptions are logged but don't break webhook processing."""
        mock_event = MagicMock()
        mock_event.id = "evt_cust"
        mock_event.data = {"object": {"id": "cus_123"}}

        from djstripe.models import Customer

        with patch("djstripe.models.Customer.objects.get", side_effect=Exception("Unexpected error")), \
             caplog.at_level(logging.ERROR):
            link_customer_to_user(sender=None, event=mock_event)

        assert "Error linking customer to user" in caplog.text
