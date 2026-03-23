from __future__ import annotations

import asyncio
import io

import httpx

from app.core.security import create_access_token
from app.domains.auth.router import reset_auth_state_for_tests
from app.domains.onboarding.router import reset_onboarding_state_for_tests
from app.main import app


def _teacher_headers(user_id: str = "usr_teacher_1") -> dict[str, str]:
    token, _ = create_access_token(subject=user_id, org_id="org_demo_1", role="teacher")
    return {"Authorization": f"Bearer {token}"}


def _non_teacher_headers() -> dict[str, str]:
    token, _ = create_access_token(subject="usr_parent_1", org_id="org_demo_1", role="parent")
    return {"Authorization": f"Bearer {token}"}


def setup_function() -> None:
    reset_auth_state_for_tests()
    reset_onboarding_state_for_tests()
    app.dependency_overrides.clear()


# ─── Class creation ────────────────────────────────────────────────────────────


def test_create_class_success() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.post(
                "/onboarding/classes",
                headers=_teacher_headers(),
                json={"name": "Science Period 1", "subject": "Science"},
            )
            assert resp.status_code == 201
            body = resp.json()
            assert body["name"] == "Science Period 1"
            assert body["subject"] == "Science"
            assert len(body["join_code"]) == 6
            assert body["join_code"].isupper() or body["join_code"].isalnum()
            assert body["student_count"] == 0
            assert body["org_id"] == "org_demo_1"
            assert body["teacher_user_id"] == "usr_teacher_1"

    asyncio.run(scenario())


def test_create_class_requires_teacher_role() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.post(
                "/onboarding/classes",
                headers=_non_teacher_headers(),
                json={"name": "Math", "subject": "Mathematics"},
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


def test_create_class_requires_auth() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.post(
                "/onboarding/classes",
                json={"name": "Math", "subject": "Mathematics"},
            )
            assert resp.status_code == 401

    asyncio.run(scenario())


# ─── List classes ──────────────────────────────────────────────────────────────


def test_list_classes_returns_seeded_and_created() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Seeded class cls_1 belongs to usr_teacher_1
            resp = await client.get("/onboarding/classes", headers=_teacher_headers())
            assert resp.status_code == 200
            body = resp.json()
            assert len(body["classes"]) == 1
            assert body["classes"][0]["class_id"] == "cls_1"

            # Create another
            await client.post(
                "/onboarding/classes",
                headers=_teacher_headers(),
                json={"name": "History", "subject": "History"},
            )
            resp2 = await client.get("/onboarding/classes", headers=_teacher_headers())
            assert len(resp2.json()["classes"]) == 2

    asyncio.run(scenario())


def test_list_classes_scoped_to_teacher() -> None:
    """Teacher 2 should not see teacher 1's classes."""
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            teacher2_token, _ = create_access_token(subject="usr_teacher_2", org_id="org_demo_1", role="teacher")
            resp = await client.get(
                "/onboarding/classes",
                headers={"Authorization": f"Bearer {teacher2_token}"},
            )
            assert resp.status_code == 200
            assert resp.json()["classes"] == []

    asyncio.run(scenario())


# ─── Roster ────────────────────────────────────────────────────────────────────


def test_get_roster_initially_empty() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get(
                "/onboarding/classes/cls_1/roster",
                headers=_teacher_headers(),
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["class_id"] == "cls_1"
            assert body["students"] == []

    asyncio.run(scenario())


def test_get_roster_class_not_found() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get(
                "/onboarding/classes/cls_nonexistent/roster",
                headers=_teacher_headers(),
            )
            assert resp.status_code == 404

    asyncio.run(scenario())


def test_get_roster_forbidden_if_not_owner() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            teacher2_token, _ = create_access_token(subject="usr_teacher_2", org_id="org_demo_1", role="teacher")
            resp = await client.get(
                "/onboarding/classes/cls_1/roster",
                headers={"Authorization": f"Bearer {teacher2_token}"},
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


# ─── Add student ───────────────────────────────────────────────────────────────


def test_add_student_success() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.post(
                "/onboarding/classes/cls_1/students",
                headers=_teacher_headers(),
                json={"name": "Jane Smith", "grade_level": "Grade 5"},
            )
            assert resp.status_code == 201
            body = resp.json()
            assert body["name"] == "Jane Smith"
            assert body["grade_level"] == "Grade 5"
            assert body["student_id"].startswith("stu_")

            # Roster should now show the student
            roster = await client.get("/onboarding/classes/cls_1/roster", headers=_teacher_headers())
            assert len(roster.json()["students"]) == 1

            # student_count in class list should be 1
            classes = await client.get("/onboarding/classes", headers=_teacher_headers())
            assert classes.json()["classes"][0]["student_count"] == 1

    asyncio.run(scenario())


def test_add_student_to_nonexistent_class_returns_404() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.post(
                "/onboarding/classes/cls_bad/students",
                headers=_teacher_headers(),
                json={"name": "Bob", "grade_level": "Grade 4"},
            )
            assert resp.status_code == 404

    asyncio.run(scenario())


def test_add_student_forbidden_if_not_owner() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            teacher2_token, _ = create_access_token(subject="usr_teacher_2", org_id="org_demo_1", role="teacher")
            resp = await client.post(
                "/onboarding/classes/cls_1/students",
                headers={"Authorization": f"Bearer {teacher2_token}"},
                json={"name": "Bob", "grade_level": "Grade 4"},
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


# ─── Remove student ────────────────────────────────────────────────────────────


def test_remove_student_success() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Add student
            add_resp = await client.post(
                "/onboarding/classes/cls_1/students",
                headers=_teacher_headers(),
                json={"name": "Alice", "grade_level": "Grade 5"},
            )
            student_id = add_resp.json()["student_id"]

            # Remove student
            del_resp = await client.delete(
                f"/onboarding/classes/cls_1/students/{student_id}",
                headers=_teacher_headers(),
            )
            assert del_resp.status_code == 204

            # Roster should be empty
            roster = await client.get("/onboarding/classes/cls_1/roster", headers=_teacher_headers())
            assert roster.json()["students"] == []

    asyncio.run(scenario())


def test_remove_student_not_enrolled_returns_404() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.delete(
                "/onboarding/classes/cls_1/students/stu_nonexistent",
                headers=_teacher_headers(),
            )
            assert resp.status_code == 404

    asyncio.run(scenario())


# ─── CSV import ────────────────────────────────────────────────────────────────


def _csv_upload(client: httpx.AsyncClient, class_id: str, csv_content: str, headers: dict[str, str]) -> httpx.Response:
    return client.post(
        f"/onboarding/classes/{class_id}/students/import",
        headers=headers,
        files={"file": ("students.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )


def test_csv_import_valid_rows() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            csv_content = "name,grade_level\nJane Smith,Grade 5\nJohn Doe,Grade 5\n"
            resp = await _csv_upload(client, "cls_1", csv_content, _teacher_headers())
            assert resp.status_code == 200
            body = resp.json()
            assert body["total_rows"] == 2
            assert body["successful"] == 2
            assert body["failed"] == 0
            assert all(r["success"] for r in body["results"])

            # Students should appear on roster
            roster = await client.get("/onboarding/classes/cls_1/roster", headers=_teacher_headers())
            assert len(roster.json()["students"]) == 2

    asyncio.run(scenario())


def test_csv_import_partial_errors() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            csv_content = "name,grade_level\nJane Smith,Grade 5\n,Grade 5\nJohn Doe,\n"
            resp = await _csv_upload(client, "cls_1", csv_content, _teacher_headers())
            assert resp.status_code == 200
            body = resp.json()
            assert body["total_rows"] == 3
            assert body["successful"] == 1
            assert body["failed"] == 2
            error_rows = [r for r in body["results"] if not r["success"]]
            assert len(error_rows) == 2

    asyncio.run(scenario())


def test_csv_import_missing_columns_returns_error_summary() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            csv_content = "student_name,level\nJane,5\n"
            resp = await _csv_upload(client, "cls_1", csv_content, _teacher_headers())
            assert resp.status_code == 200
            body = resp.json()
            assert body["successful"] == 0
            assert body["failed"] == 1
            assert "name" in body["results"][0]["error"].lower()

    asyncio.run(scenario())


def test_csv_import_idempotent_same_student() -> None:
    """Importing the same student twice should not duplicate them."""
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            csv_content = "name,grade_level\nJane Smith,Grade 5\n"
            await _csv_upload(client, "cls_1", csv_content, _teacher_headers())
            await _csv_upload(client, "cls_1", csv_content, _teacher_headers())

            roster = await client.get("/onboarding/classes/cls_1/roster", headers=_teacher_headers())
            assert len(roster.json()["students"]) == 1

    asyncio.run(scenario())


def test_csv_import_case_insensitive_headers() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            csv_content = "Name,Grade_Level\nJane Smith,Grade 5\n"
            resp = await _csv_upload(client, "cls_1", csv_content, _teacher_headers())
            assert resp.status_code == 200
            body = resp.json()
            assert body["successful"] == 1

    asyncio.run(scenario())


def test_csv_import_requires_teacher() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            csv_content = "name,grade_level\nJane,Grade 5\n"
            resp = await _csv_upload(client, "cls_1", csv_content, _non_teacher_headers())
            assert resp.status_code == 403

    asyncio.run(scenario())
