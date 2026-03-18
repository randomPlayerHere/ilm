from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

VALID_CADENCES: frozenset[str] = frozenset({"instant", "daily", "weekly", "off"})
VALID_EVENT_TYPES: frozenset[str] = frozenset(
    {"grade_approved", "recommendation_confirmed", "topic_insight_new"}
)


@dataclass(frozen=True)
class NotificationPreferenceRecord:
    user_id: str
    org_id: str
    event_type: str  # one of VALID_EVENT_TYPES
    cadence: str  # one of VALID_CADENCES
    updated_at: str  # ISO 8601 UTC


class InMemoryNotificationPreferencesRepository:
    # Key: (user_id, org_id, event_type) → record
    _preferences: ClassVar[dict[tuple[str, str, str], NotificationPreferenceRecord]] = {}

    def get_preferences_for_user(
        self, user_id: str, org_id: str
    ) -> list[NotificationPreferenceRecord]:
        """Return all preferences for user+org, sorted by event_type for stable output."""
        return sorted(
            [
                p
                for p in self.__class__._preferences.values()
                if p.user_id == user_id and p.org_id == org_id
            ],
            key=lambda p: p.event_type,
        )

    def upsert_preference(
        self,
        user_id: str,
        org_id: str,
        event_type: str,
        cadence: str,
        updated_at: str,
    ) -> NotificationPreferenceRecord:
        """Create or replace a preference record. Returns the new record."""
        record = NotificationPreferenceRecord(
            user_id=user_id,
            org_id=org_id,
            event_type=event_type,
            cadence=cadence,
            updated_at=updated_at,
        )
        self.__class__._preferences[(user_id, org_id, event_type)] = record
        return record


def reset_notifications_state_for_tests() -> None:
    InMemoryNotificationPreferencesRepository._preferences.clear()
