from __future__ import annotations

import uuid
from urllib.parse import urlparse, urlunparse

import boto3
from botocore.config import Config

from app.core.settings import settings

_PRESIGNED_URL_EXPIRY_SECONDS = 900  # 15 minutes


def _make_s3_client() -> boto3.client:
    """Build a boto3 S3 client.

    When S3_ENDPOINT_URL is set (local MinIO), path-style addressing and
    explicit endpoint are used. When empty or None, real AWS S3 is used.
    """
    endpoint_url = settings.s3_endpoint_url or None
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name="us-east-1",
        config=Config(
            s3={"addressing_style": "path"},
            signature_version="s3v4",
        ),
    )


def _rewrite_to_public_url(url: str) -> str:
    """Replace the host in a presigned URL with S3_PUBLIC_URL if configured.

    Needed when MinIO runs in Docker (minio:9000) but clients are on the LAN —
    they can't resolve Docker-internal hostnames.
    """
    if not settings.s3_public_url:
        return url
    public = urlparse(settings.s3_public_url)
    parsed = urlparse(url)
    rewritten = parsed._replace(scheme=public.scheme, netloc=public.netloc)
    return urlunparse(rewritten)


def generate_presigned_upload_url(
    org_id: str,
    filename: str,
    *,
    class_id: str = "",
    student_id: str = "",
    assignment_id: str = "",
) -> dict[str, str]:
    """Generate a time-limited pre-signed PUT URL for uploading an assignment file.

    The object key is org-scoped and server-determined — never trusted from the client.

    When class_id, student_id, and assignment_id are all provided, the key uses
    the scoped path: orgs/{org_id}/{class_id}/{student_id}/{assignment_id}/{uuid}.jpg
    Otherwise falls back to the legacy path:
    orgs/{org_id}/assignments/{uuid}/{filename}
    """
    if class_id and student_id and assignment_id:
        key = f"orgs/{org_id}/{class_id}/{student_id}/{assignment_id}/{uuid.uuid4()}.jpg"
    else:
        key = f"orgs/{org_id}/assignments/{uuid.uuid4()}/{filename}"

    client = _make_s3_client()
    url = client.generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.s3_bucket, "Key": key},
        ExpiresIn=_PRESIGNED_URL_EXPIRY_SECONDS,
    )
    return {"url": _rewrite_to_public_url(url), "key": key}


def generate_presigned_download_url(storage_key: str) -> str:
    """Generate a time-limited pre-signed GET URL for downloading a stored artifact.

    Returns the signed URL string. Caller is responsible for org-scope validation
    before calling this function.
    """
    client = _make_s3_client()
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket, "Key": storage_key},
        ExpiresIn=_PRESIGNED_URL_EXPIRY_SECONDS,
    )
    return _rewrite_to_public_url(url)
