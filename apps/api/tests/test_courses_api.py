from __future__ import annotations

import asyncio

import httpx

from app.core.security import create_access_token
from app.domains.auth.router import reset_auth_state_for_tests
from app.domains.courses.router import reset_courses_state_for_tests
from app.main import app


def _teacher_headers() -> dict[str, str]:
    token, _ = create_access_token(subject="usr_teacher_1", org_id="org_demo_1", role="teacher")
    return {"Authorization": f"Bearer {token}"}


def setup_function() -> None:
    reset_auth_state_for_tests()
    reset_courses_state_for_tests()
    app.dependency_overrides.clear()


def test_generate_draft_teacher_success_and_retrieve() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            created = await client.post(
                "/courses/drafts/generate",
                headers=_teacher_headers(),
                json={
                    "class_id": "cls_demo_math_1",
                    "unit_title": "Multiplication Unit",
                    "prompt": "Generate a math lesson for grade 6",
                },
            )
            assert created.status_code == 201
            body = created.json()
            assert body["status"] == "draft"
            draft_id = body["draft_id"]

            fetched = await client.get(
                f"/courses/drafts/{draft_id}",
                headers=_teacher_headers(),
            )
            assert fetched.status_code == 200
            assert fetched.json()["draft_id"] == draft_id

    asyncio.run(scenario())


def test_generate_draft_rejects_unauthorized_or_invalid_context() -> None:
    parent_token, _ = create_access_token(subject="usr_teacher_1", org_id="org_demo_1", role="parent")

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            unauth = await client.post(
                "/courses/drafts/generate",
                json={
                    "class_id": "cls_demo_math_1",
                    "unit_title": "Unit",
                    "prompt": "Generate",
                },
            )
            assert unauth.status_code == 401

            non_teacher = await client.post(
                "/courses/drafts/generate",
                headers={"Authorization": f"Bearer {parent_token}"},
                json={
                    "class_id": "cls_demo_math_1",
                    "unit_title": "Unit",
                    "prompt": "Generate",
                },
            )
            assert non_teacher.status_code == 403

            invalid_class = await client.post(
                "/courses/drafts/generate",
                headers=_teacher_headers(),
                json={
                    "class_id": "cls_missing",
                    "unit_title": "Unit",
                    "prompt": "Generate",
                },
            )
            assert invalid_class.status_code == 403

            cross_tenant = await client.post(
                "/courses/drafts/generate",
                headers=_teacher_headers(),
                json={
                    "class_id": "cls_other_org_1",
                    "unit_title": "Unit",
                    "prompt": "Generate",
                },
            )
            assert cross_tenant.status_code == 403

    asyncio.run(scenario())


def test_read_endpoints_deny_non_teacher_roles() -> None:
    parent_token, _ = create_access_token(subject="usr_teacher_1", org_id="org_demo_1", role="parent")

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            created = await client.post(
                "/courses/drafts/generate",
                headers=_teacher_headers(),
                json={
                    "class_id": "cls_demo_math_1",
                    "unit_title": "Unit",
                    "prompt": "Generate lesson",
                },
            )
            assert created.status_code == 201
            draft_id = created.json()["draft_id"]

            forbidden_list = await client.get(
                "/courses/drafts",
                headers={"Authorization": f"Bearer {parent_token}"},
            )
            assert forbidden_list.status_code == 403

            forbidden_get = await client.get(
                f"/courses/drafts/{draft_id}",
                headers={"Authorization": f"Bearer {parent_token}"},
            )
            assert forbidden_get.status_code == 403

    asyncio.run(scenario())


def test_read_endpoints_require_authentication() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            created = await client.post(
                "/courses/drafts/generate",
                headers=_teacher_headers(),
                json={
                    "class_id": "cls_demo_math_1",
                    "unit_title": "Unit",
                    "prompt": "Generate lesson",
                },
            )
            assert created.status_code == 201
            draft_id = created.json()["draft_id"]

            unauth_list = await client.get("/courses/drafts")
            assert unauth_list.status_code == 401

            unauth_get = await client.get(f"/courses/drafts/{draft_id}")
            assert unauth_get.status_code == 401

    asyncio.run(scenario())


def test_generate_draft_provider_failure_returns_retryable_error_and_no_partial_publish() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            failed = await client.post(
                "/courses/drafts/generate",
                headers=_teacher_headers(),
                json={
                    "class_id": "cls_demo_math_1",
                    "unit_title": "Unit",
                    "prompt": "[simulate-provider-unavailable]",
                },
            )
            assert failed.status_code == 503
            detail = failed.json()["detail"]
            assert "retry" in detail.lower()

            list_response = await client.get(
                "/courses/drafts",
                headers=_teacher_headers(),
            )
            assert list_response.status_code == 200
            drafts = list_response.json()["drafts"]
            assert drafts == []

    asyncio.run(scenario())
