"""Tests for device token registration endpoint."""
from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.domains.auth.router import reset_auth_state_for_tests
from app.main import app

client = TestClient(app)


def setup_function() -> None:
    reset_auth_state_for_tests()
    app.dependency_overrides.clear()


def _headers(user_id: str, org_id: str, role: str) -> dict[str, str]:
    token, _ = create_access_token(subject=user_id, org_id=org_id, role=role)
    return {"Authorization": f"Bearer {token}"}


class TestDeviceTokenRegistration:
    def test_register_token_returns_201(self) -> None:
        response = client.post(
            "/v1/notifications/device-token",
            json={"token": "device-tok-abc"},
            headers=_headers("usr_teacher_1", "org_demo_1", "teacher"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["token"] == "device-tok-abc"
        assert body["user_id"] == "usr_teacher_1"

    def test_register_token_rejects_unauthenticated(self) -> None:
        response = client.post(
            "/v1/notifications/device-token",
            json={"token": "device-tok-abc"},
        )
        assert response.status_code == 401

    def test_any_role_can_register_token(self) -> None:
        role_map = {
            "teacher": "usr_teacher_1",
            "parent": "usr_parent_1",
            "student": "usr_student_1",
            "admin": "usr_admin_1",
        }
        for role, user_id in role_map.items():
            response = client.post(
                "/v1/notifications/device-token",
                json={"token": f"tok-for-{role}"},
                headers=_headers(user_id, "org_demo_1", role),
            )
            assert response.status_code == 201, f"Failed for role={role}"


class TestDeviceTokenDeregistration:
    def _delete(self, token: str, headers: dict | None = None) -> object:
        return client.request(
            "DELETE",
            "/v1/notifications/device-token",
            json={"token": token},
            headers=headers or {},
        )

    def test_deregister_existing_token_returns_204(self) -> None:
        h = _headers("usr_teacher_1", "org_demo_1", "teacher")
        client.post("/v1/notifications/device-token", json={"token": "tok-to-remove"}, headers=h)
        response = self._delete("tok-to-remove", h)
        assert response.status_code == 204

    def test_deregister_nonexistent_token_returns_404(self) -> None:
        h = _headers("usr_teacher_1", "org_demo_1", "teacher")
        response = self._delete("not-registered", h)
        assert response.status_code == 404

    def test_deregister_rejects_unauthenticated(self) -> None:
        response = self._delete("tok")
        assert response.status_code == 401
