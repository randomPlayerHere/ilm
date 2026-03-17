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


def test_edit_draft_endpoint_tracks_revision_and_keeps_draft() -> None:
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

            edited = await client.put(
                f"/courses/drafts/{draft_id}",
                headers=_teacher_headers(),
                json={
                    "objectives": ["Master multiplication facts", "Apply area models"],
                    "pacing_notes": "2x 40-minute sessions",
                    "assessments": ["Exit ticket", "Quick quiz"],
                },
            )
            assert edited.status_code == 200
            body = edited.json()
            assert body["status"] == "draft"
            assert body["revision"] == 2
            assert body["objectives"] == ["Master multiplication facts", "Apply area models"]

    asyncio.run(scenario())


def test_student_variant_endpoint_creates_distinct_plan_linked_to_base() -> None:
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
            created_body = created.json()
            draft_id = created_body["draft_id"]

            edited = await client.put(
                f"/courses/drafts/{draft_id}",
                headers=_teacher_headers(),
                json={
                    "objectives": ["Base objective"],
                    "pacing_notes": "base pace",
                    "assessments": ["Base assessment"],
                },
            )
            assert edited.status_code == 200

            variant = await client.post(
                f"/courses/drafts/{draft_id}/student-variants",
                headers=_teacher_headers(),
                json={
                    "student_id": "stu_demo_1",
                    "objectives": ["Scaffolded multiplication with manipulatives"],
                    "pacing_notes": "1:1 support",
                    "assessments": ["Teacher observation"],
                },
            )
            assert variant.status_code == 201
            variant_body = variant.json()
            assert variant_body["base_draft_id"] == draft_id
            assert variant_body["student_id"] == "stu_demo_1"
            assert variant_body["status"] == "draft"

            base = await client.get(f"/courses/drafts/{draft_id}", headers=_teacher_headers())
            assert base.status_code == 200
            base_body = base.json()
            assert base_body["student_id"] is None
            assert base_body["objectives"] == ["Base objective"]
            assert base_body["pacing_notes"] == "base pace"
            assert base_body["assessments"] == ["Base assessment"]

    asyncio.run(scenario())


def test_edit_and_variant_endpoints_enforce_authz_and_fail_closed_semantics() -> None:
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
            draft_id = created.json()["draft_id"]

            unauth_edit = await client.put(
                f"/courses/drafts/{draft_id}",
                json={
                    "objectives": ["A"],
                    "pacing_notes": "B",
                    "assessments": ["C"],
                },
            )
            assert unauth_edit.status_code == 401

            non_teacher_edit = await client.put(
                f"/courses/drafts/{draft_id}",
                headers={"Authorization": f"Bearer {parent_token}"},
                json={
                    "objectives": ["A"],
                    "pacing_notes": "B",
                    "assessments": ["C"],
                },
            )
            assert non_teacher_edit.status_code == 403

            unknown_edit = await client.put(
                "/courses/drafts/draft_missing",
                headers=_teacher_headers(),
                json={
                    "objectives": ["A"],
                    "pacing_notes": "B",
                    "assessments": ["C"],
                },
            )
            assert unknown_edit.status_code == 403

            unauth_variant = await client.post(
                f"/courses/drafts/{draft_id}/student-variants",
                json={
                    "student_id": "stu_demo_1",
                    "objectives": ["A"],
                    "pacing_notes": "B",
                    "assessments": ["C"],
                },
            )
            assert unauth_variant.status_code == 401

            non_teacher_variant = await client.post(
                f"/courses/drafts/{draft_id}/student-variants",
                headers={"Authorization": f"Bearer {parent_token}"},
                json={
                    "student_id": "stu_demo_1",
                    "objectives": ["A"],
                    "pacing_notes": "B",
                    "assessments": ["C"],
                },
            )
            assert non_teacher_variant.status_code == 403

            cross_tenant_variant = await client.post(
                f"/courses/drafts/{draft_id}/student-variants",
                headers=_teacher_headers(),
                json={
                    "student_id": "stu_other_org_1",
                    "objectives": ["A"],
                    "pacing_notes": "B",
                    "assessments": ["C"],
                },
            )
            assert cross_tenant_variant.status_code == 403

    asyncio.run(scenario())


def test_revisions_endpoint_enforces_authz_and_fail_closed_semantics() -> None:
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

            unauth_revisions = await client.get(f"/courses/drafts/{draft_id}/revisions")
            assert unauth_revisions.status_code == 401

            non_teacher_revisions = await client.get(
                f"/courses/drafts/{draft_id}/revisions",
                headers={"Authorization": f"Bearer {parent_token}"},
            )
            assert non_teacher_revisions.status_code == 403

            unknown_draft_revisions = await client.get(
                "/courses/drafts/draft_missing/revisions",
                headers=_teacher_headers(),
            )
            assert unknown_draft_revisions.status_code == 403

    asyncio.run(scenario())


def test_revisions_endpoint_returns_teacher_scoped_revision_history() -> None:
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

            edited = await client.put(
                f"/courses/drafts/{draft_id}",
                headers=_teacher_headers(),
                json={
                    "objectives": ["Edited objective"],
                    "pacing_notes": "Edited pace",
                    "assessments": ["Edited assessment"],
                },
            )
            assert edited.status_code == 200

            revisions = await client.get(
                f"/courses/drafts/{draft_id}/revisions",
                headers=_teacher_headers(),
            )
            assert revisions.status_code == 200
            body = revisions.json()
            assert len(body["revisions"]) == 2
            assert body["revisions"][0]["revision"] == 1
            assert body["revisions"][1]["revision"] == 2
            assert body["revisions"][1]["objectives"] == ["Edited objective"]

    asyncio.run(scenario())
