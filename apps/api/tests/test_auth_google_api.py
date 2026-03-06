from __future__ import annotations

import asyncio

import httpx

from app.domains.auth.google_oidc import GoogleClaims, GoogleTokenVerifier
from app.domains.auth.router import (
    get_google_token_verifier,
    reset_auth_state_for_tests,
)
from app.main import app


class StubVerifier(GoogleTokenVerifier):
    def __init__(self, token_to_claims: dict[str, GoogleClaims], fail_tokens: set[str] | None = None) -> None:
        self._token_to_claims = token_to_claims
        self._fail_tokens = fail_tokens or set()

    def verify_id_token(self, id_token: str) -> GoogleClaims:
        if id_token in self._fail_tokens or id_token not in self._token_to_claims:
            raise ValueError("invalid token")
        return self._token_to_claims[id_token]


def setup_function():
    reset_auth_state_for_tests()
    app.dependency_overrides.clear()


def test_google_login_success_returns_token_and_home_path():
    verifier = StubVerifier(
        {
            "good-token-value-with-32-characters-abc": GoogleClaims(
                sub="google-sub-teacher-1",
                email="teacher@example.com",
                email_verified=True,
                aud="test-google-client-id",
                iss="https://accounts.google.com",
                exp=4_000_000_000,
            )
        }
    )
    async def override_verifier():
        return verifier

    app.dependency_overrides[get_google_token_verifier] = override_verifier

    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/auth/google",
                json={"id_token": "good-token-value-with-32-characters-abc"},
            )

            assert response.status_code == 200
            body = response.json()
            assert body["token_type"] == "bearer"
            assert body["role"] == "teacher"
            assert body["org_id"] == "org_demo_1"
            assert body["home_path"] == "/teacher"
            assert isinstance(body["access_token"], str) and body["access_token"]

    asyncio.run(scenario())


def test_google_login_without_authorized_membership_returns_contact_admin_message():
    verifier = StubVerifier(
        {
            "no-membership-token-value-32-plus-abc": GoogleClaims(
                sub="google-sub-unknown",
                email="not-member@example.com",
                email_verified=True,
                aud="test-google-client-id",
                iss="https://accounts.google.com",
                exp=4_000_000_000,
            )
        }
    )
    async def override_verifier():
        return verifier

    app.dependency_overrides[get_google_token_verifier] = override_verifier

    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/auth/google",
                json={"id_token": "no-membership-token-value-32-plus-abc"},
            )

            assert response.status_code == 403
            assert response.json() == {
                "detail": "Access requires an authorized organization membership. Please contact your administrator."
            }

    asyncio.run(scenario())


def test_google_login_invalid_token_is_generic_failure():
    verifier = StubVerifier(token_to_claims={}, fail_tokens={"bad-token-value-with-32-characters-abc"})
    async def override_verifier():
        return verifier

    app.dependency_overrides[get_google_token_verifier] = override_verifier

    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/auth/google",
                json={"id_token": "bad-token-value-with-32-characters-abc"},
            )

            assert response.status_code == 401
            assert response.json() == {"detail": "Google authentication failed"}

    asyncio.run(scenario())


def test_google_login_invalid_payload_is_rejected():
    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post("/auth/google", json={"id_token": "short"})

            assert response.status_code == 422

    asyncio.run(scenario())


def test_google_login_inactive_user_is_generic_failure():
    verifier = StubVerifier(
        {
            "inactive-user-token-value-32-plus-ab": GoogleClaims(
                sub="google-sub-inactive",
                email="inactive.teacher@example.com",
                email_verified=True,
                aud="test-google-client-id",
                iss="https://accounts.google.com",
                exp=4_000_000_000,
            )
        }
    )

    async def override_verifier():
        return verifier

    app.dependency_overrides[get_google_token_verifier] = override_verifier

    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/auth/google",
                json={"id_token": "inactive-user-token-value-32-plus-ab"},
            )

            assert response.status_code == 401
            assert response.json() == {"detail": "Google authentication failed"}

    asyncio.run(scenario())


def test_google_login_invalid_token_rotation_is_rate_limited():
    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            for idx in range(5):
                response = await client.post(
                    "/auth/google",
                    json={"id_token": f"rotating-invalid-token-value-32-{idx:02d}"},
                )
                assert response.status_code in (401, 422)

            blocked = await client.post(
                "/auth/google",
                json={"id_token": "rotating-invalid-token-value-32-99"},
            )
            assert blocked.status_code == 429
            assert blocked.json() == {"detail": "Too many login attempts. Try again later."}

    asyncio.run(scenario())
