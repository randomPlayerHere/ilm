from __future__ import annotations

from pydantic import BaseModel, field_validator

from app.domains.notifications.repository import VALID_CADENCES, VALID_EVENT_TYPES


class NotificationPreferenceItem(BaseModel):
    event_type: str
    cadence: str
    updated_at: str


class NotificationPreferencesResponse(BaseModel):
    preferences: list[NotificationPreferenceItem]


class NotificationPreferenceUpdateItem(BaseModel):
    event_type: str
    cadence: str

    @field_validator("cadence")
    @classmethod
    def validate_cadence(cls, v: str) -> str:
        if v not in VALID_CADENCES:
            raise ValueError(f"cadence must be one of: {sorted(VALID_CADENCES)}")
        return v

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        if v not in VALID_EVENT_TYPES:
            raise ValueError(f"event_type must be one of: {sorted(VALID_EVENT_TYPES)}")
        return v


class NotificationPreferencesUpdateRequest(BaseModel):
    preferences: list[NotificationPreferenceUpdateItem]
