from __future__ import annotations

import asyncio

import httpx
import os

from app.core.security import create_access_token
from app.domains.grading.ai_provider import (
    MockAIGradingProvider,
    NonMockAIGradingProvider,
)
from app.domains.grading.router import _make_ai_provider
from app.domains.auth.router import reset_auth_state_for_tests
from app.domains.grading.router import reset_grading_state_for_tests
from app.main import app


def _teacher_headers() -> dict[str, str]:
    token, _ = create_access_token(
        subject="usr_teacher_1", org_id="org_demo_1", role="teacher"
    )
    return {"Authorization": f"Bearer {token}"}


def _non_teacher_headers() -> dict[str, str]:
    # usr_teacher_1 is stored as role="teacher" in auth repo — mismatched role token → 403
    token, _ = create_access_token(
        subject="usr_teacher_1", org_id="org_demo_1", role="parent"
    )
    return {"Authorization": f"Bearer {token}"}


def setup_function() -> None:
    reset_auth_state_for_tests()
    reset_grading_state_for_tests()
    app.dependency_overrides.clear()


def test_make_ai_provider_switches_with_env_var() -> None:
    original = os.environ.get("AI_MOCK_MODE")
    try:
        os.environ["AI_MOCK_MODE"] = "true"
        assert isinstance(_make_ai_provider(), MockAIGradingProvider)
        os.environ["AI_MOCK_MODE"] = "false"
        assert isinstance(_make_ai_provider(), NonMockAIGradingProvider)
    finally:
        if original is None:
            os.environ.pop("AI_MOCK_MODE", None)
        else:
            os.environ["AI_MOCK_MODE"] = original


async def _create_assignment(
    client: httpx.AsyncClient, title: str = "Chapter 3 Quiz"
) -> str:
    resp = await client.post(
        "/grading/assignments",
        headers=_teacher_headers(),
        json={"class_id": "cls_demo_math_1", "title": title},
    )
    assert resp.status_code == 201
    return resp.json()["assignment_id"]


# --- Assignment creation ---


def test_create_assignment_teacher_success() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/grading/assignments",
                headers=_teacher_headers(),
                json={"class_id": "cls_demo_math_1", "title": "Chapter 3 Quiz"},
            )
            assert resp.status_code == 201
            body = resp.json()
            assert body["assignment_id"].startswith("asgn_")
            assert body["class_id"] == "cls_demo_math_1"
            assert body["org_id"] == "org_demo_1"
            assert body["teacher_user_id"] == "usr_teacher_1"
            assert body["title"] == "Chapter 3 Quiz"
            assert body["created_at"]

    asyncio.run(scenario())


def test_create_assignment_unauthenticated() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/grading/assignments",
                json={"class_id": "cls_demo_math_1", "title": "Quiz"},
            )
            assert resp.status_code == 401

    asyncio.run(scenario())


def test_create_assignment_non_teacher_forbidden() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/grading/assignments",
                headers=_non_teacher_headers(),
                json={"class_id": "cls_demo_math_1", "title": "Quiz"},
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


def test_create_assignment_unknown_class_forbidden() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/grading/assignments",
                headers=_teacher_headers(),
                json={"class_id": "cls_unknown", "title": "Quiz"},
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


def test_create_assignment_cross_tenant_class_forbidden() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/grading/assignments",
                headers=_teacher_headers(),
                json={"class_id": "cls_other_org_1", "title": "Quiz"},
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


# --- Artifact upload ---


def test_upload_artifact_jpeg_success() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            resp = await client.post(
                f"/grading/assignments/{assignment_id}/artifacts",
                headers=_teacher_headers(),
                data={"student_id": "stu_demo_1"},
                files={"file": ("homework.jpg", b"fake-image-bytes", "image/jpeg")},
            )
            assert resp.status_code == 201
            body = resp.json()
            assert body["artifact_id"].startswith("artf_")
            assert body["assignment_id"] == assignment_id
            assert body["student_id"] == "stu_demo_1"
            assert body["class_id"] == "cls_demo_math_1"
            assert body["org_id"] == "org_demo_1"
            assert body["teacher_user_id"] == "usr_teacher_1"
            assert body["file_name"] == "homework.jpg"
            assert body["media_type"] == "image/jpeg"
            assert body["storage_key"].startswith("s3://stub/")
            assert body["created_at"]

    asyncio.run(scenario())


def test_upload_artifact_png_success() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            resp = await client.post(
                f"/grading/assignments/{assignment_id}/artifacts",
                headers=_teacher_headers(),
                data={"student_id": "stu_demo_1"},
                files={"file": ("scan.png", b"fake-png-bytes", "image/png")},
            )
            assert resp.status_code == 201
            assert resp.json()["media_type"] == "image/png"

    asyncio.run(scenario())


def test_upload_artifact_pdf_success() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            resp = await client.post(
                f"/grading/assignments/{assignment_id}/artifacts",
                headers=_teacher_headers(),
                data={"student_id": "stu_demo_1"},
                files={"file": ("report.pdf", b"%PDF-fake", "application/pdf")},
            )
            assert resp.status_code == 201
            assert resp.json()["media_type"] == "application/pdf"

    asyncio.run(scenario())


def test_upload_artifact_webp_success() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            resp = await client.post(
                f"/grading/assignments/{assignment_id}/artifacts",
                headers=_teacher_headers(),
                data={"student_id": "stu_demo_1"},
                files={"file": ("photo.webp", b"fake-webp-bytes", "image/webp")},
            )
            assert resp.status_code == 201
            assert resp.json()["media_type"] == "image/webp"

    asyncio.run(scenario())


def test_upload_artifact_gif_success() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            resp = await client.post(
                f"/grading/assignments/{assignment_id}/artifacts",
                headers=_teacher_headers(),
                data={"student_id": "stu_demo_1"},
                files={"file": ("animation.gif", b"GIF89a-fake", "image/gif")},
            )
            assert resp.status_code == 201
            assert resp.json()["media_type"] == "image/gif"

    asyncio.run(scenario())


def test_upload_artifact_rejects_unsupported_format() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            resp = await client.post(
                f"/grading/assignments/{assignment_id}/artifacts",
                headers=_teacher_headers(),
                data={"student_id": "stu_demo_1"},
                files={
                    "file": ("virus.exe", b"MZ\x90\x00", "application/x-msdownload")
                },
            )
            assert resp.status_code == 422
            body = resp.json()
            assert "detail" in body
            assert "Unsupported" in body["detail"]

    asyncio.run(scenario())


def test_upload_artifact_unauthenticated() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/grading/assignments/asgn_1/artifacts",
                data={"student_id": "stu_demo_1"},
                files={"file": ("test.jpg", b"bytes", "image/jpeg")},
            )
            assert resp.status_code == 401

    asyncio.run(scenario())


def test_upload_artifact_non_teacher_forbidden() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/grading/assignments/asgn_1/artifacts",
                headers=_non_teacher_headers(),
                data={"student_id": "stu_demo_1"},
                files={"file": ("test.jpg", b"bytes", "image/jpeg")},
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


def test_upload_artifact_unknown_assignment_forbidden() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/grading/assignments/asgn_unknown/artifacts",
                headers=_teacher_headers(),
                data={"student_id": "stu_demo_1"},
                files={"file": ("test.jpg", b"bytes", "image/jpeg")},
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


def test_upload_artifact_metadata_links_assignment_student_class_org() -> None:
    """AC1: file is stored and retrievable; metadata links to assignment, student, class, org."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            upload_resp = await client.post(
                f"/grading/assignments/{assignment_id}/artifacts",
                headers=_teacher_headers(),
                data={"student_id": "stu_demo_1"},
                files={"file": ("hw.jpg", b"bytes", "image/jpeg")},
            )
            assert upload_resp.status_code == 201
            body = upload_resp.json()
            assert body["assignment_id"] == assignment_id
            assert body["student_id"] == "stu_demo_1"
            assert body["class_id"] == "cls_demo_math_1"
            assert body["org_id"] == "org_demo_1"

    asyncio.run(scenario())


# --- Artifact retrieval ---


def test_get_artifact_success() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            upload_resp = await client.post(
                f"/grading/assignments/{assignment_id}/artifacts",
                headers=_teacher_headers(),
                data={"student_id": "stu_demo_1"},
                files={"file": ("test.jpg", b"bytes", "image/jpeg")},
            )
            artifact_id = upload_resp.json()["artifact_id"]
            get_resp = await client.get(
                f"/grading/assignments/{assignment_id}/artifacts/{artifact_id}",
                headers=_teacher_headers(),
            )
            assert get_resp.status_code == 200
            assert get_resp.json()["artifact_id"] == artifact_id
            assert get_resp.json()["file_name"] == "test.jpg"
            assert get_resp.json()["storage_key"].startswith("s3://stub/")

    asyncio.run(scenario())


def test_get_artifact_unauthenticated() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.get("/grading/assignments/asgn_1/artifacts/artf_1")
            assert resp.status_code == 401

    asyncio.run(scenario())


def test_get_artifact_non_teacher_forbidden() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.get(
                "/grading/assignments/asgn_1/artifacts/artf_1",
                headers=_non_teacher_headers(),
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


def test_get_artifact_fail_closed_unknown() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.get(
                "/grading/assignments/asgn_1/artifacts/artf_unknown",
                headers=_teacher_headers(),
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


# --- List artifacts ---


def test_list_artifacts_for_assignment_success() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            for fname, mt in [("a.jpg", "image/jpeg"), ("b.pdf", "application/pdf")]:
                await client.post(
                    f"/grading/assignments/{assignment_id}/artifacts",
                    headers=_teacher_headers(),
                    data={"student_id": "stu_demo_1"},
                    files={"file": (fname, b"bytes", mt)},
                )
            list_resp = await client.get(
                f"/grading/assignments/{assignment_id}/artifacts",
                headers=_teacher_headers(),
            )
            assert list_resp.status_code == 200
            artifacts = list_resp.json()["artifacts"]
            assert len(artifacts) == 2
            file_names = {a["file_name"] for a in artifacts}
            assert "a.jpg" in file_names
            assert "b.pdf" in file_names

    asyncio.run(scenario())


def test_list_artifacts_unauthenticated() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.get("/grading/assignments/asgn_1/artifacts")
            assert resp.status_code == 401

    asyncio.run(scenario())


def test_list_artifacts_non_teacher_forbidden() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.get(
                "/grading/assignments/asgn_1/artifacts",
                headers=_non_teacher_headers(),
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


def test_list_artifacts_unknown_assignment_forbidden() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.get(
                "/grading/assignments/asgn_unknown/artifacts",
                headers=_teacher_headers(),
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


# --- Grading job submission ---


async def _upload_artifact(client: httpx.AsyncClient, assignment_id: str) -> str:
    resp = await client.post(
        f"/grading/assignments/{assignment_id}/artifacts",
        headers=_teacher_headers(),
        data={"student_id": "stu_demo_1"},
        files={"file": ("homework.jpg", b"fake-bytes", "image/jpeg")},
    )
    assert resp.status_code == 201
    return resp.json()["artifact_id"]


def test_submit_grading_job_success() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            artifact_id = await _upload_artifact(client, assignment_id)
            resp = await client.post(
                f"/grading/assignments/{assignment_id}/grading-jobs",
                headers=_teacher_headers(),
                json={"artifact_id": artifact_id},
            )
            assert resp.status_code == 202
            body = resp.json()
            assert body["job_id"].startswith("gjob_")
            assert body["artifact_id"] == artifact_id
            assert body["assignment_id"] == assignment_id
            assert body["status"] == "pending"
            assert body["attempt_count"] == 0
            assert body["submitted_at"]
            assert body["completed_at"] is None

    asyncio.run(scenario())


def test_submit_grading_job_idempotent() -> None:
    """Two POSTs for the same artifact return the same job_id."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            artifact_id = await _upload_artifact(client, assignment_id)
            resp1 = await client.post(
                f"/grading/assignments/{assignment_id}/grading-jobs",
                headers=_teacher_headers(),
                json={"artifact_id": artifact_id},
            )
            resp2 = await client.post(
                f"/grading/assignments/{assignment_id}/grading-jobs",
                headers=_teacher_headers(),
                json={"artifact_id": artifact_id},
            )
            assert resp1.status_code == 202
            assert resp2.status_code == 202
            assert resp1.json()["job_id"] == resp2.json()["job_id"]

    asyncio.run(scenario())


def test_submit_grading_job_unauthenticated() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/grading/assignments/asgn_1/grading-jobs",
                json={"artifact_id": "artf_1"},
            )
            assert resp.status_code == 401

    asyncio.run(scenario())


def test_submit_grading_job_non_teacher_forbidden() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/grading/assignments/asgn_1/grading-jobs",
                headers=_non_teacher_headers(),
                json={"artifact_id": "artf_1"},
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


def test_submit_grading_job_unknown_artifact_forbidden() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            resp = await client.post(
                f"/grading/assignments/{assignment_id}/grading-jobs",
                headers=_teacher_headers(),
                json={"artifact_id": "artf_does_not_exist"},
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


def test_submit_grading_job_mismatched_assignment_forbidden() -> None:
    """Artifact belonging to a different assignment returns 403 at the API level."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            # Create two separate assignments and upload an artifact to the first
            assignment_id_1 = await _create_assignment(client)
            assignment_id_2 = await _create_assignment(client)
            artifact_id = await _upload_artifact(client, assignment_id_1)
            # Submitting the artifact under the second assignment should be forbidden
            resp = await client.post(
                f"/grading/assignments/{assignment_id_2}/grading-jobs",
                headers=_teacher_headers(),
                json={"artifact_id": artifact_id},
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


# --- Grading job polling ---


def test_get_grading_job_returns_200() -> None:
    """GET grading job returns 200 after submission (background task runs synchronously in ASGI tests)."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            artifact_id = await _upload_artifact(client, assignment_id)
            submit_resp = await client.post(
                f"/grading/assignments/{assignment_id}/grading-jobs",
                headers=_teacher_headers(),
                json={"artifact_id": artifact_id},
            )
            assert submit_resp.status_code == 202
            job_id = submit_resp.json()["job_id"]
            get_resp = await client.get(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}",
                headers=_teacher_headers(),
            )
            assert get_resp.status_code == 200

    asyncio.run(scenario())


def test_get_grading_job_completed() -> None:
    """After background task processes the job, GET returns status 'completed' with result."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            artifact_id = await _upload_artifact(client, assignment_id)
            submit_resp = await client.post(
                f"/grading/assignments/{assignment_id}/grading-jobs",
                headers=_teacher_headers(),
                json={"artifact_id": artifact_id},
            )
            assert submit_resp.status_code == 202
            job_id = submit_resp.json()["job_id"]
            # In httpx.ASGITransport tests, background tasks run synchronously before this
            # coroutine resumes, so the job should already be completed.
            get_resp = await client.get(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}",
                headers=_teacher_headers(),
            )
            assert get_resp.status_code == 200
            body = get_resp.json()
            assert body["status"] == "completed"
            assert body["completed_at"] is not None
            result = body["result"]
            assert result is not None
            assert result["proposed_score"] == "85/100"
            assert "content_accuracy" in result["rubric_mapping"]
            assert result["draft_feedback"]
            assert result["generated_at"]
            assert result["confidence_level"] in ("high", "medium", "low")
            assert isinstance(result["confidence_score"], float)
            assert 0.0 <= result["confidence_score"] <= 1.0
            assert "confidence_reason" in result  # may be None for high confidence
            assert isinstance(result["practice_recommendations"], list)

    asyncio.run(scenario())


def test_get_grading_job_unauthenticated() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.get("/grading/assignments/asgn_1/grading-jobs/gjob_1")
            assert resp.status_code == 401

    asyncio.run(scenario())


def test_get_grading_job_non_teacher_forbidden() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.get(
                "/grading/assignments/asgn_1/grading-jobs/gjob_1",
                headers=_non_teacher_headers(),
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


def test_get_grading_job_unknown_job_forbidden() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            resp = await client.get(
                f"/grading/assignments/{assignment_id}/grading-jobs/gjob_does_not_exist",
                headers=_teacher_headers(),
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


# --- Approval endpoints ---


async def _submit_and_process_job(
    client: httpx.AsyncClient, assignment_id: str, artifact_id: str
) -> str:
    """Submit a grading job and return job_id. BackgroundTasks run synchronously in ASGITransport."""
    resp = await client.post(
        f"/grading/assignments/{assignment_id}/grading-jobs",
        headers=_teacher_headers(),
        json={"artifact_id": artifact_id},
    )
    assert resp.status_code == 202
    return resp.json()["job_id"]


def test_approve_grading_job_success() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            artifact_id = await _upload_artifact(client, assignment_id)
            job_id = await _submit_and_process_job(client, assignment_id, artifact_id)

            resp = await client.post(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/approve",
                headers=_teacher_headers(),
                json={
                    "approved_score": "90/100",
                    "approved_feedback": "Excellent work.",
                },
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["job_id"] == job_id
            assert body["approved_score"] == "90/100"
            assert body["approved_feedback"] == "Excellent work."
            assert body["approver_user_id"] == "usr_teacher_1"
            assert body["approved_at"]
            assert body["version"] == 1

    asyncio.run(scenario())


def test_approve_grading_job_reapproval_increments_version() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            artifact_id = await _upload_artifact(client, assignment_id)
            job_id = await _submit_and_process_job(client, assignment_id, artifact_id)

            await client.post(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/approve",
                headers=_teacher_headers(),
                json={"approved_score": "85/100", "approved_feedback": "Good."},
            )
            resp = await client.post(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/approve",
                headers=_teacher_headers(),
                json={"approved_score": "88/100", "approved_feedback": "Very good."},
            )
            assert resp.status_code == 200
            assert resp.json()["version"] == 2
            assert resp.json()["approved_score"] == "88/100"

    asyncio.run(scenario())


def test_approve_grading_job_unauthenticated() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/grading/assignments/asgn_1/grading-jobs/gjob_1/approve",
                json={"approved_score": "85/100", "approved_feedback": "Good."},
            )
            assert resp.status_code == 401

    asyncio.run(scenario())


def test_approve_grading_job_non_teacher_forbidden() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/grading/assignments/asgn_1/grading-jobs/gjob_1/approve",
                headers=_non_teacher_headers(),
                json={"approved_score": "85/100", "approved_feedback": "Good."},
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


def test_approve_grading_job_not_completed_conflict() -> None:
    """Approving a job still in pending state returns 409."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            artifact_id = await _upload_artifact(client, assignment_id)
            # Create a pending job directly via the repository (bypassing background task)
            from app.domains.grading.router import _grading_service

            assign = _grading_service._repository.get_assignment(assignment_id)
            job_record = _grading_service._repository.create_grading_job(
                artifact_id=artifact_id + "_pending",
                assignment_id=assignment_id,
                org_id=assign.org_id,
                teacher_user_id=assign.teacher_user_id,
            )
            resp = await client.post(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_record.job_id}/approve",
                headers=_teacher_headers(),
                json={"approved_score": "85/100", "approved_feedback": "Good."},
            )
            assert resp.status_code == 409

    asyncio.run(scenario())


def test_get_grade_approval_success() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            artifact_id = await _upload_artifact(client, assignment_id)
            job_id = await _submit_and_process_job(client, assignment_id, artifact_id)

            await client.post(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/approve",
                headers=_teacher_headers(),
                json={"approved_score": "91/100", "approved_feedback": "Well done."},
            )

            resp = await client.get(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/approval",
                headers=_teacher_headers(),
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["approved_score"] == "91/100"
            assert body["version"] == 1

    asyncio.run(scenario())


def test_get_grade_approval_unapproved_forbidden() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            artifact_id = await _upload_artifact(client, assignment_id)
            job_id = await _submit_and_process_job(client, assignment_id, artifact_id)

            resp = await client.get(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/approval",
                headers=_teacher_headers(),
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


def test_list_grade_versions_success() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            artifact_id = await _upload_artifact(client, assignment_id)
            job_id = await _submit_and_process_job(client, assignment_id, artifact_id)

            await client.post(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/approve",
                headers=_teacher_headers(),
                json={"approved_score": "85/100", "approved_feedback": "Good."},
            )

            resp = await client.get(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/versions",
                headers=_teacher_headers(),
            )
            assert resp.status_code == 200
            body = resp.json()
            assert len(body["versions"]) == 1
            assert body["versions"][0]["version"] == 1
            assert body["versions"][0]["approved_score"] == "85/100"
            assert body["versions"][0]["is_approved"] is True

    asyncio.run(scenario())


def test_get_grading_job_with_result_includes_is_approved_field() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            artifact_id = await _upload_artifact(client, assignment_id)
            job_id = await _submit_and_process_job(client, assignment_id, artifact_id)

            # Before approval: is_approved must be False
            resp = await client.get(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}",
                headers=_teacher_headers(),
            )
            assert resp.status_code == 200
            assert resp.json()["is_approved"] is False

            # After approval: is_approved must be True
            await client.post(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/approve",
                headers=_teacher_headers(),
                json={"approved_score": "85/100", "approved_feedback": "Done."},
            )
            resp = await client.get(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}",
                headers=_teacher_headers(),
            )
            assert resp.status_code == 200
            assert resp.json()["is_approved"] is True

    asyncio.run(scenario())


def test_get_grade_approval_unauthenticated() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.get(
                "/grading/assignments/asgn_1/grading-jobs/gjob_1/approval"
            )
            assert resp.status_code == 401

    asyncio.run(scenario())


def test_get_grade_approval_non_teacher_forbidden() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.get(
                "/grading/assignments/asgn_1/grading-jobs/gjob_1/approval",
                headers=_non_teacher_headers(),
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


def test_list_grade_versions_unauthenticated() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.get(
                "/grading/assignments/asgn_1/grading-jobs/gjob_1/versions"
            )
            assert resp.status_code == 401

    asyncio.run(scenario())


def test_list_grade_versions_non_teacher_forbidden() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.get(
                "/grading/assignments/asgn_1/grading-jobs/gjob_1/versions",
                headers=_non_teacher_headers(),
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


# --- Recommendation endpoints ---


async def _submit_approve_and_get_job_id(
    client: httpx.AsyncClient, assignment_id: str, artifact_id: str
) -> str:
    """Submit, process (synchronously via ASGITransport), and approve a grading job. Returns job_id."""
    job_id = await _submit_and_process_job(client, assignment_id, artifact_id)
    resp = await client.post(
        f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/approve",
        headers=_teacher_headers(),
        json={"approved_score": "85/100", "approved_feedback": "Good."},
    )
    assert resp.status_code == 200
    return job_id


def test_submit_recommendation_job_success() -> None:
    """AC1: POST 202, body has rec_job_id/job_id/student_id/status=pending."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            artifact_id = await _upload_artifact(client, assignment_id)
            job_id = await _submit_approve_and_get_job_id(
                client, assignment_id, artifact_id
            )

            resp = await client.post(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/recommendation-jobs",
                headers=_teacher_headers(),
            )
            assert resp.status_code == 202
            body = resp.json()
            assert body["rec_job_id"].startswith("rec_")
            assert body["job_id"] == job_id
            assert body["student_id"] == "stu_demo_1"
            assert (
                body["status"] == "pending"
            )  # Response body reflects pre-background-task state

    asyncio.run(scenario())


def test_submit_recommendation_job_unauthenticated() -> None:
    """AC7: unauthenticated → 401."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/grading/assignments/asgn_1/grading-jobs/gjob_1/recommendation-jobs",
            )
            assert resp.status_code == 401

    asyncio.run(scenario())


def test_submit_recommendation_job_non_teacher_forbidden() -> None:
    """AC7: non-teacher → 403."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/grading/assignments/asgn_1/grading-jobs/gjob_1/recommendation-jobs",
                headers=_non_teacher_headers(),
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


def test_get_recommendation_job_unauthenticated() -> None:
    """AC7: unauthenticated → 401 on GET poll endpoint."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.get(
                "/grading/assignments/asgn_1/grading-jobs/gjob_1/recommendation-jobs/rec_1",
            )
            assert resp.status_code == 401

    asyncio.run(scenario())


def test_get_recommendation_job_non_teacher_forbidden() -> None:
    """AC7: non-teacher → 403 on GET poll endpoint."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.get(
                "/grading/assignments/asgn_1/grading-jobs/gjob_1/recommendation-jobs/rec_1",
                headers=_non_teacher_headers(),
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


def test_confirm_recommendations_unauthenticated() -> None:
    """AC7: unauthenticated → 401 on POST confirm endpoint."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/grading/assignments/asgn_1/grading-jobs/gjob_1/recommendation-jobs/rec_1/confirm",
                json={"topics": []},
            )
            assert resp.status_code == 401

    asyncio.run(scenario())


def test_confirm_recommendations_non_teacher_forbidden() -> None:
    """AC7: non-teacher → 403 on POST confirm endpoint."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/grading/assignments/asgn_1/grading-jobs/gjob_1/recommendation-jobs/rec_1/confirm",
                headers=_non_teacher_headers(),
                json={"topics": []},
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


def test_get_confirmed_recommendations_unauthenticated() -> None:
    """AC7: unauthenticated → 401 on GET confirm endpoint."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.get(
                "/grading/assignments/asgn_1/grading-jobs/gjob_1/recommendation-jobs/rec_1/confirm",
            )
            assert resp.status_code == 401

    asyncio.run(scenario())


def test_get_confirmed_recommendations_non_teacher_forbidden() -> None:
    """AC7: non-teacher → 403 on GET confirm endpoint."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.get(
                "/grading/assignments/asgn_1/grading-jobs/gjob_1/recommendation-jobs/rec_1/confirm",
                headers=_non_teacher_headers(),
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


def test_submit_recommendation_job_not_approved_conflict() -> None:
    """AC3: 409 when grading job not yet approved."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            artifact_id = await _upload_artifact(client, assignment_id)
            # Submit grading job (BackgroundTasks run synchronously → job is completed but NOT approved)
            job_id = await _submit_and_process_job(client, assignment_id, artifact_id)

            resp = await client.post(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/recommendation-jobs",
                headers=_teacher_headers(),
            )
            assert resp.status_code == 409

    asyncio.run(scenario())


def test_submit_recommendation_job_idempotent() -> None:
    """AC1: same rec_job_id on second POST."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            artifact_id = await _upload_artifact(client, assignment_id)
            job_id = await _submit_approve_and_get_job_id(
                client, assignment_id, artifact_id
            )

            resp1 = await client.post(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/recommendation-jobs",
                headers=_teacher_headers(),
            )
            resp2 = await client.post(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/recommendation-jobs",
                headers=_teacher_headers(),
            )
            assert resp1.status_code == 202
            assert resp2.status_code == 202
            assert resp1.json()["rec_job_id"] == resp2.json()["rec_job_id"]

    asyncio.run(scenario())


def test_get_recommendation_job_completed() -> None:
    """AC2: GET returns status=completed, result.topics non-empty."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            artifact_id = await _upload_artifact(client, assignment_id)
            job_id = await _submit_approve_and_get_job_id(
                client, assignment_id, artifact_id
            )

            submit_resp = await client.post(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/recommendation-jobs",
                headers=_teacher_headers(),
            )
            rec_job_id = submit_resp.json()["rec_job_id"]

            resp = await client.get(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/recommendation-jobs/{rec_job_id}",
                headers=_teacher_headers(),
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["status"] == "completed"
            assert body["result"] is not None
            assert len(body["result"]["topics"]) >= 1
            for topic in body["result"]["topics"]:
                assert topic["topic"]
                assert topic["suggestion"]
                assert topic["weakness_signal"]

    asyncio.run(scenario())


def test_get_recommendation_job_is_confirmed_field() -> None:
    """AC5+6: is_confirmed false before confirm, true after confirm."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            artifact_id = await _upload_artifact(client, assignment_id)
            job_id = await _submit_approve_and_get_job_id(
                client, assignment_id, artifact_id
            )

            submit_resp = await client.post(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/recommendation-jobs",
                headers=_teacher_headers(),
            )
            rec_job_id = submit_resp.json()["rec_job_id"]

            resp = await client.get(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/recommendation-jobs/{rec_job_id}",
                headers=_teacher_headers(),
            )
            assert resp.json()["is_confirmed"] is False

            await client.post(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/recommendation-jobs/{rec_job_id}/confirm",
                headers=_teacher_headers(),
                json={
                    "topics": [
                        {"topic": "Content Accuracy", "suggestion": "Review chapter 3."}
                    ]
                },
            )

            resp = await client.get(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/recommendation-jobs/{rec_job_id}",
                headers=_teacher_headers(),
            )
            assert resp.json()["is_confirmed"] is True

    asyncio.run(scenario())


def test_confirm_recommendations_success() -> None:
    """AC4: 200, confirmed_by==usr_teacher_1, topics list present."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            artifact_id = await _upload_artifact(client, assignment_id)
            job_id = await _submit_approve_and_get_job_id(
                client, assignment_id, artifact_id
            )

            submit_resp = await client.post(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/recommendation-jobs",
                headers=_teacher_headers(),
            )
            rec_job_id = submit_resp.json()["rec_job_id"]

            resp = await client.post(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/recommendation-jobs/{rec_job_id}/confirm",
                headers=_teacher_headers(),
                json={
                    "topics": [
                        {"topic": "Content Accuracy", "suggestion": "Review chapter 3."}
                    ]
                },
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["confirmed_by"] == "usr_teacher_1"
            assert body["confirmed_at"]
            assert len(body["topics"]) == 1
            assert body["topics"][0]["topic"] == "Content Accuracy"
            assert body["topics"][0]["weakness_signal"]

    asyncio.run(scenario())


def test_confirm_recommendations_not_completed_conflict() -> None:
    """AC4: 409 when rec_job not yet processed (pending status)."""

    async def scenario() -> None:
        from app.domains.grading.router import _grading_service

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            artifact_id = await _upload_artifact(client, assignment_id)
            # Submit and approve grading job
            job_id = await _submit_approve_and_get_job_id(
                client, assignment_id, artifact_id
            )

            # Create a recommendation job record directly in pending state (bypass background processing)
            # by injecting via the repository before the POST hits the router
            # Since BackgroundTasks are synchronous in tests, we use idempotency to block requeue:
            # First submit a rec job (it runs synchronously → completed). Then test the 409 via
            # a pending rec job injected via the repository.
            rec_record = _grading_service._repository.create_recommendation_job(
                job_id=job_id,
                assignment_id=assignment_id,
                org_id="org_demo_1",
                teacher_user_id="usr_teacher_1",
                student_id="stu_demo_1",
            )
            # rec_record is pending — try to confirm it → 409
            resp = await client.post(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/recommendation-jobs/{rec_record.rec_job_id}/confirm",
                headers=_teacher_headers(),
                json={"topics": []},
            )
            assert resp.status_code == 409

    asyncio.run(scenario())


def test_get_confirmed_recommendations_success() -> None:
    """AC5: GET .../confirm returns the confirmed recommendation record."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            artifact_id = await _upload_artifact(client, assignment_id)
            job_id = await _submit_approve_and_get_job_id(
                client, assignment_id, artifact_id
            )

            submit_resp = await client.post(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/recommendation-jobs",
                headers=_teacher_headers(),
            )
            rec_job_id = submit_resp.json()["rec_job_id"]

            await client.post(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/recommendation-jobs/{rec_job_id}/confirm",
                headers=_teacher_headers(),
                json={
                    "topics": [
                        {"topic": "Content Accuracy", "suggestion": "Review chapter 3."}
                    ]
                },
            )

            resp = await client.get(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/recommendation-jobs/{rec_job_id}/confirm",
                headers=_teacher_headers(),
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["rec_job_id"] == rec_job_id
            assert body["confirmed_by"] == "usr_teacher_1"
            assert body["topics"][0]["weakness_signal"]

    asyncio.run(scenario())


def test_get_confirmed_recommendations_forbidden_when_not_confirmed() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            artifact_id = await _upload_artifact(client, assignment_id)
            job_id = await _submit_approve_and_get_job_id(
                client, assignment_id, artifact_id
            )

            submit_resp = await client.post(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/recommendation-jobs",
                headers=_teacher_headers(),
            )
            rec_job_id = submit_resp.json()["rec_job_id"]

            resp = await client.get(
                f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/recommendation-jobs/{rec_job_id}/confirm",
                headers=_teacher_headers(),
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


# --- Story 5.9: Artifact register, assignment list, download URL ---


def test_register_artifact_success() -> None:
    """POST /grading/assignments/{id}/artifacts/register stores provided storage_key."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            resp = await client.post(
                f"/grading/assignments/{assignment_id}/artifacts/register",
                headers=_teacher_headers(),
                json={
                    "student_id": "stu_demo_1",
                    "storage_key": "orgs/org_demo_1/cls_demo_math_1/stu_demo_1/asgn_1/uuid.jpg",
                    "file_name": "assignment.jpg",
                    "media_type": "image/jpeg",
                },
            )
        assert resp.status_code == 201
        body = resp.json()
        assert body["artifact_id"].startswith("artf_")
        assert body["storage_key"] == "orgs/org_demo_1/cls_demo_math_1/stu_demo_1/asgn_1/uuid.jpg"
        assert body["file_name"] == "assignment.jpg"

    asyncio.run(scenario())


def test_register_artifact_unsupported_media_type_returns_422() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            resp = await client.post(
                f"/grading/assignments/{assignment_id}/artifacts/register",
                headers=_teacher_headers(),
                json={
                    "student_id": "stu_demo_1",
                    "storage_key": "orgs/org_demo_1/cls/stu/asgn/uuid.doc",
                    "file_name": "assignment.doc",
                    "media_type": "application/msword",
                },
            )
        assert resp.status_code == 422

    asyncio.run(scenario())


def test_register_artifact_unknown_assignment_returns_403() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/grading/assignments/asgn_unknown/artifacts/register",
                headers=_teacher_headers(),
                json={
                    "student_id": "stu_demo_1",
                    "storage_key": "orgs/org_demo_1/cls/stu/asgn/uuid.jpg",
                    "file_name": "photo.jpg",
                    "media_type": "image/jpeg",
                },
            )
        assert resp.status_code == 403

    asyncio.run(scenario())


def test_list_assignments_for_class_returns_created_assignments() -> None:
    """GET /grading/assignments?class_id= returns assignments for the teacher's class."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            await _create_assignment(client, title="Quiz 1")
            await _create_assignment(client, title="Quiz 2")
            resp = await client.get(
                "/grading/assignments?class_id=cls_demo_math_1",
                headers=_teacher_headers(),
            )
        assert resp.status_code == 200
        body = resp.json()
        assert "assignments" in body
        titles = [a["title"] for a in body["assignments"]]
        assert "Quiz 1" in titles
        assert "Quiz 2" in titles
        for assignment in body["assignments"]:
            assert "artifact_count" in assignment
            assert isinstance(assignment["artifact_count"], int)

    asyncio.run(scenario())


def test_list_assignments_unknown_class_returns_403() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.get(
                "/grading/assignments?class_id=cls_unknown",
                headers=_teacher_headers(),
            )
        assert resp.status_code == 403

    asyncio.run(scenario())


def test_get_artifact_download_url_stub_returns_stub_key() -> None:
    """For stub-uploaded artifacts, download-url returns the stub storage key."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            artifact_id = await _upload_artifact(client, assignment_id)
            resp = await client.get(
                f"/grading/assignments/{assignment_id}/artifacts/{artifact_id}/download-url",
                headers=_teacher_headers(),
            )
        assert resp.status_code == 200
        body = resp.json()
        assert "url" in body
        # Stub artifacts return the stub key directly
        assert "stub" in body["url"] or body["url"].startswith("s3://")

    asyncio.run(scenario())


def test_get_artifact_download_url_unknown_artifact_returns_403() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            assignment_id = await _create_assignment(client)
            resp = await client.get(
                f"/grading/assignments/{assignment_id}/artifacts/artf_unknown/download-url",
                headers=_teacher_headers(),
            )
        assert resp.status_code == 403

    asyncio.run(scenario())
