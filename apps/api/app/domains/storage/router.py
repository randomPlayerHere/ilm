from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.storage import generate_presigned_upload_url
from app.domains.auth.dependencies import ActorContext, require_authenticated_actor

router = APIRouter(prefix="/v1/storage", tags=["storage"])

_SAFE_FILENAME_RE = re.compile(r"^[A-Za-z0-9_.\-]{1,255}$")


class PresignedUrlRequest(BaseModel):
    filename: str


class PresignedUrlResponse(BaseModel):
    url: str
    key: str


@router.post("/presigned-url", response_model=PresignedUrlResponse)
async def create_presigned_url(
    payload: PresignedUrlRequest,
    actor: ActorContext = Depends(require_authenticated_actor),
) -> PresignedUrlResponse:
    if not _SAFE_FILENAME_RE.match(payload.filename):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="filename must be 1-255 characters and contain only letters, digits, underscores, hyphens, or dots",
        )
    result = generate_presigned_upload_url(
        org_id=actor.org_id,
        filename=payload.filename,
    )
    return PresignedUrlResponse(url=result["url"], key=result["key"])
