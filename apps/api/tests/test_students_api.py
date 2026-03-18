from __future__ import annotations

import asyncio

import httpx

from app.core.security import create_access_token
from app.domains.auth.router import reset_auth_state_for_tests
from app.domains.students.repository import InMemoryStudentsRepository
from app.domains.students.router import reset_students_state_for_tests
from app.main import app


def _teacher_headers() -> dict[str, str]:
    token, _ = create_access_token(subject="usr_teacher_1", org_id="org_demo_1", role="teacher")
    return {"Authorization": f"Bearer {token}"}


def _non_teacher_headers() -> dict[str, str]:
    # Token carries role="parent" for usr_teacher_1 (stored as role="teacher" in auth repo).
    # require_authenticated_actor cross-checks token role vs. DB role → 403 Forbidden.
    token, _ = create_access_token(subject="usr_teacher_1", org_id="org_demo_1", role="parent")
    return {"Authorization": f"Bearer {token}"}


def _parent_headers() -> dict[str, str]:
    token, _ = create_access_token(subject="usr_parent_1", org_id="org_demo_1", role="parent")
    return {"Authorization": f"Bearer {token}"}


def setup_function() -> None:
    reset_auth_state_for_tests()
    reset_students_state_for_tests()
    app.dependency_overrides.clear()


# --- Test 1: create guardian link — teacher success ---


def test_create_guardian_link_teacher_success() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.post(
                "/students/usr_student_1/guardian-links",
                headers=_teacher_headers(),
                json={"guardian_id": "usr_parent_1"},
            )
            assert resp.status_code == 201
            body = resp.json()
            assert body["link_id"].startswith("link_")
            assert body["guardian_id"] == "usr_parent_1"
            assert body["student_id"] == "usr_student_1"
            assert body["org_id"] == "org_demo_1"
            assert body["linked_by"] == "usr_teacher_1"
            assert body["created_at"]

    asyncio.run(scenario())


# --- Test 2: duplicate link → 409 ---


def test_create_guardian_link_duplicate_conflict() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            await client.post(
                "/students/usr_student_1/guardian-links",
                headers=_teacher_headers(),
                json={"guardian_id": "usr_parent_1"},
            )
            resp = await client.post(
                "/students/usr_student_1/guardian-links",
                headers=_teacher_headers(),
                json={"guardian_id": "usr_parent_1"},
            )
            assert resp.status_code == 409

    asyncio.run(scenario())


# --- Test 3: unauthenticated → 401 ---


def test_create_guardian_link_unauthenticated() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.post(
                "/students/usr_student_1/guardian-links",
                json={"guardian_id": "usr_parent_1"},
            )
            assert resp.status_code == 401

    asyncio.run(scenario())


# --- Test 4: non-teacher role → 403 ---


def test_create_guardian_link_non_teacher_forbidden() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.post(
                "/students/usr_student_1/guardian-links",
                headers=_non_teacher_headers(),
                json={"guardian_id": "usr_parent_1"},
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


# --- Test 5: list guardian links — teacher success ---


def test_list_guardian_links_teacher_success() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            await client.post(
                "/students/usr_student_1/guardian-links",
                headers=_teacher_headers(),
                json={"guardian_id": "usr_parent_1"},
            )
            resp = await client.get(
                "/students/usr_student_1/guardian-links",
                headers=_teacher_headers(),
            )
            assert resp.status_code == 200
            body = resp.json()
            assert len(body["links"]) == 1
            link = body["links"][0]
            assert link["guardian_id"] == "usr_parent_1"
            assert link["student_id"] == "usr_student_1"
            assert link["org_id"] == "org_demo_1"
            assert link["linked_by"] == "usr_teacher_1"
            assert link["created_at"]

    asyncio.run(scenario())


# --- Test 6: list guardian links — empty ---


def test_list_guardian_links_empty() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get(
                "/students/usr_student_1/guardian-links",
                headers=_teacher_headers(),
            )
            assert resp.status_code == 200
            assert resp.json()["links"] == []

    asyncio.run(scenario())


# --- Test 7: list guardian links — unauthenticated → 401 ---


def test_list_guardian_links_unauthenticated() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get("/students/usr_student_1/guardian-links")
            assert resp.status_code == 401

    asyncio.run(scenario())


# --- Test 8: list guardian links — non-teacher → 403 ---


def test_list_guardian_links_non_teacher_forbidden() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get(
                "/students/usr_student_1/guardian-links",
                headers=_non_teacher_headers(),
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


# --- Test 9: delete guardian link — teacher success ---


def test_delete_guardian_link_teacher_success() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            create_resp = await client.post(
                "/students/usr_student_1/guardian-links",
                headers=_teacher_headers(),
                json={"guardian_id": "usr_parent_1"},
            )
            link_id = create_resp.json()["link_id"]
            resp = await client.delete(
                f"/students/usr_student_1/guardian-links/{link_id}",
                headers=_teacher_headers(),
            )
            assert resp.status_code == 204
            list_resp = await client.get(
                "/students/usr_student_1/guardian-links",
                headers=_teacher_headers(),
            )
            assert list_resp.json()["links"] == []

    asyncio.run(scenario())


# --- Test 10: delete unknown link → 404 ---


def test_delete_guardian_link_not_found() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.delete(
                "/students/usr_student_1/guardian-links/link_999",
                headers=_teacher_headers(),
            )
            assert resp.status_code == 404

    asyncio.run(scenario())


# --- Test 11: delete — unauthenticated → 401 ---


def test_delete_guardian_link_unauthenticated() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.delete("/students/usr_student_1/guardian-links/link_1")
            assert resp.status_code == 401

    asyncio.run(scenario())


# --- Test 12: delete — non-teacher → 403 ---


def test_delete_guardian_link_non_teacher_forbidden() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.delete(
                "/students/usr_student_1/guardian-links/link_1",
                headers=_non_teacher_headers(),
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


# --- Test 13: get_links_for_guardian repo direct (covers AC 9) ---


def test_get_links_for_guardian_repo_direct() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            await client.post(
                "/students/usr_student_1/guardian-links",
                headers=_teacher_headers(),
                json={"guardian_id": "usr_parent_1"},
            )
        links = InMemoryStudentsRepository().get_links_for_guardian("usr_parent_1", "org_demo_1")
        assert len(links) == 1
        assert links[0].guardian_id == "usr_parent_1"
        assert links[0].student_id == "usr_student_1"

    asyncio.run(scenario())


# --- Test 14: parent calling teacher endpoint → 403 (genuine RBAC check, covers AC 4) ---


def test_parent_calling_teacher_endpoint_forbidden() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.post(
                "/students/usr_student_1/guardian-links",
                headers=_parent_headers(),
                json={"guardian_id": "usr_parent_1"},
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


# --- Test 15: delete with mismatched student_id → 404 ---


def test_delete_student_mismatch_returns_404() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            create_resp = await client.post(
                "/students/usr_student_1/guardian-links",
                headers=_teacher_headers(),
                json={"guardian_id": "usr_parent_1"},
            )
            link_id = create_resp.json()["link_id"]
            resp = await client.delete(
                f"/students/usr_admin_1/guardian-links/{link_id}",
                headers=_teacher_headers(),
            )
            assert resp.status_code == 404

    asyncio.run(scenario())


# --- Test 16: org isolation validated at repo layer ---


def test_list_guardian_links_org_isolation() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            await client.post(
                "/students/usr_student_1/guardian-links",
                headers=_teacher_headers(),
                json={"guardian_id": "usr_parent_1"},
            )
        # NOTE: org isolation validated at repo layer; HTTP cross-org test not possible with
        # single-org seed — add org_demo_2 seed in a future story if needed
        links = InMemoryStudentsRepository().get_links_for_student("usr_student_1", "org_demo_2")
        assert links == []

    asyncio.run(scenario())
