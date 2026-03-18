from __future__ import annotations

import pytest

from app.domains.grading.repository import InMemoryGradingRepository
from app.domains.grading.service import (
    ArtifactFormatError,
    GradingAccessError,
    GradingProcessError,
    GradingService,
    GradingStateError,
)


def setup_function() -> None:
    InMemoryGradingRepository.reset_state()
    GradingService._fail_on_job_ids.clear()


def _make_service() -> GradingService:
    return GradingService(repository=InMemoryGradingRepository())


def _create_demo_assignment(service: GradingService) -> str:
    assignment = service.create_assignment(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        class_id="cls_demo_math_1",
        title="Chapter 3 Quiz",
    )
    return assignment.assignment_id


# --- Assignment creation ---


def test_create_assignment_success() -> None:
    service = _make_service()
    assignment = service.create_assignment(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        class_id="cls_demo_math_1",
        title="Chapter 3 Quiz",
    )
    assert assignment.assignment_id.startswith("asgn_")
    assert assignment.class_id == "cls_demo_math_1"
    assert assignment.org_id == "org_demo_1"
    assert assignment.teacher_user_id == "usr_teacher_1"
    assert assignment.title == "Chapter 3 Quiz"
    assert assignment.created_at


def test_create_assignment_fails_for_unknown_class() -> None:
    service = _make_service()
    try:
        service.create_assignment(
            actor_user_id="usr_teacher_1",
            actor_org_id="org_demo_1",
            class_id="cls_does_not_exist",
            title="Quiz",
        )
        assert False, "Should have raised GradingAccessError"
    except GradingAccessError:
        pass


def test_create_assignment_fails_for_cross_tenant_class() -> None:
    service = _make_service()
    try:
        service.create_assignment(
            actor_user_id="usr_teacher_1",
            actor_org_id="org_demo_1",
            class_id="cls_other_org_1",
            title="Quiz",
        )
        assert False, "Should have raised GradingAccessError"
    except GradingAccessError:
        pass


def test_create_assignment_fails_for_wrong_teacher() -> None:
    service = _make_service()
    try:
        service.create_assignment(
            actor_user_id="usr_teacher_2",
            actor_org_id="org_demo_1",
            class_id="cls_demo_math_1",
            title="Quiz",
        )
        assert False, "Should have raised GradingAccessError"
    except GradingAccessError:
        pass


# --- Artifact creation ---


def test_create_artifact_success_jpeg() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact = service.create_artifact(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        student_id="stu_demo_1",
        file_name="homework.jpg",
        media_type="image/jpeg",
    )
    assert artifact.artifact_id.startswith("artf_")
    assert artifact.assignment_id == assignment_id
    assert artifact.student_id == "stu_demo_1"
    assert artifact.class_id == "cls_demo_math_1"
    assert artifact.org_id == "org_demo_1"
    assert artifact.teacher_user_id == "usr_teacher_1"
    assert artifact.file_name == "homework.jpg"
    assert artifact.media_type == "image/jpeg"
    assert artifact.storage_key.startswith("s3://stub/")
    assert artifact.created_at


def test_create_artifact_success_pdf() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact = service.create_artifact(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        student_id="stu_demo_1",
        file_name="worksheet.pdf",
        media_type="application/pdf",
    )
    assert artifact.media_type == "application/pdf"
    assert artifact.storage_key.startswith("s3://stub/")


def test_create_artifact_success_png() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact = service.create_artifact(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        student_id="stu_demo_1",
        file_name="scan.png",
        media_type="image/png",
    )
    assert artifact.media_type == "image/png"


def test_create_artifact_success_webp() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact = service.create_artifact(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        student_id="stu_demo_1",
        file_name="image.webp",
        media_type="image/webp",
    )
    assert artifact.media_type == "image/webp"


def test_create_artifact_success_gif() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact = service.create_artifact(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        student_id="stu_demo_1",
        file_name="animation.gif",
        media_type="image/gif",
    )
    assert artifact.media_type == "image/gif"


def test_create_artifact_rejects_unsupported_mime_type() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    try:
        service.create_artifact(
            actor_user_id="usr_teacher_1",
            actor_org_id="org_demo_1",
            assignment_id=assignment_id,
            student_id="stu_demo_1",
            file_name="malware.exe",
            media_type="application/x-msdownload",
        )
        assert False, "Should have raised ArtifactFormatError"
    except ArtifactFormatError as exc:
        assert "Unsupported" in str(exc)
        assert "image/jpeg" in str(exc)


def test_create_artifact_rejects_unknown_assignment() -> None:
    service = _make_service()
    try:
        service.create_artifact(
            actor_user_id="usr_teacher_1",
            actor_org_id="org_demo_1",
            assignment_id="asgn_does_not_exist",
            student_id="stu_demo_1",
            file_name="test.jpg",
            media_type="image/jpeg",
        )
        assert False, "Should have raised GradingAccessError"
    except GradingAccessError:
        pass


def test_create_artifact_rejects_cross_tenant_assignment() -> None:
    service = _make_service()
    repo = InMemoryGradingRepository()
    other_assignment = repo.create_assignment(
        class_id="cls_other_org_1",
        org_id="org_other_1",
        teacher_user_id="usr_teacher_9",
        title="Other org assignment",
    )
    try:
        service.create_artifact(
            actor_user_id="usr_teacher_1",
            actor_org_id="org_demo_1",
            assignment_id=other_assignment.assignment_id,
            student_id="stu_demo_1",
            file_name="test.jpg",
            media_type="image/jpeg",
        )
        assert False, "Should have raised GradingAccessError"
    except GradingAccessError:
        pass


def test_create_artifact_rejects_student_in_different_class() -> None:
    """Student stu_science_1 is in cls_demo_science_1, not cls_demo_math_1 — class boundary enforced."""
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    # stu_science_1 is seeded in cls_demo_science_1 (same org/teacher, different class)
    try:
        service.create_artifact(
            actor_user_id="usr_teacher_1",
            actor_org_id="org_demo_1",
            assignment_id=assignment_id,
            student_id="stu_science_1",
            file_name="test.jpg",
            media_type="image/jpeg",
        )
        assert False, "Should have raised GradingAccessError"
    except GradingAccessError:
        pass


def test_create_artifact_rejects_unknown_student() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    try:
        service.create_artifact(
            actor_user_id="usr_teacher_1",
            actor_org_id="org_demo_1",
            assignment_id=assignment_id,
            student_id="stu_does_not_exist",
            file_name="test.jpg",
            media_type="image/jpeg",
        )
        assert False, "Should have raised GradingAccessError"
    except GradingAccessError:
        pass


# --- Artifact retrieval ---


def test_get_artifact_success() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    created = service.create_artifact(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        student_id="stu_demo_1",
        file_name="test.png",
        media_type="image/png",
    )
    fetched = service.get_artifact(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        artifact_id=created.artifact_id,
    )
    assert fetched.artifact_id == created.artifact_id
    assert fetched.file_name == "test.png"
    assert fetched.storage_key.startswith("s3://stub/")


def test_get_artifact_fails_for_unknown_artifact() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    try:
        service.get_artifact(
            actor_user_id="usr_teacher_1",
            actor_org_id="org_demo_1",
            assignment_id=assignment_id,
            artifact_id="artf_does_not_exist",
        )
        assert False, "Should have raised GradingAccessError"
    except GradingAccessError:
        pass


def test_get_artifact_fails_for_wrong_assignment() -> None:
    """Artifact belongs to assignment 1 but is requested via assignment 2 path — fail closed."""
    service = _make_service()
    assignment_id_1 = _create_demo_assignment(service)
    assignment_id_2 = service.create_assignment(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        class_id="cls_demo_math_1",
        title="Second Quiz",
    ).assignment_id
    artifact = service.create_artifact(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id_1,
        student_id="stu_demo_1",
        file_name="test.jpg",
        media_type="image/jpeg",
    )
    try:
        service.get_artifact(
            actor_user_id="usr_teacher_1",
            actor_org_id="org_demo_1",
            assignment_id=assignment_id_2,
            artifact_id=artifact.artifact_id,
        )
        assert False, "Should have raised GradingAccessError"
    except GradingAccessError:
        pass


# --- List artifacts ---


def test_list_artifacts_for_assignment() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    service.create_artifact(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        student_id="stu_demo_1",
        file_name="hw1.jpg",
        media_type="image/jpeg",
    )
    service.create_artifact(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        student_id="stu_demo_1",
        file_name="hw2.pdf",
        media_type="application/pdf",
    )
    artifacts = service.list_artifacts(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
    )
    assert len(artifacts) == 2
    file_names = {a.file_name for a in artifacts}
    assert "hw1.jpg" in file_names
    assert "hw2.pdf" in file_names


def test_list_artifacts_returns_empty_for_new_assignment() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifacts = service.list_artifacts(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
    )
    assert artifacts == []


def test_list_artifacts_fails_for_unknown_assignment() -> None:
    service = _make_service()
    try:
        service.list_artifacts(
            actor_user_id="usr_teacher_1",
            actor_org_id="org_demo_1",
            assignment_id="asgn_unknown",
        )
        assert False, "Should have raised GradingAccessError"
    except GradingAccessError:
        pass


def test_list_artifacts_fails_for_cross_tenant_assignment() -> None:
    """Assignment owned by org_other_1/usr_teacher_9 is inaccessible to org_demo_1/usr_teacher_1."""
    service = _make_service()
    repo = InMemoryGradingRepository()
    other_assignment = repo.create_assignment(
        class_id="cls_other_org_1",
        org_id="org_other_1",
        teacher_user_id="usr_teacher_9",
        title="Other org assignment",
    )
    try:
        service.list_artifacts(
            actor_user_id="usr_teacher_1",
            actor_org_id="org_demo_1",
            assignment_id=other_assignment.assignment_id,
        )
        assert False, "Should have raised GradingAccessError"
    except GradingAccessError:
        pass


def test_metadata_links_artifact_to_assignment_student_class_org() -> None:
    """AC1: metadata links artifact to assignment, student, class, and org."""
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact = service.create_artifact(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        student_id="stu_demo_1",
        file_name="test.jpg",
        media_type="image/jpeg",
    )
    assert artifact.assignment_id == assignment_id
    assert artifact.student_id == "stu_demo_1"
    assert artifact.class_id == "cls_demo_math_1"
    assert artifact.org_id == "org_demo_1"
    assert artifact.teacher_user_id == "usr_teacher_1"


# --- Grading job submission ---


def _create_demo_artifact(service: GradingService, assignment_id: str) -> str:
    artifact = service.create_artifact(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        student_id="stu_demo_1",
        file_name="homework.jpg",
        media_type="image/jpeg",
    )
    return artifact.artifact_id


def test_submit_grading_job_success() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job = service.submit_grading_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        artifact_id=artifact_id,
    )
    assert job.job_id.startswith("gjob_")
    assert job.artifact_id == artifact_id
    assert job.assignment_id == assignment_id
    assert job.status == "pending"
    assert job.attempt_count == 0
    assert job.submitted_at
    assert job.completed_at is None


def test_submit_grading_job_idempotent() -> None:
    """Second submit for the same artifact returns the same job_id."""
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job1 = service.submit_grading_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        artifact_id=artifact_id,
    )
    job2 = service.submit_grading_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        artifact_id=artifact_id,
    )
    assert job1.job_id == job2.job_id


def test_submit_grading_job_unknown_artifact_forbidden() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    with pytest.raises(GradingAccessError):
        service.submit_grading_job(
            actor_user_id="usr_teacher_1",
            actor_org_id="org_demo_1",
            assignment_id=assignment_id,
            artifact_id="artf_does_not_exist",
        )


def test_submit_grading_job_cross_tenant_artifact_forbidden() -> None:
    """Artifact owned by org_other_1 is inaccessible to org_demo_1 actor."""
    service = _make_service()
    # Create assignment and artifact under other org via repo directly
    repo = InMemoryGradingRepository()
    other_assignment = repo.create_assignment(
        class_id="cls_other_org_1",
        org_id="org_other_1",
        teacher_user_id="usr_teacher_9",
        title="Other org quiz",
    )
    other_artifact = repo.create_artifact(
        assignment_id=other_assignment.assignment_id,
        student_id="stu_other_org_1",
        class_id="cls_other_org_1",
        org_id="org_other_1",
        teacher_user_id="usr_teacher_9",
        file_name="other.jpg",
        media_type="image/jpeg",
    )
    with pytest.raises(GradingAccessError):
        service.submit_grading_job(
            actor_user_id="usr_teacher_1",
            actor_org_id="org_demo_1",
            assignment_id=other_assignment.assignment_id,
            artifact_id=other_artifact.artifact_id,
        )


def test_submit_grading_job_mismatched_assignment_forbidden() -> None:
    """Artifact belongs to assignment_1 but request uses assignment_2 — fail closed."""
    service = _make_service()
    assignment_id_1 = _create_demo_assignment(service)
    assignment_id_2 = service.create_assignment(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        class_id="cls_demo_math_1",
        title="Second Quiz",
    ).assignment_id
    artifact_id = _create_demo_artifact(service, assignment_id_1)
    with pytest.raises(GradingAccessError):
        service.submit_grading_job(
            actor_user_id="usr_teacher_1",
            actor_org_id="org_demo_1",
            assignment_id=assignment_id_2,
            artifact_id=artifact_id,
        )


# --- Grading job processing ---


def test_process_grading_job_success() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job = service.submit_grading_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        artifact_id=artifact_id,
    )
    service.process_grading_job(job.job_id)
    job_with_result = service.get_grading_job_status(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job.job_id,
    )
    assert job_with_result.status == "completed"
    assert job_with_result.completed_at is not None
    assert job_with_result.attempt_count == 1
    result = job_with_result.result
    assert result is not None
    assert result.proposed_score == "85/100"
    assert "content_accuracy" in result.rubric_mapping
    assert result.draft_feedback


def test_process_grading_job_idempotent_when_already_completed() -> None:
    """Calling process_grading_job twice on a completed job is a no-op."""
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job = service.submit_grading_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        artifact_id=artifact_id,
    )
    service.process_grading_job(job.job_id)
    # Second call should be a no-op — no error and no duplicate result
    service.process_grading_job(job.job_id)
    job_with_result = service.get_grading_job_status(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job.job_id,
    )
    assert job_with_result.status == "completed"
    assert job_with_result.attempt_count == 1  # not incremented by second call


# --- Grading job status polling ---


def test_get_grading_job_status_success_pending() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job = service.submit_grading_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        artifact_id=artifact_id,
    )
    job_status = service.get_grading_job_status(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job.job_id,
    )
    assert job_status.status == "pending"
    assert job_status.result is None


def test_get_grading_job_status_success_completed() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job = service.submit_grading_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        artifact_id=artifact_id,
    )
    service.process_grading_job(job.job_id)
    job_status = service.get_grading_job_status(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job.job_id,
    )
    assert job_status.status == "completed"
    assert job_status.result is not None
    assert job_status.result.proposed_score == "85/100"
    assert len(job_status.result.rubric_mapping) > 0
    assert job_status.result.draft_feedback


def test_get_grading_job_status_unknown_job_forbidden() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    with pytest.raises(GradingAccessError):
        service.get_grading_job_status(
            actor_user_id="usr_teacher_1",
            actor_org_id="org_demo_1",
            assignment_id=assignment_id,
            job_id="gjob_does_not_exist",
        )


def test_get_grading_job_status_cross_tenant_forbidden() -> None:
    """Job owned by org_other_1 is inaccessible to org_demo_1 actor."""
    service = _make_service()
    repo = InMemoryGradingRepository()
    other_assignment = repo.create_assignment(
        class_id="cls_other_org_1",
        org_id="org_other_1",
        teacher_user_id="usr_teacher_9",
        title="Other org quiz",
    )
    other_artifact = repo.create_artifact(
        assignment_id=other_assignment.assignment_id,
        student_id="stu_other_org_1",
        class_id="cls_other_org_1",
        org_id="org_other_1",
        teacher_user_id="usr_teacher_9",
        file_name="other.jpg",
        media_type="image/jpeg",
    )
    other_job = repo.create_grading_job(
        artifact_id=other_artifact.artifact_id,
        assignment_id=other_assignment.assignment_id,
        org_id="org_other_1",
        teacher_user_id="usr_teacher_9",
    )
    with pytest.raises(GradingAccessError):
        service.get_grading_job_status(
            actor_user_id="usr_teacher_1",
            actor_org_id="org_demo_1",
            assignment_id=other_assignment.assignment_id,
            job_id=other_job.job_id,
        )


# --- Transient error simulation ---


def test_process_grading_job_simulated_failure_sets_status_failed() -> None:
    """Injectable error causes job to transition to 'failed' and raises GradingProcessError."""
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job = service.submit_grading_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        artifact_id=artifact_id,
    )
    GradingService._fail_on_job_ids.add(job.job_id)
    with pytest.raises(GradingProcessError):
        service.process_grading_job(job.job_id)
    job_status = service.get_grading_job_status(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job.job_id,
    )
    assert job_status.status == "failed"
    assert job_status.attempt_count == 1
    assert job_status.result is None


def test_process_grading_job_failed_job_is_idempotent_no_op() -> None:
    """A job already in 'failed' state is skipped (idempotency guard)."""
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job = service.submit_grading_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        artifact_id=artifact_id,
    )
    GradingService._fail_on_job_ids.add(job.job_id)
    with pytest.raises(GradingProcessError):
        service.process_grading_job(job.job_id)
    # Second call must be a no-op (idempotency guard: status == "failed")
    service.process_grading_job(job.job_id)  # should not raise
    job_status = service.get_grading_job_status(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job.job_id,
    )
    assert job_status.attempt_count == 1  # not incremented by second call


# --- Approval gate ---


def _submit_and_process(service: GradingService, assignment_id: str, artifact_id: str) -> str:
    """Submit a grading job and process it; return job_id."""
    job = service.submit_grading_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        artifact_id=artifact_id,
    )
    service.process_grading_job(job.job_id)
    return job.job_id


def test_approve_grading_job_success() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job_id = _submit_and_process(service, assignment_id, artifact_id)

    approval = service.approve_grading_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
        approved_score="90/100",
        approved_feedback="Excellent work.",
    )
    assert approval.job_id == job_id
    assert approval.approved_score == "90/100"
    assert approval.approved_feedback == "Excellent work."
    assert approval.approver_user_id == "usr_teacher_1"
    assert approval.approved_at
    assert approval.version == 1


def test_approve_grading_job_override_score() -> None:
    """Teacher can set a different score than AI proposed."""
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job_id = _submit_and_process(service, assignment_id, artifact_id)

    approval = service.approve_grading_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
        approved_score="75/100",
        approved_feedback="Needs improvement on section 2.",
    )
    assert approval.approved_score == "75/100"
    assert approval.approved_score != "85/100"  # differs from AI proposed_score


def test_approve_grading_job_reapproval_increments_version() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job_id = _submit_and_process(service, assignment_id, artifact_id)

    service.approve_grading_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
        approved_score="85/100",
        approved_feedback="Good.",
    )
    second = service.approve_grading_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
        approved_score="88/100",
        approved_feedback="Very good.",
    )
    assert second.version == 2
    assert second.approved_score == "88/100"


def test_approve_grading_job_fails_if_not_completed() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job = service.submit_grading_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        artifact_id=artifact_id,
    )
    # Job is still "pending" — not yet processed
    with pytest.raises(GradingStateError):
        service.approve_grading_job(
            actor_user_id="usr_teacher_1",
            actor_org_id="org_demo_1",
            assignment_id=assignment_id,
            job_id=job.job_id,
            approved_score="85/100",
            approved_feedback="Good.",
        )


def test_approve_grading_job_cross_tenant_forbidden() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job_id = _submit_and_process(service, assignment_id, artifact_id)

    with pytest.raises(GradingAccessError):
        service.approve_grading_job(
            actor_user_id="usr_teacher_9",
            actor_org_id="org_other_1",
            assignment_id=assignment_id,
            job_id=job_id,
            approved_score="85/100",
            approved_feedback="Good.",
        )


def test_approve_grading_job_unknown_job_forbidden() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    with pytest.raises(GradingAccessError):
        service.approve_grading_job(
            actor_user_id="usr_teacher_1",
            actor_org_id="org_demo_1",
            assignment_id=assignment_id,
            job_id="gjob_does_not_exist",
            approved_score="85/100",
            approved_feedback="Good.",
        )


def test_get_grade_approval_success() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job_id = _submit_and_process(service, assignment_id, artifact_id)
    service.approve_grading_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
        approved_score="90/100",
        approved_feedback="Great.",
    )

    approval = service.get_grade_approval(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
    )
    assert approval.approved_score == "90/100"
    assert approval.version == 1


def test_get_grade_approval_unapproved_returns_forbidden() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job_id = _submit_and_process(service, assignment_id, artifact_id)

    with pytest.raises(GradingAccessError):
        service.get_grade_approval(
            actor_user_id="usr_teacher_1",
            actor_org_id="org_demo_1",
            assignment_id=assignment_id,
            job_id=job_id,
        )


def test_list_grade_versions_after_two_approvals() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job_id = _submit_and_process(service, assignment_id, artifact_id)

    service.approve_grading_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
        approved_score="80/100",
        approved_feedback="First pass.",
    )
    service.approve_grading_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
        approved_score="85/100",
        approved_feedback="Revised.",
    )

    versions = service.list_grade_versions(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
    )
    assert len(versions) == 2
    assert versions[0].version == 1
    assert versions[0].approved_score == "80/100"
    assert versions[1].version == 2
    assert versions[1].approved_score == "85/100"


def test_get_grading_job_status_is_approved_false_before_approval() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job_id = _submit_and_process(service, assignment_id, artifact_id)

    job_status = service.get_grading_job_status(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
    )
    assert job_status.is_approved is False


def test_get_grading_job_status_is_approved_true_after_approval() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job_id = _submit_and_process(service, assignment_id, artifact_id)
    service.approve_grading_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
        approved_score="85/100",
        approved_feedback="Approved.",
    )

    job_status = service.get_grading_job_status(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
    )
    assert job_status.is_approved is True


def test_get_grade_approval_cross_tenant_forbidden() -> None:
    """Job owned by org_demo_1 is inaccessible to a different org actor (AC8)."""
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job_id = _submit_and_process(service, assignment_id, artifact_id)
    service.approve_grading_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
        approved_score="85/100",
        approved_feedback="Good.",
    )

    with pytest.raises(GradingAccessError):
        service.get_grade_approval(
            actor_user_id="usr_teacher_9",
            actor_org_id="org_other_1",
            assignment_id=assignment_id,
            job_id=job_id,
        )


def test_list_grade_versions_cross_tenant_forbidden() -> None:
    """Job owned by org_demo_1 is inaccessible to a different org actor (AC8)."""
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job_id = _submit_and_process(service, assignment_id, artifact_id)

    with pytest.raises(GradingAccessError):
        service.list_grade_versions(
            actor_user_id="usr_teacher_9",
            actor_org_id="org_other_1",
            assignment_id=assignment_id,
            job_id=job_id,
        )


# --- Recommendation jobs ---


def _submit_approve_and_get_job_id(service: GradingService, assignment_id: str, artifact_id: str) -> str:
    """Submit, process, and approve a grading job; return job_id."""
    job_id = _submit_and_process(service, assignment_id, artifact_id)
    service.approve_grading_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
        approved_score="85/100",
        approved_feedback="Good.",
    )
    return job_id


def test_submit_recommendation_job_success() -> None:
    """AC1: rec_job created, status=pending, student_id populated from artifact."""
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job_id = _submit_approve_and_get_job_id(service, assignment_id, artifact_id)

    rec_job = service.submit_recommendation_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
    )
    assert rec_job.rec_job_id.startswith("rec_")
    assert rec_job.job_id == job_id
    assert rec_job.assignment_id == assignment_id
    assert rec_job.student_id == "stu_demo_1"
    assert rec_job.status == "pending"
    assert rec_job.attempt_count == 0
    assert rec_job.submitted_at
    assert rec_job.completed_at is None


def test_submit_recommendation_job_requires_approved_job() -> None:
    """AC3: un-approved job raises GradingStateError."""
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job_id = _submit_and_process(service, assignment_id, artifact_id)

    with pytest.raises(GradingStateError, match="approved"):
        service.submit_recommendation_job(
            actor_user_id="usr_teacher_1",
            actor_org_id="org_demo_1",
            assignment_id=assignment_id,
            job_id=job_id,
        )


def test_submit_recommendation_job_idempotent() -> None:
    """AC1: second call returns same rec_job_id."""
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job_id = _submit_approve_and_get_job_id(service, assignment_id, artifact_id)

    rec_job1 = service.submit_recommendation_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
    )
    rec_job2 = service.submit_recommendation_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
    )
    assert rec_job1.rec_job_id == rec_job2.rec_job_id


def test_submit_recommendation_job_cross_tenant_forbidden() -> None:
    """AC8: cross-tenant actor raises GradingAccessError."""
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job_id = _submit_approve_and_get_job_id(service, assignment_id, artifact_id)

    with pytest.raises(GradingAccessError):
        service.submit_recommendation_job(
            actor_user_id="usr_teacher_9",
            actor_org_id="org_other_1",
            assignment_id=assignment_id,
            job_id=job_id,
        )


def test_submit_recommendation_job_unknown_job_forbidden() -> None:
    """AC8: unknown job_id raises GradingAccessError."""
    service = _make_service()
    assignment_id = _create_demo_assignment(service)

    with pytest.raises(GradingAccessError):
        service.submit_recommendation_job(
            actor_user_id="usr_teacher_1",
            actor_org_id="org_demo_1",
            assignment_id=assignment_id,
            job_id="gjob_does_not_exist",
        )


def test_submit_recommendation_job_forbidden_if_job_artifact_missing() -> None:
    """Defensive check: recommendation submit fails closed if grading job references missing artifact."""
    service = _make_service()
    repo = InMemoryGradingRepository()

    assignment = repo.create_assignment(
        class_id="cls_demo_math_1",
        org_id="org_demo_1",
        teacher_user_id="usr_teacher_1",
        title="Chapter 3 Quiz",
    )
    grading_job = repo.create_grading_job(
        artifact_id="artf_missing",
        assignment_id=assignment.assignment_id,
        org_id="org_demo_1",
        teacher_user_id="usr_teacher_1",
    )
    repo.update_grading_job(
        job_id=grading_job.job_id,
        status="completed",
        attempt_count=1,
    )
    repo.upsert_grade_approval(
        job_id=grading_job.job_id,
        approved_score="85/100",
        approved_feedback="Good.",
        approver_user_id="usr_teacher_1",
        version=1,
        approved_at="2026-03-18T00:00:00+00:00",
    )

    with pytest.raises(GradingAccessError):
        service.submit_recommendation_job(
            actor_user_id="usr_teacher_1",
            actor_org_id="org_demo_1",
            assignment_id=assignment.assignment_id,
            job_id=grading_job.job_id,
        )


def test_process_recommendation_job_generates_topics() -> None:
    """AC2: topics non-empty after processing; each has topic/suggestion/weakness_signal."""
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job_id = _submit_approve_and_get_job_id(service, assignment_id, artifact_id)

    rec_job = service.submit_recommendation_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
    )
    service.process_recommendation_job(rec_job.rec_job_id)

    result = service.get_recommendation_job_status(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
        rec_job_id=rec_job.rec_job_id,
    )
    assert result.status == "completed"
    assert result.result is not None
    assert len(result.result.topics) >= 1
    for topic in result.result.topics:
        assert topic["topic"]
        assert topic["suggestion"]
        assert topic["weakness_signal"]


def test_process_recommendation_job_idempotent_when_completed() -> None:
    """Second process call is a no-op (attempt_count unchanged)."""
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job_id = _submit_approve_and_get_job_id(service, assignment_id, artifact_id)

    rec_job = service.submit_recommendation_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
    )
    service.process_recommendation_job(rec_job.rec_job_id)
    status_after_first = service.get_recommendation_job_status(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
        rec_job_id=rec_job.rec_job_id,
    )
    attempt_count_after_first = status_after_first.attempt_count

    service.process_recommendation_job(rec_job.rec_job_id)
    status_after_second = service.get_recommendation_job_status(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
        rec_job_id=rec_job.rec_job_id,
    )
    assert status_after_second.attempt_count == attempt_count_after_first


def test_get_recommendation_job_status_pending() -> None:
    """Before processing: status=pending, result=None."""
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job_id = _submit_approve_and_get_job_id(service, assignment_id, artifact_id)

    rec_job = service.submit_recommendation_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
    )
    status_obj = service.get_recommendation_job_status(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
        rec_job_id=rec_job.rec_job_id,
    )
    assert status_obj.status == "pending"
    assert status_obj.result is None


def test_get_recommendation_job_status_completed() -> None:
    """After processing: status=completed, result non-None."""
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job_id = _submit_approve_and_get_job_id(service, assignment_id, artifact_id)

    rec_job = service.submit_recommendation_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
    )
    service.process_recommendation_job(rec_job.rec_job_id)
    status_obj = service.get_recommendation_job_status(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
        rec_job_id=rec_job.rec_job_id,
    )
    assert status_obj.status == "completed"
    assert status_obj.result is not None


def test_get_recommendation_job_is_confirmed_false_before_confirm() -> None:
    """AC6: is_confirmed == False before confirmation."""
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job_id = _submit_approve_and_get_job_id(service, assignment_id, artifact_id)

    rec_job = service.submit_recommendation_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
    )
    service.process_recommendation_job(rec_job.rec_job_id)
    status_obj = service.get_recommendation_job_status(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
        rec_job_id=rec_job.rec_job_id,
    )
    assert status_obj.is_confirmed is False


def test_confirm_recommendations_success() -> None:
    """AC4+5: confirmed_by set, confirmed_at non-empty; is_confirmed==True on subsequent GET."""
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job_id = _submit_approve_and_get_job_id(service, assignment_id, artifact_id)

    rec_job = service.submit_recommendation_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
    )
    service.process_recommendation_job(rec_job.rec_job_id)

    confirmed = service.confirm_recommendations(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
        rec_job_id=rec_job.rec_job_id,
        topics=[{"topic": "Content Accuracy", "suggestion": "Review chapter 3."}],
    )
    assert confirmed.confirmed_by == "usr_teacher_1"
    assert confirmed.confirmed_at
    assert confirmed.topics[0]["weakness_signal"]

    status_obj = service.get_recommendation_job_status(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
        rec_job_id=rec_job.rec_job_id,
    )
    assert status_obj.is_confirmed is True


def test_confirm_recommendations_requires_completed_status() -> None:
    """AC4: raises GradingStateError if rec_job not completed."""
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job_id = _submit_approve_and_get_job_id(service, assignment_id, artifact_id)

    rec_job = service.submit_recommendation_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
    )
    # Do NOT process — rec_job is still pending

    with pytest.raises(GradingStateError, match="completed"):
        service.confirm_recommendations(
            actor_user_id="usr_teacher_1",
            actor_org_id="org_demo_1",
            assignment_id=assignment_id,
            job_id=job_id,
            rec_job_id=rec_job.rec_job_id,
            topics=[],
        )


def test_confirm_recommendations_upserts_on_reconfirm() -> None:
    """AC4: second confirm with different topics upserts correctly."""
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job_id = _submit_approve_and_get_job_id(service, assignment_id, artifact_id)

    rec_job = service.submit_recommendation_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
    )
    service.process_recommendation_job(rec_job.rec_job_id)

    service.confirm_recommendations(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
        rec_job_id=rec_job.rec_job_id,
        topics=[{"topic": "Old Topic", "suggestion": "Old suggestion."}],
    )
    confirmed2 = service.confirm_recommendations(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
        rec_job_id=rec_job.rec_job_id,
        topics=[{"topic": "New Topic", "suggestion": "New suggestion."}],
    )
    assert confirmed2.topics[0]["topic"] == "New Topic"


def test_get_recommendation_job_status_cross_tenant_forbidden() -> None:
    """AC8: cross-tenant actor cannot poll another org's recommendation job."""
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job_id = _submit_approve_and_get_job_id(service, assignment_id, artifact_id)

    rec_job = service.submit_recommendation_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
    )

    with pytest.raises(GradingAccessError):
        service.get_recommendation_job_status(
            actor_user_id="usr_teacher_9",
            actor_org_id="org_other_1",
            assignment_id=assignment_id,
            job_id=job_id,
            rec_job_id=rec_job.rec_job_id,
        )


def test_confirm_recommendations_cross_tenant_forbidden() -> None:
    """AC8: cross-tenant actor raises GradingAccessError."""
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job_id = _submit_approve_and_get_job_id(service, assignment_id, artifact_id)

    rec_job = service.submit_recommendation_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
    )
    service.process_recommendation_job(rec_job.rec_job_id)

    with pytest.raises(GradingAccessError):
        service.confirm_recommendations(
            actor_user_id="usr_teacher_9",
            actor_org_id="org_other_1",
            assignment_id=assignment_id,
            job_id=job_id,
            rec_job_id=rec_job.rec_job_id,
            topics=[],
        )


def test_get_confirmed_recommendation_success() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job_id = _submit_approve_and_get_job_id(service, assignment_id, artifact_id)

    rec_job = service.submit_recommendation_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
    )
    service.process_recommendation_job(rec_job.rec_job_id)
    service.confirm_recommendations(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
        rec_job_id=rec_job.rec_job_id,
        topics=[{"topic": "Content Accuracy", "suggestion": "Review chapter 3."}],
    )

    confirmed = service.get_confirmed_recommendation(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
        rec_job_id=rec_job.rec_job_id,
    )
    assert confirmed.rec_job_id == rec_job.rec_job_id
    assert confirmed.confirmed_by == "usr_teacher_1"


def test_get_confirmed_recommendation_forbidden_when_not_confirmed() -> None:
    service = _make_service()
    assignment_id = _create_demo_assignment(service)
    artifact_id = _create_demo_artifact(service, assignment_id)
    job_id = _submit_approve_and_get_job_id(service, assignment_id, artifact_id)

    rec_job = service.submit_recommendation_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
    )
    service.process_recommendation_job(rec_job.rec_job_id)

    with pytest.raises(GradingAccessError):
        service.get_confirmed_recommendation(
            actor_user_id="usr_teacher_1",
            actor_org_id="org_demo_1",
            assignment_id=assignment_id,
            job_id=job_id,
            rec_job_id=rec_job.rec_job_id,
        )
