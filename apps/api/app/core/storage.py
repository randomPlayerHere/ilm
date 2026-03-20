from __future__ import annotations

import uuid

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


def generate_presigned_upload_url(
    org_id: str,
    filename: str,
) -> dict[str, str]:
    """Generate a time-limited pre-signed PUT URL for uploading an assignment file.

    The object key is org-scoped and server-determined — never trusted from the client.
    Returns {"url": "...", "key": "orgs/{org_id}/assignments/{uuid}/{filename}"}.
    """
    key = f"orgs/{org_id}/assignments/{uuid.uuid4()}/{filename}"
    client = _make_s3_client()
    url = client.generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.s3_bucket, "Key": key},
        ExpiresIn=_PRESIGNED_URL_EXPIRY_SECONDS,
    )
    return {"url": url, "key": key}
