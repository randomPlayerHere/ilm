"""Tests for POST /v1/storage/presigned-url endpoint and storage abstraction."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.core.storage import generate_presigned_upload_url
from app.domains.auth.router import reset_auth_state_for_tests
from app.main import app

client = TestClient(app)


def setup_function() -> None:
    reset_auth_state_for_tests()
    app.dependency_overrides.clear()


def _teacher_headers() -> dict[str, str]:
    token, _ = create_access_token(subject="usr_teacher_1", org_id="org_demo_1", role="teacher")
    return {"Authorization": f"Bearer {token}"}


class TestPresignedUrlEndpoint:
    def test_returns_url_and_key_for_authenticated_user(self) -> None:
        mock_url = "http://minio:9000/ilm-assignments/orgs/org_demo_1/assignments/uuid/file.jpg?sig=abc"
        with patch("app.core.storage._make_s3_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.generate_presigned_url.return_value = mock_url
            mock_client_fn.return_value = mock_client

            response = client.post(
                "/v1/storage/presigned-url",
                json={"filename": "photo.jpg"},
                headers=_teacher_headers(),
            )

        assert response.status_code == 200
        body = response.json()
        assert body["url"] == mock_url
        assert "orgs/org_demo_1/assignments/" in body["key"]
        assert body["key"].endswith("photo.jpg")

    def test_rejects_unauthenticated_request(self) -> None:
        response = client.post("/v1/storage/presigned-url", json={"filename": "x.jpg"})
        assert response.status_code == 401

    def test_rejects_path_traversal_filename(self) -> None:
        response = client.post(
            "/v1/storage/presigned-url",
            json={"filename": "../../etc/passwd"},
            headers=_teacher_headers(),
        )
        assert response.status_code == 422

    def test_rejects_filename_with_slash(self) -> None:
        response = client.post(
            "/v1/storage/presigned-url",
            json={"filename": "subdir/file.jpg"},
            headers=_teacher_headers(),
        )
        assert response.status_code == 422

    def test_rejects_empty_filename(self) -> None:
        response = client.post(
            "/v1/storage/presigned-url",
            json={"filename": ""},
            headers=_teacher_headers(),
        )
        assert response.status_code == 422


class TestStorageAbstractionUnit:
    def test_key_uses_org_scoped_path(self) -> None:
        with patch("app.core.storage._make_s3_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.generate_presigned_url.return_value = "http://fake-url"
            mock_client_fn.return_value = mock_client

            result = generate_presigned_upload_url(org_id="org-abc", filename="test.pdf")

        assert result["key"].startswith("orgs/org-abc/assignments/")
        assert result["key"].endswith("test.pdf")

    def test_presigned_url_uses_put_method(self) -> None:
        with patch("app.core.storage._make_s3_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.generate_presigned_url.return_value = "http://fake-url"
            mock_client_fn.return_value = mock_client

            generate_presigned_upload_url(org_id="org-abc", filename="test.pdf")

        call_args = mock_client.generate_presigned_url.call_args
        assert call_args[0][0] == "put_object"

    def test_presigned_url_expires_in_900_seconds(self) -> None:
        with patch("app.core.storage._make_s3_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.generate_presigned_url.return_value = "http://fake-url"
            mock_client_fn.return_value = mock_client

            generate_presigned_upload_url(org_id="org-abc", filename="test.pdf")

        call_kwargs = mock_client.generate_presigned_url.call_args[1]
        assert call_kwargs["ExpiresIn"] == 900
