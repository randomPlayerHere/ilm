"""Tests for email service abstraction."""
from __future__ import annotations

import logging

import pytest

from app.core.email import ConsoleEmailProvider, SESEmailProvider


class TestConsoleEmailProvider:
    def test_send_invitation_logs_to_console(self, caplog: pytest.LogCaptureFixture) -> None:
        provider = ConsoleEmailProvider()
        with caplog.at_level(logging.INFO, logger="app.core.email"):
            provider.send_invitation(
                to="user@example.com",
                invitation_token="tok-abc",
                org_name="Springfield Elementary",
            )
        assert any("invitation" in record.message for record in caplog.records)
        assert any("user@example.com" in record.message for record in caplog.records)

    def test_send_password_reset_logs_to_console(self, caplog: pytest.LogCaptureFixture) -> None:
        provider = ConsoleEmailProvider()
        with caplog.at_level(logging.INFO, logger="app.core.email"):
            provider.send_password_reset(to="user@example.com", reset_token="reset-xyz")
        assert any("password_reset" in record.message for record in caplog.records)


class TestSESEmailProviderIsStub:
    def test_send_invitation_raises_not_implemented(self) -> None:
        provider = SESEmailProvider()
        with pytest.raises(NotImplementedError):
            provider.send_invitation(to="x@y.com", invitation_token="tok", org_name="org")

    def test_send_password_reset_raises_not_implemented(self) -> None:
        provider = SESEmailProvider()
        with pytest.raises(NotImplementedError):
            provider.send_password_reset(to="x@y.com", reset_token="tok")
