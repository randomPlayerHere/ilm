from __future__ import annotations

import pytest

from app.domains.grading.repository import InMemoryGradingRepository
from app.domains.grading.service import ArtifactFormatError, GradingAccessError, GradingService


def setup_function() -> None:
    InMemoryGradingRepository.reset_state()


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
