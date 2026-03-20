from __future__ import annotations

import asyncio
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.domains.auth.dependencies import ActorContext, require_authenticated_actor

router = APIRouter(prefix="/v1/notifications", tags=["push"])

# In-memory store: user_id → set of device tokens
# Replaced by a DB table in a future story.
_lock = asyncio.Lock()
_device_tokens: dict[str, set[str]] = defaultdict(set)


class DeviceTokenRequest(BaseModel):
    token: str


class DeviceTokenResponse(BaseModel):
    user_id: str
    token: str


@router.post(
    "/device-token",
    response_model=DeviceTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_device_token(
    payload: DeviceTokenRequest,
    actor: ActorContext = Depends(require_authenticated_actor),
) -> DeviceTokenResponse:
    """Register or refresh a device push token for the authenticated user."""
    async with _lock:
        _device_tokens[actor.user_id].add(payload.token)
    return DeviceTokenResponse(user_id=actor.user_id, token=payload.token)


@router.delete("/device-token", status_code=status.HTTP_204_NO_CONTENT)
async def deregister_device_token(
    payload: DeviceTokenRequest,
    actor: ActorContext = Depends(require_authenticated_actor),
) -> None:
    """Remove a device token for the authenticated user (handles rotation/logout)."""
    async with _lock:
        tokens = _device_tokens.get(actor.user_id)
        if not tokens or payload.token not in tokens:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="token not found")
        tokens.discard(payload.token)
