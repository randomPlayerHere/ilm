from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from app.core.settings import settings

logger = logging.getLogger(__name__)


class NotificationProvider(ABC):
    """Provider-agnostic push notification interface.

    Swap implementations via NOTIFICATION_PROVIDER config.
    Local dev → ConsoleNotificationProvider (logs to console).
    Future cloud → FcmApnsNotificationProvider.
    """

    @abstractmethod
    def send(self, *, device_token: str, title: str, body: str, data: dict | None = None) -> None: ...


class ConsoleNotificationProvider(NotificationProvider):
    """Local dev provider — logs notification payloads to console."""

    def send(self, *, device_token: str, title: str, body: str, data: dict | None = None) -> None:
        logger.info(
            "[PUSH:notification] token=%s title=%r body=%r data=%s",
            device_token,
            title,
            body,
            data,
        )


class FcmApnsNotificationProvider(NotificationProvider):
    """Future FCM/APNs provider — swap in via NOTIFICATION_PROVIDER=fcm_apns."""

    def send(self, *, device_token: str, title: str, body: str, data: dict | None = None) -> None:
        raise NotImplementedError("FCM/APNs provider not yet implemented")


def _build_notification_provider() -> NotificationProvider:
    provider = settings.notification_provider
    if provider == "fcm_apns":
        return FcmApnsNotificationProvider()
    return ConsoleNotificationProvider()


notification_service: NotificationProvider = _build_notification_provider()
