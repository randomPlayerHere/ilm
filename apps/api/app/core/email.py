from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from app.core.settings import settings

logger = logging.getLogger(__name__)


class EmailProvider(ABC):
    """Provider-agnostic email interface. Swap implementations via EMAIL_PROVIDER config."""

    @abstractmethod
    def send_invitation(self, *, to: str, invitation_token: str, org_name: str) -> None: ...

    @abstractmethod
    def send_password_reset(self, *, to: str, reset_token: str) -> None: ...


class ConsoleEmailProvider(EmailProvider):
    """Local dev provider — logs email content to console instead of sending."""

    def send_invitation(self, *, to: str, invitation_token: str, org_name: str) -> None:
        logger.info(
            "[EMAIL:invitation] to=%s org=%s token=%s",
            to,
            org_name,
            invitation_token,
        )

    def send_password_reset(self, *, to: str, reset_token: str) -> None:
        logger.info("[EMAIL:password_reset] to=%s token=%s", to, reset_token)


class SESEmailProvider(EmailProvider):
    """Future AWS SES provider — swap in via EMAIL_PROVIDER=ses config."""

    def send_invitation(self, *, to: str, invitation_token: str, org_name: str) -> None:
        raise NotImplementedError("SES provider not yet implemented")

    def send_password_reset(self, *, to: str, reset_token: str) -> None:
        raise NotImplementedError("SES provider not yet implemented")


def _build_email_provider() -> EmailProvider:
    provider = settings.email_provider
    if provider == "ses":
        return SESEmailProvider()
    return ConsoleEmailProvider()


email_service: EmailProvider = _build_email_provider()
