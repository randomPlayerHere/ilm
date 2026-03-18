from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime

import httpx

from app.core.security import create_access_token
from app.domains.auth.router import reset_auth_state_for_tests
from app.domains.grading.repository import InMemoryGradingRepository
from app.domains.progress.router import reset_progress_state_for_tests
from app.main import app


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------


def _parent_headers() -> dict[str, str]:
    token, _ = create_access_token(subject="usr_parent_1", org_id="org_demo_1", role="parent")
    return {"Authorization": f"Bearer {token}"}


def _student_headers() -> dict[str, str]:
    token, _ = create_access_token(subject="usr_student_1", org_id="org_demo_1", role="student")
    return {"Authorization": f"Bearer {token}"}


def _teacher_headers() -> dict[str, str]:
    # teacher role → not parent or student → 403 from _require_parent_or_student
    token, _ = create_access_token(subject="usr_teacher_1", org_id="org_demo_1", role="teacher")
    return {"Authorization": f"Bearer {token}"}


def _wrong_student_headers() -> dict[str, str]:
    # Mismatched-role trick: usr_teacher_1 is stored as role=teacher in auth repo.
    # Sending role=student in token → require_authenticated_actor cross-check → 403.
    token, _ = create_access_token(subject="usr_teacher_1", org_id="org_demo_1", role="student")
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Grading state helpers (direct repo — avoids HTTP pipeline overhead)
# ---------------------------------------------------------------------------


def _create_approved_grade_pipeline(student_id: str = "usr_student_1", org_id: str = "org_demo_1") -> tuple[str, str, str]:
    """Create assignment → artifact → grading job → result → approval. Returns (job_id, artifact_id, assignment_id)."""
    repo = InMemoryGradingRepository()
    assignment = repo.create_assignment(
        class_id="cls_demo_math_1",
        org_id=org_id,
        teacher_user_id="usr_teacher_1",
        title="Test Assignment",
    )
    artifact = repo.create_artifact(
        assignment_id=assignment.assignment_id,
        student_id=student_id,
        class_id="cls_demo_math_1",
        org_id=org_id,
        teacher_user_id="usr_teacher_1",
        file_name="test.pdf",
        media_type="application/pdf",
    )
    job = repo.create_grading_job(
        artifact_id=artifact.artifact_id,
        assignment_id=assignment.assignment_id,
        org_id=org_id,
        teacher_user_id="usr_teacher_1",
    )
    repo.save_grading_result(
        job_id=job.job_id,
        proposed_score="85",
        rubric_mapping={"clarity": "good"},
        draft_feedback="Good work.",
    )
    now = datetime.now(UTC).isoformat()
    repo.upsert_grade_approval(
        job_id=job.job_id,
        approved_score="90",
        approved_feedback="Excellent work.",
        approver_user_id="usr_teacher_1",
        version=1,
        approved_at=now,
    )
    return job.job_id, artifact.artifact_id, assignment.assignment_id


def _create_confirmed_recommendation_pipeline(student_id: str = "usr_student_1", org_id: str = "org_demo_1") -> str:
    """Create full recommendation pipeline through confirmation. Returns rec_job_id."""
    repo = InMemoryGradingRepository()
    job_id, _, assignment_id = _create_approved_grade_pipeline(student_id=student_id, org_id=org_id)
    rec_job = repo.create_recommendation_job(
        job_id=job_id,
        assignment_id=assignment_id,
        org_id=org_id,
        teacher_user_id="usr_teacher_1",
        student_id=student_id,
    )
    repo.save_recommendation_result(
        rec_job_id=rec_job.rec_job_id,
        job_id=job_id,
        student_id=student_id,
        topics=[{"topic": "Algebra", "suggestion": "Practice more", "weakness_signal": "low score"}],
    )
    now = datetime.now(UTC).isoformat()
    repo.upsert_confirmed_recommendation(
        rec_job_id=rec_job.rec_job_id,
        job_id=job_id,
        student_id=student_id,
        topics=[{"topic": "Algebra", "suggestion": "Practice more", "weakness_signal": "low score"}],
        confirmed_by="usr_teacher_1",
        confirmed_at=now,
    )
    return rec_job.rec_job_id


def _create_guardian_link(student_id: str = "usr_student_1") -> None:
    """Create guardian-student link via HTTP POST as teacher."""
    async def _do() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            token, _ = create_access_token(subject="usr_teacher_1", org_id="org_demo_1", role="teacher")
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.post(
                f"/students/{student_id}/guardian-links",
                headers=headers,
                json={"guardian_id": "usr_parent_1"},
            )
            assert resp.status_code == 201, f"Failed to create guardian link: {resp.json()}"
    asyncio.run(_do())


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------


def setup_function() -> None:
    reset_auth_state_for_tests()
    reset_progress_state_for_tests()
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Test 1: parent success — grades endpoint
# ---------------------------------------------------------------------------


def test_parent_can_access_linked_student_grades() -> None:
    _create_approved_grade_pipeline()
    _create_guardian_link()

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get(
                "/progress/students/usr_student_1/grades",
                headers=_parent_headers(),
            )
            assert resp.status_code == 200
            body = resp.json()
            assert len(body["grades"]) == 1
            grade = body["grades"][0]
            assert grade["student_id"] == "usr_student_1"
            assert grade["approved_score"] == "90"
            assert grade["approved_feedback"] == "Excellent work."
            assert grade["approver_user_id"] == "usr_teacher_1"
            assert grade["version"] == 1

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Test 2: student self-access — grades endpoint
# ---------------------------------------------------------------------------


def test_student_can_access_own_grades() -> None:
    _create_approved_grade_pipeline()

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get(
                "/progress/students/usr_student_1/grades",
                headers=_student_headers(),
            )
            assert resp.status_code == 200
            body = resp.json()
            assert len(body["grades"]) == 1
            assert body["grades"][0]["student_id"] == "usr_student_1"

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Test 3: parent unlinked → 404
# ---------------------------------------------------------------------------


def test_parent_unlinked_student_returns_404() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get(
                "/progress/students/usr_student_1/grades",
                headers=_parent_headers(),
            )
            assert resp.status_code == 404

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Test 4: student wrong id → 403
# ---------------------------------------------------------------------------


def test_student_wrong_id_returns_403() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get(
                "/progress/students/usr_student_2/grades",
                headers=_student_headers(),
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Test 5: unauthenticated → 401
# ---------------------------------------------------------------------------


def test_unauthenticated_returns_401() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get("/progress/students/usr_student_1/grades")
            assert resp.status_code == 401

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Test 6: teacher role → 403
# ---------------------------------------------------------------------------


def test_teacher_role_returns_403() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get(
                "/progress/students/usr_student_1/grades",
                headers=_teacher_headers(),
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Test 7: org isolation (repo-layer validation)
# ---------------------------------------------------------------------------


def test_org_isolation_repo_layer() -> None:
    repo = InMemoryGradingRepository()
    # stu_other_org_1 is in org_other_1 — querying with org_demo_1 returns empty
    results = repo.list_approved_grades_for_student("stu_other_org_1", "org_demo_1")
    assert results == []

    # HTTP cross-org isolation is also covered by tests 17-18 (parent with cross-org link → 404)


# ---------------------------------------------------------------------------
# Test 8: empty state returns 200 with empty list
# ---------------------------------------------------------------------------


def test_empty_state_returns_200_empty_list() -> None:
    _create_guardian_link()

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get(
                "/progress/students/usr_student_1/grades",
                headers=_parent_headers(),
            )
            assert resp.status_code == 200
            assert resp.json()["grades"] == []

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Test 9: unapproved grade not returned
# ---------------------------------------------------------------------------


def test_unapproved_grade_not_surfaced() -> None:
    # Create artifact + job but NO approval
    repo = InMemoryGradingRepository()
    assignment = repo.create_assignment(
        class_id="cls_demo_math_1",
        org_id="org_demo_1",
        teacher_user_id="usr_teacher_1",
        title="Unapproved Assignment",
    )
    artifact = repo.create_artifact(
        assignment_id=assignment.assignment_id,
        student_id="usr_student_1",
        class_id="cls_demo_math_1",
        org_id="org_demo_1",
        teacher_user_id="usr_teacher_1",
        file_name="test.pdf",
        media_type="application/pdf",
    )
    job = repo.create_grading_job(
        artifact_id=artifact.artifact_id,
        assignment_id=assignment.assignment_id,
        org_id="org_demo_1",
        teacher_user_id="usr_teacher_1",
    )
    repo.save_grading_result(
        job_id=job.job_id,
        proposed_score="70",
        rubric_mapping={},
        draft_feedback="Draft feedback.",
    )
    # No approval → should not appear

    _create_guardian_link()

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get(
                "/progress/students/usr_student_1/grades",
                headers=_parent_headers(),
            )
            assert resp.status_code == 200
            assert resp.json()["grades"] == []

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Test 10: unconfirmed recommendation not returned
# ---------------------------------------------------------------------------


def test_unconfirmed_recommendation_not_surfaced() -> None:
    # Create recommendation pipeline but NO confirmation
    repo = InMemoryGradingRepository()
    job_id, _, assignment_id = _create_approved_grade_pipeline()
    rec_job = repo.create_recommendation_job(
        job_id=job_id,
        assignment_id=assignment_id,
        org_id="org_demo_1",
        teacher_user_id="usr_teacher_1",
        student_id="usr_student_1",
    )
    repo.save_recommendation_result(
        rec_job_id=rec_job.rec_job_id,
        job_id=job_id,
        student_id="usr_student_1",
        topics=[{"topic": "Geometry", "suggestion": "Practice", "weakness_signal": "low"}],
    )
    # No confirmation → should not appear

    _create_guardian_link()

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get(
                "/progress/students/usr_student_1/recommendations",
                headers=_parent_headers(),
            )
            assert resp.status_code == 200
            assert resp.json()["recommendations"] == []

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Test 11: parent access to recommendations endpoint
# ---------------------------------------------------------------------------


def test_parent_can_access_linked_student_recommendations() -> None:
    _create_confirmed_recommendation_pipeline()  # side effect: seeds confirmed rec state
    _create_guardian_link()

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get(
                "/progress/students/usr_student_1/recommendations",
                headers=_parent_headers(),
            )
            assert resp.status_code == 200
            body = resp.json()
            assert len(body["recommendations"]) == 1
            rec = body["recommendations"][0]
            assert rec["student_id"] == "usr_student_1"
            assert rec["confirmed_by"] == "usr_teacher_1"
            assert len(rec["topics"]) == 1
            assert rec["topics"][0]["topic"] == "Algebra"

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Test 12: student access to recommendations endpoint
# ---------------------------------------------------------------------------


def test_student_can_access_own_recommendations() -> None:
    _create_confirmed_recommendation_pipeline()  # side effect: seeds confirmed rec state

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get(
                "/progress/students/usr_student_1/recommendations",
                headers=_student_headers(),
            )
            assert resp.status_code == 200
            body = resp.json()
            assert len(body["recommendations"]) == 1
            assert body["recommendations"][0]["student_id"] == "usr_student_1"

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Test 13: admin role → 403 (AC3 — covers non-parent/non-student roles beyond teacher)
# ---------------------------------------------------------------------------


def test_admin_role_returns_403() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            token, _ = create_access_token(subject="usr_admin_1", org_id="org_demo_1", role="admin")
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.get(
                "/progress/students/usr_student_1/grades",
                headers=headers,
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Test 14: mismatched-role token → 403 at auth layer (exercises _wrong_student_headers)
# ---------------------------------------------------------------------------


def test_mismatched_role_token_returns_403() -> None:
    """Auth layer cross-check: usr_teacher_1 claims role=student but is teacher in DB → 403."""
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get(
                "/progress/students/usr_teacher_1/grades",
                headers=_wrong_student_headers(),
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Test 15: recommendations empty state → 200 with [] (AC8 — symmetric with test 8)
# ---------------------------------------------------------------------------


def test_empty_state_recommendations_returns_200_empty_list() -> None:
    _create_guardian_link()

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get(
                "/progress/students/usr_student_1/recommendations",
                headers=_parent_headers(),
            )
            assert resp.status_code == 200
            assert resp.json()["recommendations"] == []

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Test 16: recommendations unauthenticated → 401
# ---------------------------------------------------------------------------


def test_recommendations_unauthenticated_returns_401() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get("/progress/students/usr_student_1/recommendations")
            assert resp.status_code == 401

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Tests 17-18: AC7 cross-org isolation over HTTP
# Parent has a guardian link to stu_other_org_1 (cross-org student);
# endpoint must return 404, not 200+[] — defense-in-depth org check in router.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Test 17: teacher role → 403 on /recommendations (symmetric with test 6 on /grades)
# ---------------------------------------------------------------------------


def test_teacher_role_recommendations_returns_403() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get(
                "/progress/students/usr_student_1/recommendations",
                headers=_teacher_headers(),
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Test 18: principal role → 403 on grades (covers non-parent/non-student principal role)
# ---------------------------------------------------------------------------


def test_principal_role_returns_403() -> None:
    """Principal role must not access progress data.
    Uses mismatched-role trick: usr_teacher_1 claims role=principal but is teacher in DB.
    Auth layer cross-check catches mismatch → 403 (principal is excluded at auth or endpoint level).
    """
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            token, _ = create_access_token(subject="usr_teacher_1", org_id="org_demo_1", role="principal")
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.get(
                "/progress/students/usr_student_1/grades",
                headers=headers,
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Tests 19-20: AC7 cross-org isolation over HTTP
# Parent has a guardian link to stu_other_org_1 (cross-org student);
# endpoint must return 404, not 200+[] — defense-in-depth org check in router.
# ---------------------------------------------------------------------------


def test_parent_cross_org_link_grades_returns_404() -> None:
    """AC7: parent (org_demo_1) has a link to stu_other_org_1 (org_other_1) → 404.
    org_other_1 serves as the cross-org tenant (AC7 intent: cross-org isolation, org name is illustrative).
    """
    _create_guardian_link(student_id="stu_other_org_1")

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get(
                "/progress/students/stu_other_org_1/grades",
                headers=_parent_headers(),
            )
            assert resp.status_code == 404

    asyncio.run(scenario())


def test_parent_cross_org_link_recommendations_returns_404() -> None:
    """AC7: parent (org_demo_1) has a link to stu_other_org_1 (org_other_1) → 404."""  # noqa: E501
    _create_guardian_link(student_id="stu_other_org_1")

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get(
                "/progress/students/stu_other_org_1/recommendations",
                headers=_parent_headers(),
            )
            assert resp.status_code == 404

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Test 21: grade response includes assignment_title (AC1)
# ---------------------------------------------------------------------------


def test_grade_response_includes_assignment_title() -> None:
    """AC1: grade response includes assignment_title matching the title passed to create_assignment."""
    repo = InMemoryGradingRepository()
    assignment = repo.create_assignment(
        class_id="cls_demo_math_1",
        org_id="org_demo_1",
        teacher_user_id="usr_teacher_1",
        title="Math Quiz",
    )
    artifact = repo.create_artifact(
        assignment_id=assignment.assignment_id,
        student_id="usr_student_1",
        class_id="cls_demo_math_1",
        org_id="org_demo_1",
        teacher_user_id="usr_teacher_1",
        file_name="quiz.pdf",
        media_type="application/pdf",
    )
    job = repo.create_grading_job(
        artifact_id=artifact.artifact_id,
        assignment_id=assignment.assignment_id,
        org_id="org_demo_1",
        teacher_user_id="usr_teacher_1",
    )
    repo.save_grading_result(
        job_id=job.job_id,
        proposed_score="80",
        rubric_mapping={},
        draft_feedback="Good.",
    )
    repo.upsert_grade_approval(
        job_id=job.job_id,
        approved_score="85",
        approved_feedback="Well done.",
        approver_user_id="usr_teacher_1",
        version=1,
        approved_at=datetime.now(UTC).isoformat(),
    )

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get(
                "/progress/students/usr_student_1/grades",
                headers=_student_headers(),
            )
            assert resp.status_code == 200
            grades = resp.json()["grades"]
            assert len(grades) == 1
            assert grades[0]["assignment_title"] == "Math Quiz"
            assert grades[0]["assignment_id"] == assignment.assignment_id
            assert grades[0]["approved_feedback"] == "Well done."

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Test 22: grades returned in chronological order (AC3 — trend ordering)
# ---------------------------------------------------------------------------


def test_grades_returned_in_chronological_order() -> None:
    """AC3: grades returned sorted by approved_at ascending (oldest → newest).

    Creates Beta (later date) first, then Alpha (earlier date) to confirm
    the response is sorted by timestamp rather than insertion order.
    """
    repo = InMemoryGradingRepository()

    def _make_pipeline(title: str, approved_at: str) -> None:
        assignment = repo.create_assignment(
            class_id="cls_demo_math_1",
            org_id="org_demo_1",
            teacher_user_id="usr_teacher_1",
            title=title,
        )
        artifact = repo.create_artifact(
            assignment_id=assignment.assignment_id,
            student_id="usr_student_1",
            class_id="cls_demo_math_1",
            org_id="org_demo_1",
            teacher_user_id="usr_teacher_1",
            file_name="work.pdf",
            media_type="application/pdf",
        )
        job = repo.create_grading_job(
            artifact_id=artifact.artifact_id,
            assignment_id=assignment.assignment_id,
            org_id="org_demo_1",
            teacher_user_id="usr_teacher_1",
        )
        repo.save_grading_result(
            job_id=job.job_id,
            proposed_score="75",
            rubric_mapping={},
            draft_feedback="Draft.",
        )
        repo.upsert_grade_approval(
            job_id=job.job_id,
            approved_score="80",
            approved_feedback="Good.",
            approver_user_id="usr_teacher_1",
            version=1,
            approved_at=approved_at,
        )

    # Insert Beta (later date) first, then Alpha (earlier date) — validates sort, not insertion order
    _make_pipeline("Assignment Beta", "2024-02-01T00:00:00+00:00")
    _make_pipeline("Assignment Alpha", "2024-01-01T00:00:00+00:00")

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get(
                "/progress/students/usr_student_1/grades",
                headers=_student_headers(),
            )
            assert resp.status_code == 200
            grades = resp.json()["grades"]
            assert len(grades) == 2
            assert grades[0]["assignment_title"] == "Assignment Alpha"
            assert grades[1]["assignment_title"] == "Assignment Beta"
            assert grades[0]["approved_at"] < grades[1]["approved_at"]

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Test 23: AC4 performance contract — grades endpoint p95 ≤ 700 ms (NFR-001)
# ---------------------------------------------------------------------------


def test_grades_endpoint_responds_within_max_700ms() -> None:
    """AC4: NFR-001 requires p95 ≤ 700 ms for student read endpoints.

    Runs 5 warm-up requests (discarded) then 20 measured requests against the
    in-memory ASGI app. Asserts that the maximum observed latency stays under
    700 ms — a conservative proxy for the p95 constraint with this sample size.
    In-process ASGI calls have no network overhead; any breach indicates a
    regression in computation or middleware, not transport.
    """
    _create_approved_grade_pipeline()
    latencies: list[float] = []

    async def measure() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Warm-up: discard first 5 requests to avoid cold-start skew
            for _ in range(5):
                await client.get(
                    "/progress/students/usr_student_1/grades",
                    headers=_student_headers(),
                )
            # Measured pass: 20 requests
            for _ in range(20):
                start = time.perf_counter()
                resp = await client.get(
                    "/progress/students/usr_student_1/grades",
                    headers=_student_headers(),
                )
                latencies.append(time.perf_counter() - start)
                assert resp.status_code == 200

    asyncio.run(measure())
    max_ms = max(latencies) * 1000
    assert max_ms <= 700, f"max latency {max_ms:.1f} ms exceeds 700 ms NFR-001 threshold"
