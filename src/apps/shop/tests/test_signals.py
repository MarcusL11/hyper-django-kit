import logging
from unittest.mock import MagicMock

import pytest

from apps.shop.signals import handle_failed_payment, handle_refund, handle_successful_payment


class TestHandleSuccessfulPayment:

    def test_logs_payment_intent_id(self, caplog):
        """Logs info message with payment intent ID."""
        mock_event = MagicMock()
        mock_event.data = {"object": {"id": "pi_test123"}}

        with caplog.at_level(logging.INFO, logger="apps.shop.signals"):
            handle_successful_payment(sender=None, event=mock_event)

        assert "pi_test123" in caplog.text
        assert "succeeded" in caplog.text


class TestHandleFailedPayment:

    def test_logs_payment_intent_id(self, caplog):
        """Logs warning message with payment intent ID."""
        mock_event = MagicMock()
        mock_event.data = {"object": {"id": "pi_failed456"}}

        with caplog.at_level(logging.WARNING, logger="apps.shop.signals"):
            handle_failed_payment(sender=None, event=mock_event)

        assert "pi_failed456" in caplog.text
        assert "failed" in caplog.text


class TestHandleRefund:

    def test_logs_charge_id(self, caplog):
        """Logs info message with charge ID."""
        mock_event = MagicMock()
        mock_event.data = {"object": {"id": "ch_refund789"}}

        with caplog.at_level(logging.INFO, logger="apps.shop.signals"):
            handle_refund(sender=None, event=mock_event)

        assert "ch_refund789" in caplog.text
        assert "refunded" in caplog.text
