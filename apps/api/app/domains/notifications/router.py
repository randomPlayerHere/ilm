from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.domains.auth.dependencies import ActorContext, require_authenticated_actor
from app.domains.notifications.repository import InMemoryNotificationPreferencesRepository
from app.domains.notifications.schemas import (
    NotificationPreferenceItem,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdateRequest,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])

_prefs_repo = InMemoryNotificationPreferencesRepository()


def _require_parent(actor: ActorContext) -> None:
    """Guard: only parent role may manage notification preferences."""
    if actor.role != "parent":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    actor: ActorContext = Depends(require_authenticated_actor),
) -> NotificationPreferencesResponse:
    _require_parent(actor)
    records = _prefs_repo.get_preferences_for_user(actor.user_id, actor.org_id)
    return NotificationPreferencesResponse(
        preferences=[
            NotificationPreferenceItem(
                event_type=r.event_type,
                cadence=r.cadence,
                updated_at=r.updated_at,
            )
            for r in records
        ]
    )


@router.put("/preferences", response_model=NotificationPreferencesResponse)
async def update_notification_preferences(
    body: NotificationPreferencesUpdateRequest,
    actor: ActorContext = Depends(require_authenticated_actor),
) -> NotificationPreferencesResponse:
    _require_parent(actor)
    now = datetime.now(tz=UTC).isoformat()
    for item in body.preferences:
        _prefs_repo.upsert_preference(
            user_id=actor.user_id,
            org_id=actor.org_id,
            event_type=item.event_type,
            cadence=item.cadence,
            updated_at=now,
        )
    records = _prefs_repo.get_preferences_for_user(actor.user_id, actor.org_id)
    return NotificationPreferencesResponse(
        preferences=[
            NotificationPreferenceItem(
                event_type=r.event_type,
                cadence=r.cadence,
                updated_at=r.updated_at,
            )
            for r in records
        ]
    )
