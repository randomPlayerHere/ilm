import asyncio

import httpx

from app.domains.auth.router import reset_auth_state_for_tests
from app.main import app


def setup_function():
    reset_auth_state_for_tests()


def test_login_success_returns_token_and_home_path():
    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            response = await client.post(
                "/auth/login",
                json={
                    "email": "teacher@example.com",
                    "password": "correct-horse-battery-staple",
                },
            )

            assert response.status_code == 200
            body = response.json()
            assert body["token_type"] == "bearer"
            assert body["role"] == "teacher"
            assert body["org_id"] == "org_demo_1"
            assert body["home_path"] == "/(teacher)"
            assert isinstance(body["access_token"], str) and body["access_token"]
            assert body["expires_in"] > 0

    asyncio.run(scenario())


def test_login_invalid_password_and_unknown_user_are_indistinguishable():
    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            bad_password = await client.post(
                "/auth/login",
                json={"email": "teacher@example.com", "password": "bad-password"},
            )
            unknown_user = await client.post(
                "/auth/login",
                json={"email": "nobody@example.com", "password": "bad-password"},
            )

            assert bad_password.status_code == 401
            assert unknown_user.status_code == 401
            assert (
                bad_password.json()
                == unknown_user.json()
                == {"detail": "Invalid credentials"}
            )

    asyncio.run(scenario())


def test_login_inactive_user_is_denied_with_generic_error():
    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            response = await client.post(
                "/auth/login",
                json={
                    "email": "inactive.teacher@example.com",
                    "password": "correct-horse-battery-staple",
                },
            )

            assert response.status_code == 401
            assert response.json() == {"detail": "Invalid credentials"}

    asyncio.run(scenario())


def test_login_rejects_invalid_payload_shape():
    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            response = await client.post(
                "/auth/login",
                json={
                    "email": "not-an-email",
                    "password": "short",
                    "unexpected": "field",
                },
            )

            assert response.status_code == 422

    asyncio.run(scenario())


def test_login_rate_limit_blocks_after_repeated_failures():
    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            for _ in range(5):
                fail = await client.post(
                    "/auth/login",
                    json={"email": "teacher@example.com", "password": "bad-password"},
                )
                assert fail.status_code == 401

            blocked = await client.post(
                "/auth/login",
                json={"email": "teacher@example.com", "password": "bad-password"},
            )
            assert blocked.status_code == 429
            assert blocked.json() == {
                "detail": "Too many login attempts. Try again later."
            }

    asyncio.run(scenario())
