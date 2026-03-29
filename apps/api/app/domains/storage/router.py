from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.storage import generate_presigned_download_url, generate_presigned_upload_url
from app.domains.auth.dependencies import ActorContext, require_authenticated_actor

router = APIRouter(prefix="/v1/storage", tags=["storage"])

_SAFE_FILENAME_RE = re.compile(r"^[A-Za-z0-9_.\-]{1,255}$")
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_.\-]{1,128}$")


class PresignedUrlRequest(BaseModel):
    filename: str
    class_id: str = ""
    student_id: str = ""
    assignment_id: str = ""


class PresignedUrlResponse(BaseModel):
    url: str
    key: str


class PresignedDownloadUrlRequest(BaseModel):
    key: str


class PresignedDownloadUrlResponse(BaseModel):
    url: str


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
    for field_name, value in [
        ("class_id", payload.class_id),
        ("student_id", payload.student_id),
        ("assignment_id", payload.assignment_id),
    ]:
        if value and not _SAFE_ID_RE.match(value):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"{field_name} contains invalid characters",
            )
    result = generate_presigned_upload_url(
        org_id=actor.org_id,
        filename=payload.filename,
        class_id=payload.class_id,
        student_id=payload.student_id,
        assignment_id=payload.assignment_id,
    )
    return PresignedUrlResponse(url=result["url"], key=result["key"])


@router.post("/presigned-download-url", response_model=PresignedDownloadUrlResponse)
async def create_presigned_download_url(
    payload: PresignedDownloadUrlRequest,
    actor: ActorContext = Depends(require_authenticated_actor),
) -> PresignedDownloadUrlResponse:
    expected_prefix = f"orgs/{actor.org_id}/"
    if not payload.key.startswith(expected_prefix):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )
    url = generate_presigned_download_url(payload.key)
    return PresignedDownloadUrlResponse(url=url)
