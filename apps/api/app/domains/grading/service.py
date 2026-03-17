from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.domains.grading.repository import (
    ArtifactRecord,
    AssignmentRecord,
    GradingJobRecord,
    GradingResultRecord,
    InMemoryGradingRepository,
)

SUPPORTED_MEDIA_TYPES = frozenset({
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "application/pdf",
})


class GradingAccessError(Exception):
    pass


class ArtifactFormatError(Exception):
    pass


@dataclass(frozen=True)
class Assignment:
    assignment_id: str
    class_id: str
    org_id: str
    teacher_user_id: str
    title: str
    created_at: str


@dataclass(frozen=True)
class Artifact:
    artifact_id: str
    assignment_id: str
    student_id: str
    class_id: str
    org_id: str
    teacher_user_id: str
    file_name: str
    media_type: str
    storage_key: str
    created_at: str


class GradingService:
    def __init__(self, repository: InMemoryGradingRepository) -> None:
        self._repository = repository

    def create_assignment(
        self,
        actor_user_id: str,
        actor_org_id: str,
        class_id: str,
        title: str,
    ) -> Assignment:
        class_context = self._repository.get_class_context(class_id)
        if class_context is None:
            raise GradingAccessError("Forbidden")
        if class_context.org_id != actor_org_id:
            raise GradingAccessError("Forbidden")
        if class_context.teacher_user_id != actor_user_id:
            raise GradingAccessError("Forbidden")

        record = self._repository.create_assignment(
            class_id=class_id,
            org_id=actor_org_id,
            teacher_user_id=actor_user_id,
            title=title,
        )
        return self._to_assignment(record)

    def create_artifact(
        self,
        actor_user_id: str,
        actor_org_id: str,
        assignment_id: str,
        student_id: str,
        file_name: str,
        media_type: str,
    ) -> Artifact:
        # Ownership check runs first: unknown/cross-tenant assignments always 403 regardless of payload
        assignment = self._repository.get_assignment(assignment_id)
        if assignment is None:
            raise GradingAccessError("Forbidden")
        if assignment.org_id != actor_org_id or assignment.teacher_user_id != actor_user_id:
            raise GradingAccessError("Forbidden")

        if media_type not in SUPPORTED_MEDIA_TYPES:
            raise ArtifactFormatError(
                f"Unsupported file format: {media_type!r}. "
                f"Supported types: {', '.join(sorted(SUPPORTED_MEDIA_TYPES))}"
            )

        student = self._repository.get_student_context(student_id)
        if student is None:
            raise GradingAccessError("Forbidden")
        if student.org_id != actor_org_id or student.teacher_user_id != actor_user_id:
            raise GradingAccessError("Forbidden")
        if student.class_id != assignment.class_id:
            raise GradingAccessError("Forbidden")

        record = self._repository.create_artifact(
            assignment_id=assignment_id,
            student_id=student_id,
            class_id=assignment.class_id,
            org_id=actor_org_id,
            teacher_user_id=actor_user_id,
            file_name=file_name,
            media_type=media_type,
        )
        return self._to_artifact(record)

    def get_artifact(
        self,
        actor_user_id: str,
        actor_org_id: str,
        assignment_id: str,
        artifact_id: str,
    ) -> Artifact:
        artifact = self._repository.get_artifact(artifact_id)
        if artifact is None:
            raise GradingAccessError("Forbidden")
        if artifact.assignment_id != assignment_id:
            raise GradingAccessError("Forbidden")
        if artifact.org_id != actor_org_id or artifact.teacher_user_id != actor_user_id:
            raise GradingAccessError("Forbidden")
        return self._to_artifact(artifact)

    def list_artifacts(
        self,
        actor_user_id: str,
        actor_org_id: str,
        assignment_id: str,
    ) -> list[Artifact]:
        assignment = self._repository.get_assignment(assignment_id)
        if assignment is None:
            raise GradingAccessError("Forbidden")
        if assignment.org_id != actor_org_id or assignment.teacher_user_id != actor_user_id:
            raise GradingAccessError("Forbidden")
        records = self._repository.list_artifacts_for_assignment(assignment_id)
        return [self._to_artifact(r) for r in records]

    def _to_assignment(self, record: AssignmentRecord) -> Assignment:
        return Assignment(
            assignment_id=record.assignment_id,
            class_id=record.class_id,
            org_id=record.org_id,
            teacher_user_id=record.teacher_user_id,
            title=record.title,
            created_at=record.created_at,
        )

    def _to_artifact(self, record: ArtifactRecord) -> Artifact:
        return Artifact(
            artifact_id=record.artifact_id,
            assignment_id=record.assignment_id,
            student_id=record.student_id,
            class_id=record.class_id,
            org_id=record.org_id,
            teacher_user_id=record.teacher_user_id,
            file_name=record.file_name,
            media_type=record.media_type,
            storage_key=record.storage_key,
            created_at=record.created_at,
        )

    # --- Grading job operations ---

    def submit_grading_job(
        self,
        actor_user_id: str,
        actor_org_id: str,
        assignment_id: str,
        artifact_id: str,
    ) -> GradingJob:
        # Verify artifact ownership — fail-closed 403 on any mismatch
        artifact = self._repository.get_artifact(artifact_id)
        if artifact is None:
            raise GradingAccessError("Forbidden")
        if artifact.org_id != actor_org_id or artifact.teacher_user_id != actor_user_id:
            raise GradingAccessError("Forbidden")
        if artifact.assignment_id != assignment_id:
            raise GradingAccessError("Forbidden")

        # Idempotency: return existing job if one already exists for this artifact
        existing = self._repository.get_grading_job_for_artifact(artifact_id)
        if existing is not None:
            return self._to_grading_job(existing)

        record = self._repository.create_grading_job(
            artifact_id=artifact_id,
            assignment_id=assignment_id,
            org_id=actor_org_id,
            teacher_user_id=actor_user_id,
        )
        return self._to_grading_job(record)

    def process_grading_job(self, job_id: str) -> None:
        """Run stub AI grading. Called by background task after job submission."""
        job = self._repository.get_grading_job_by_id(job_id)
        if job is None:
            return
        # Idempotency guard: no-op if already completed or failed
        if job.status in {"completed", "failed"}:
            return

        updated_job = self._repository.update_grading_job(
            job_id=job_id,
            status="processing",
            attempt_count=job.attempt_count + 1,
        )

        # Stub AI grading output — deterministic for reliable test assertions
        self._repository.save_grading_result(
            job_id=job_id,
            proposed_score="85/100",
            rubric_mapping={
                "content_accuracy": "meets_expectations",
                "presentation": "exceeds_expectations",
                "completeness": "meets_expectations",
            },
            draft_feedback=(
                "Good work overall. Content is accurate and presentation is strong. "
                "Review completeness of answers on section 3."
            ),
        )

        now = datetime.now(UTC).isoformat()
        self._repository.update_grading_job(
            job_id=job_id,
            status="completed",
            attempt_count=updated_job.attempt_count,
            completed_at=now,
        )

    def get_grading_job_status(
        self,
        actor_user_id: str,
        actor_org_id: str,
        assignment_id: str,
        job_id: str,
    ) -> GradingJobWithResult:
        job = self._repository.get_grading_job_by_id(job_id)
        if job is None:
            raise GradingAccessError("Forbidden")
        if job.org_id != actor_org_id or job.teacher_user_id != actor_user_id:
            raise GradingAccessError("Forbidden")
        if job.assignment_id != assignment_id:
            raise GradingAccessError("Forbidden")

        result: GradingResult | None = None
        if job.status == "completed":
            result_record = self._repository.get_grading_result(job_id)
            if result_record is not None:
                result = self._to_grading_result(result_record)

        return GradingJobWithResult(
            job_id=job.job_id,
            artifact_id=job.artifact_id,
            assignment_id=job.assignment_id,
            status=job.status,
            attempt_count=job.attempt_count,
            submitted_at=job.submitted_at,
            completed_at=job.completed_at,
            result=result,
        )

    def _to_grading_job(self, record: GradingJobRecord) -> GradingJob:
        return GradingJob(
            job_id=record.job_id,
            artifact_id=record.artifact_id,
            assignment_id=record.assignment_id,
            status=record.status,
            attempt_count=record.attempt_count,
            submitted_at=record.submitted_at,
            completed_at=record.completed_at,
        )

    def _to_grading_result(self, record: GradingResultRecord) -> GradingResult:
        return GradingResult(
            job_id=record.job_id,
            proposed_score=record.proposed_score,
            rubric_mapping=record.rubric_mapping,
            draft_feedback=record.draft_feedback,
            generated_at=record.generated_at,
        )


@dataclass(frozen=True)
class GradingJob:
    job_id: str
    artifact_id: str
    assignment_id: str
    status: str
    attempt_count: int
    submitted_at: str
    completed_at: str | None


@dataclass(frozen=True)
class GradingResult:
    job_id: str
    proposed_score: str
    rubric_mapping: dict[str, str]
    draft_feedback: str
    generated_at: str


@dataclass(frozen=True)
class GradingJobWithResult:
    job_id: str
    artifact_id: str
    assignment_id: str
    status: str
    attempt_count: int
    submitted_at: str
    completed_at: str | None
    result: GradingResult | None
