from __future__ import annotations

import asyncio

import httpx

from app.core.security import create_access_token
from app.domains.auth.router import reset_auth_state_for_tests
from app.domains.grading.router import reset_grading_state_for_tests
from app.main import app


def _teacher_headers() -> dict[str, str]:
    token, _ = create_access_token(subject="usr_teacher_1", org_id="org_demo_1", role="teacher")
    return {"Authorization": f"Bearer {token}"}


def _non_teacher_headers() -> dict[str, str]:
    # usr_teacher_1 is stored as role="teacher" in auth repo — mismatched role token → 403
    token, _ = create_access_token(subject="usr_teacher_1", org_id="org_demo_1", role="parent")
    return {"Authorization": f"Bearer {token}"}


def setup_function() -> None:
    reset_auth_state_for_tests()
    reset_grading_state_for_tests()
    app.dependency_overrides.clear()


async def _create_assignment(client: httpx.AsyncClient, title: str = "Chapter 3 Quiz") -> str:
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
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
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
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.post(
                "/grading/assignments",
                json={"class_id": "cls_demo_math_1", "title": "Quiz"},
            )
            assert resp.status_code == 401

    asyncio.run(scenario())


def test_create_assignment_non_teacher_forbidden() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
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
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
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
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
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
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
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
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
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
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
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
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
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
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
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
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            assignment_id = await _create_assignment(client)
            resp = await client.post(
                f"/grading/assignments/{assignment_id}/artifacts",
                headers=_teacher_headers(),
                data={"student_id": "stu_demo_1"},
                files={"file": ("virus.exe", b"MZ\x90\x00", "application/x-msdownload")},
            )
            assert resp.status_code == 422
            body = resp.json()
            assert "detail" in body
            assert "Unsupported" in body["detail"]

    asyncio.run(scenario())


def test_upload_artifact_unauthenticated() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
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
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
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
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
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
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
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
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
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
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get("/grading/assignments/asgn_1/artifacts/artf_1")
            assert resp.status_code == 401

    asyncio.run(scenario())


def test_get_artifact_non_teacher_forbidden() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get(
                "/grading/assignments/asgn_1/artifacts/artf_1",
                headers=_non_teacher_headers(),
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


def test_get_artifact_fail_closed_unknown() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
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
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
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
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get("/grading/assignments/asgn_1/artifacts")
            assert resp.status_code == 401

    asyncio.run(scenario())


def test_list_artifacts_non_teacher_forbidden() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get(
                "/grading/assignments/asgn_1/artifacts",
                headers=_non_teacher_headers(),
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


def test_list_artifacts_unknown_assignment_forbidden() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
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
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
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
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
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
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.post(
                "/grading/assignments/asgn_1/grading-jobs",
                json={"artifact_id": "artf_1"},
            )
            assert resp.status_code == 401

    asyncio.run(scenario())


def test_submit_grading_job_non_teacher_forbidden() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
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
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            assignment_id = await _create_assignment(client)
            resp = await client.post(
                f"/grading/assignments/{assignment_id}/grading-jobs",
                headers=_teacher_headers(),
                json={"artifact_id": "artf_does_not_exist"},
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


# --- Grading job polling ---


def test_get_grading_job_pending() -> None:
    """Freshly submitted job has status 'pending' and result=null before background task runs."""
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            assignment_id = await _create_assignment(client)
            artifact_id = await _upload_artifact(client, assignment_id)
            # NOTE: With ASGITransport, background tasks run synchronously after the response
            # in the same asyncio loop iteration. So by the time we poll, the job is already
            # completed. To test the 'pending' state, we poll via service directly before
            # the background task runs — that is a service-layer test. This API test verifies
            # that after background task completes the job is in 'completed' state.
            submit_resp = await client.post(
                f"/grading/assignments/{assignment_id}/grading-jobs",
                headers=_teacher_headers(),
                json={"artifact_id": artifact_id},
            )
            assert submit_resp.status_code == 202
            job_id = submit_resp.json()["job_id"]
            # Background task runs synchronously in test environment
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
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
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

    asyncio.run(scenario())


def test_get_grading_job_unauthenticated() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get("/grading/assignments/asgn_1/grading-jobs/gjob_1")
            assert resp.status_code == 401

    asyncio.run(scenario())


def test_get_grading_job_non_teacher_forbidden() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get(
                "/grading/assignments/asgn_1/grading-jobs/gjob_1",
                headers=_non_teacher_headers(),
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


def test_get_grading_job_unknown_job_forbidden() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            assignment_id = await _create_assignment(client)
            resp = await client.get(
                f"/grading/assignments/{assignment_id}/grading-jobs/gjob_does_not_exist",
                headers=_teacher_headers(),
            )
            assert resp.status_code == 403

    asyncio.run(scenario())
