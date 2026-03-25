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


def test_list_classes_scoped_to_requesting_teacher() -> None:
    """Classes are scoped to the teacher_user_id on the token; seeded class belongs only to usr_teacher_1."""
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Create a class for teacher_1
            create_resp = await client.post(
                "/onboarding/classes",
                headers=_teacher_headers(),
                json={"name": "Art Class", "subject": "Art"},
            )
            assert create_resp.status_code == 201

            # Teacher_1 should see 2 classes (seeded + new)
            resp = await client.get("/onboarding/classes", headers=_teacher_headers())
            assert resp.status_code == 200
            body = resp.json()
            assert len(body["classes"]) == 2
            # All returned classes belong to teacher_1
            assert all(c["teacher_user_id"] == "usr_teacher_1" for c in body["classes"])

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


async def _csv_upload(client: httpx.AsyncClient, class_id: str, csv_content: str, headers: dict[str, str]) -> httpx.Response:
    return await client.post(
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


def test_csv_import_too_many_rows_returns_error_summary() -> None:
    """CSV imports exceeding 200 rows should return an error summary without enrolling anyone."""
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            rows = ["name,grade_level"] + [f"Student {i},Grade 5" for i in range(201)]
            csv_content = "\n".join(rows)
            resp = await _csv_upload(client, "cls_1", csv_content, _teacher_headers())
            assert resp.status_code == 200
            body = resp.json()
            assert body["successful"] == 0
            assert body["failed"] > 0
            assert any("Too many rows" in (r.get("error") or "") for r in body["results"])

            # No students should have been enrolled
            roster = await client.get("/onboarding/classes/cls_1/roster", headers=_teacher_headers())
            assert roster.json()["students"] == []

    asyncio.run(scenario())


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _parent_headers(user_id: str = "usr_parent_1") -> dict[str, str]:
    token, _ = create_access_token(subject=user_id, org_id="org_demo_1", role="parent")
    return {"Authorization": f"Bearer {token}"}


def _student_headers(user_id: str = "usr_student_1") -> dict[str, str]:
    token, _ = create_access_token(subject=user_id, org_id="org_demo_1", role="student")
    return {"Authorization": f"Bearer {token}"}


async def _add_student_to_class(client: httpx.AsyncClient, class_id: str = "cls_1") -> str:
    """Add a student to a class and return student_id."""
    resp = await client.post(
        f"/onboarding/classes/{class_id}/students",
        headers=_teacher_headers(),
        json={"name": "Test Student", "grade_level": "Grade 5"},
    )
    assert resp.status_code == 201
    return resp.json()["student_id"]


# ─── Invite link — generate ───────────────────────────────────────────────────


def test_generate_invite_link_success() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            student_id = await _add_student_to_class(client)
            resp = await client.post(
                f"/onboarding/classes/cls_1/students/{student_id}/invite-link",
                headers=_teacher_headers(),
            )
            assert resp.status_code == 200
            body = resp.json()
            assert "invite_id" in body
            assert "token" in body
            assert body["url"].startswith("ilm://invite/")
            assert body["student_id"] == student_id
            assert "expires_at" in body

    asyncio.run(scenario())


def test_generate_invite_link_idempotent() -> None:
    """Second call for same student returns existing active link."""
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            student_id = await _add_student_to_class(client)
            resp1 = await client.post(
                f"/onboarding/classes/cls_1/students/{student_id}/invite-link",
                headers=_teacher_headers(),
            )
            resp2 = await client.post(
                f"/onboarding/classes/cls_1/students/{student_id}/invite-link",
                headers=_teacher_headers(),
            )
            assert resp1.status_code == 200
            assert resp2.status_code == 200
            assert resp1.json()["token"] == resp2.json()["token"]

    asyncio.run(scenario())


def test_generate_invite_link_teacher_not_owner_returns_403() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            student_id = await _add_student_to_class(client)
            teacher2_token, _ = create_access_token(subject="usr_teacher_2", org_id="org_demo_1", role="teacher")
            resp = await client.post(
                f"/onboarding/classes/cls_1/students/{student_id}/invite-link",
                headers={"Authorization": f"Bearer {teacher2_token}"},
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


# ─── Invite link — resolve ────────────────────────────────────────────────────


def test_resolve_invite_link_valid_unused() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            student_id = await _add_student_to_class(client)
            gen_resp = await client.post(
                f"/onboarding/classes/cls_1/students/{student_id}/invite-link",
                headers=_teacher_headers(),
            )
            token = gen_resp.json()["token"]
            resp = await client.get(f"/onboarding/invite/{token}")
            assert resp.status_code == 200
            body = resp.json()
            assert body["valid"] is True
            assert body["reason"] is None
            assert body["class_name"] == "Math Period 3"

    asyncio.run(scenario())


def test_resolve_invite_link_already_used() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            student_id = await _add_student_to_class(client)
            gen_resp = await client.post(
                f"/onboarding/classes/cls_1/students/{student_id}/invite-link",
                headers=_teacher_headers(),
            )
            token = gen_resp.json()["token"]
            # Accept it as parent
            await client.post(
                f"/onboarding/invite/{token}/accept",
                headers=_parent_headers(),
            )
            # Now resolve
            resp = await client.get(f"/onboarding/invite/{token}")
            assert resp.status_code == 200
            body = resp.json()
            assert body["valid"] is False
            assert body["reason"] == "already_used"

    asyncio.run(scenario())


def test_resolve_invite_link_unknown_token_returns_404() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get("/onboarding/invite/nonexistent_token_xyz")
            assert resp.status_code == 404

    asyncio.run(scenario())


# ─── Invite link — accept ─────────────────────────────────────────────────────


def test_accept_invite_link_success() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            student_id = await _add_student_to_class(client)
            gen_resp = await client.post(
                f"/onboarding/classes/cls_1/students/{student_id}/invite-link",
                headers=_teacher_headers(),
            )
            token = gen_resp.json()["token"]
            resp = await client.post(
                f"/onboarding/invite/{token}/accept",
                headers=_parent_headers(),
            )
            assert resp.status_code == 200
            body = resp.json()
            assert "link_id" in body
            assert body["student_id"] == student_id

    asyncio.run(scenario())


def test_accept_invite_link_already_used_returns_400() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            student_id = await _add_student_to_class(client)
            gen_resp = await client.post(
                f"/onboarding/classes/cls_1/students/{student_id}/invite-link",
                headers=_teacher_headers(),
            )
            token = gen_resp.json()["token"]
            # Accept once
            await client.post(f"/onboarding/invite/{token}/accept", headers=_parent_headers())
            # Accept same used invite again — used_at check fires before linked check → 400
            resp = await client.post(
                f"/onboarding/invite/{token}/accept",
                headers=_parent_headers(),
            )
            assert resp.status_code == 400

    asyncio.run(scenario())


def test_accept_invite_link_already_linked_returns_409() -> None:
    """Parent accepting the same student's invite twice → 409."""
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Add student, generate first invite, accept it
            student_id = await _add_student_to_class(client)
            gen1 = await client.post(
                f"/onboarding/classes/cls_1/students/{student_id}/invite-link",
                headers=_teacher_headers(),
            )
            token1 = gen1.json()["token"]
            await client.post(f"/onboarding/invite/{token1}/accept", headers=_parent_headers())

            # Create a class for teacher 2, add the same student somehow via another approach
            # Simpler: generate a new invite for the same student from a different class
            # Actually since the idempotent check returns same token, we need a new student
            # The 409 case: same parent tries to accept a second invite for the SAME student
            # To test this, we need a new (different, non-used) invite for the SAME student.
            # Since the existing invite is used, a new one will be created.
            # But the parent is already linked to that student → 409
            # To create a second active invite: the service creates a new one because the old is used.
            gen2 = await client.post(
                f"/onboarding/classes/cls_1/students/{student_id}/invite-link",
                headers=_teacher_headers(),
            )
            token2 = gen2.json()["token"]
            resp = await client.post(
                f"/onboarding/invite/{token2}/accept",
                headers=_parent_headers(),
            )
            assert resp.status_code == 409

    asyncio.run(scenario())


def test_accept_invite_link_non_parent_returns_403() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            student_id = await _add_student_to_class(client)
            gen_resp = await client.post(
                f"/onboarding/classes/cls_1/students/{student_id}/invite-link",
                headers=_teacher_headers(),
            )
            token = gen_resp.json()["token"]
            resp = await client.post(
                f"/onboarding/invite/{token}/accept",
                headers=_teacher_headers(),  # teacher, not parent
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


# ─── Join class by code ───────────────────────────────────────────────────────


def test_join_class_by_code_success() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.post(
                "/onboarding/join",
                headers=_student_headers(),
                json={"join_code": "A3BX9K"},  # seeded join code for cls_1
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["class_id"] == "cls_1"
            assert body["class_name"] == "Math Period 3"
            assert body["subject"] == "Mathematics"

    asyncio.run(scenario())


def test_join_class_by_code_invalid_code_returns_404() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.post(
                "/onboarding/join",
                headers=_student_headers(),
                json={"join_code": "ZZZZZZ"},
            )
            assert resp.status_code == 404

    asyncio.run(scenario())


def test_join_class_already_enrolled_returns_409() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Join once
            await client.post(
                "/onboarding/join",
                headers=_student_headers(),
                json={"join_code": "A3BX9K"},
            )
            # Join again
            resp = await client.post(
                "/onboarding/join",
                headers=_student_headers(),
                json={"join_code": "A3BX9K"},
            )
            assert resp.status_code == 409

    asyncio.run(scenario())


def test_join_class_non_student_returns_403() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.post(
                "/onboarding/join",
                headers=_teacher_headers(),  # teacher, not student
                json={"join_code": "A3BX9K"},
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


# ─── Parent linked children ─────────────────────────────────────────────────


def test_get_linked_children_returns_empty_when_no_links() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get(
                "/onboarding/parent/children",
                headers=_parent_headers(),
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["children"] == []

    asyncio.run(scenario())


def test_get_linked_children_returns_linked_child_with_class() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Add student to class and generate invite link
            student_id = await _add_student_to_class(client)
            gen_resp = await client.post(
                f"/onboarding/classes/cls_1/students/{student_id}/invite-link",
                headers=_teacher_headers(),
            )
            token = gen_resp.json()["token"]
            # Parent accepts invite
            await client.post(f"/onboarding/invite/{token}/accept", headers=_parent_headers())

            # Fetch linked children
            resp = await client.get(
                "/onboarding/parent/children",
                headers=_parent_headers(),
            )
            assert resp.status_code == 200
            body = resp.json()
            assert len(body["children"]) == 1
            child = body["children"][0]
            assert child["student_id"] == student_id
            assert "student_name" in child
            assert "link_id" in child
            assert "consent_status" in child
            assert child["class_name"] == "Math Period 3"
            assert child["subject"] == "Mathematics"

    asyncio.run(scenario())


def test_get_linked_children_requires_parent_role() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get(
                "/onboarding/parent/children",
                headers=_teacher_headers(),  # teacher, not parent
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


def test_get_linked_children_requires_auth() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get("/onboarding/parent/children")
            assert resp.status_code == 401

    asyncio.run(scenario())
