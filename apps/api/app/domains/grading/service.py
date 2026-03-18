from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.domains.grading.repository import (
    ArtifactRecord,
    AssignmentRecord,
    ConfirmedRecommendationRecord,
    GradeApprovalRecord,
    GradeVersionRecord,
    GradingJobRecord,
    GradingResultRecord,
    InMemoryGradingRepository,
    RecommendationJobRecord,
    RecommendationResultRecord,
)

SUPPORTED_MEDIA_TYPES = frozenset({
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "application/pdf",
})

STRONG_RATINGS = frozenset({"exceeds_expectations"})

_RECOMMENDATION_SUGGESTIONS: dict[str, str] = {
    "content_accuracy": (
        "Review foundational concepts in the relevant chapter and complete the "
        "practice exercises before the next assessment."
    ),
    "completeness": (
        "Ensure all rubric sections are fully addressed. Re-read the assignment "
        "prompt and check each criterion before submitting."
    ),
    "presentation": (
        "Practice structuring responses with a clear opening, supporting details, "
        "and a summary conclusion."
    ),
}


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


class GradingProcessError(Exception):
    """Raised by process_grading_job on simulated transient failure."""


class GradingStateError(Exception):
    """Raised when a job is in the wrong state for the requested operation."""


class GradingService:
    _fail_on_job_ids: set[str] = set()  # test-injectable: jobs that should fail

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
        """Run stub AI grading. Called by background task after job submission.

        Raises GradingProcessError for jobs in _fail_on_job_ids (test-injectable transient failure).
        """
        job = self._repository.get_grading_job_by_id(job_id)
        if job is None:
            return
        # Idempotency guard: no-op if already completed or failed
        if job.status in {"completed", "failed"}:
            return

        # Simulated transient error injection for testing
        if job_id in self.__class__._fail_on_job_ids:
            self._repository.update_grading_job(
                job_id=job_id,
                status="failed",
                attempt_count=job.attempt_count + 1,
            )
            raise GradingProcessError(f"Simulated transient error for job {job_id}")

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

        is_approved = self._repository.get_grade_approval(job_id) is not None
        return GradingJobWithResult(
            job_id=job.job_id,
            artifact_id=job.artifact_id,
            assignment_id=job.assignment_id,
            status=job.status,
            attempt_count=job.attempt_count,
            submitted_at=job.submitted_at,
            completed_at=job.completed_at,
            result=result,
            is_approved=is_approved,
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

    # --- Grade approval operations ---

    def approve_grading_job(
        self,
        actor_user_id: str,
        actor_org_id: str,
        assignment_id: str,
        job_id: str,
        approved_score: str,
        approved_feedback: str,
    ) -> GradeApproval:
        job = self._repository.get_grading_job_by_id(job_id)
        if job is None:
            raise GradingAccessError("Forbidden")
        if job.org_id != actor_org_id or job.teacher_user_id != actor_user_id:
            raise GradingAccessError("Forbidden")
        if job.assignment_id != assignment_id:
            raise GradingAccessError("Forbidden")
        if job.status != "completed":
            raise GradingStateError("Job must be completed before approval")

        existing = self._repository.get_grade_approval(job_id)
        new_version = (existing.version + 1) if existing is not None else 1
        now = datetime.now(UTC).isoformat()

        self._repository.append_grade_version(
            job_id=job_id,
            version=new_version,
            approved_score=approved_score,
            approved_feedback=approved_feedback,
            editor_user_id=actor_user_id,
            is_approved=True,
        )
        record = self._repository.upsert_grade_approval(
            job_id=job_id,
            approved_score=approved_score,
            approved_feedback=approved_feedback,
            approver_user_id=actor_user_id,
            version=new_version,
            approved_at=now,
        )
        return self._to_grade_approval(record)

    def get_grade_approval(
        self,
        actor_user_id: str,
        actor_org_id: str,
        assignment_id: str,
        job_id: str,
    ) -> GradeApproval:
        job = self._repository.get_grading_job_by_id(job_id)
        if job is None:
            raise GradingAccessError("Forbidden")
        if job.org_id != actor_org_id or job.teacher_user_id != actor_user_id:
            raise GradingAccessError("Forbidden")
        if job.assignment_id != assignment_id:
            raise GradingAccessError("Forbidden")
        record = self._repository.get_grade_approval(job_id)
        if record is None:
            raise GradingAccessError("Forbidden")
        return self._to_grade_approval(record)

    def list_grade_versions(
        self,
        actor_user_id: str,
        actor_org_id: str,
        assignment_id: str,
        job_id: str,
    ) -> list[GradeVersion]:
        job = self._repository.get_grading_job_by_id(job_id)
        if job is None:
            raise GradingAccessError("Forbidden")
        if job.org_id != actor_org_id or job.teacher_user_id != actor_user_id:
            raise GradingAccessError("Forbidden")
        if job.assignment_id != assignment_id:
            raise GradingAccessError("Forbidden")
        records = self._repository.list_grade_versions(job_id)
        return [self._to_grade_version(r) for r in records]

    def _to_grade_approval(self, record: GradeApprovalRecord) -> GradeApproval:
        return GradeApproval(
            job_id=record.job_id,
            approved_score=record.approved_score,
            approved_feedback=record.approved_feedback,
            approver_user_id=record.approver_user_id,
            approved_at=record.approved_at,
            version=record.version,
        )

    def _to_grade_version(self, record: GradeVersionRecord) -> GradeVersion:
        return GradeVersion(
            job_id=record.job_id,
            version=record.version,
            approved_score=record.approved_score,
            approved_feedback=record.approved_feedback,
            editor_user_id=record.editor_user_id,
            edited_at=record.edited_at,
            is_approved=record.is_approved,
        )

    # --- Recommendation job operations ---

    def submit_recommendation_job(
        self,
        actor_user_id: str,
        actor_org_id: str,
        assignment_id: str,
        job_id: str,
    ) -> RecommendationJob:
        job = self._repository.get_grading_job_by_id(job_id)
        if job is None:
            raise GradingAccessError("Forbidden")
        if job.org_id != actor_org_id or job.teacher_user_id != actor_user_id:
            raise GradingAccessError("Forbidden")
        if job.assignment_id != assignment_id:
            raise GradingAccessError("Forbidden")

        if self._repository.get_grade_approval(job_id) is None:
            raise GradingStateError("Grading job must be approved before generating recommendations")

        existing = self._repository.get_recommendation_job_for_grading_job(job_id)
        if existing is not None:
            return self._to_recommendation_job(existing)

        artifact = self._repository.get_artifact(job.artifact_id)
        if artifact is None:
            raise GradingAccessError("Forbidden")
        student_id = artifact.student_id

        record = self._repository.create_recommendation_job(
            job_id=job_id,
            assignment_id=assignment_id,
            org_id=actor_org_id,
            teacher_user_id=actor_user_id,
            student_id=student_id,
        )
        return self._to_recommendation_job(record)

    def process_recommendation_job(self, rec_job_id: str) -> None:
        """Run stub recommendation generation. Called by background task."""
        rec_job = self._repository.get_recommendation_job_by_id(rec_job_id)
        if rec_job is None:
            return
        if rec_job.status in {"completed", "failed"}:
            return

        updated_rec_job = self._repository.update_recommendation_job(
            rec_job_id=rec_job_id,
            status="processing",
            attempt_count=rec_job.attempt_count + 1,
        )

        grading_result = self._repository.get_grading_result(rec_job.job_id)
        rubric_mapping = grading_result.rubric_mapping if grading_result is not None else {}
        topics = _extract_weakness_topics(rubric_mapping)

        self._repository.save_recommendation_result(
            rec_job_id=rec_job_id,
            job_id=rec_job.job_id,
            student_id=rec_job.student_id,
            topics=topics,
        )

        now = datetime.now(UTC).isoformat()
        self._repository.update_recommendation_job(
            rec_job_id=rec_job_id,
            status="completed",
            attempt_count=updated_rec_job.attempt_count,
            completed_at=now,
        )

    def get_recommendation_job_status(
        self,
        actor_user_id: str,
        actor_org_id: str,
        assignment_id: str,
        job_id: str,
        rec_job_id: str,
    ) -> RecommendationJobWithResult:
        job = self._repository.get_grading_job_by_id(job_id)
        if job is None:
            raise GradingAccessError("Forbidden")
        if job.org_id != actor_org_id or job.teacher_user_id != actor_user_id:
            raise GradingAccessError("Forbidden")
        if job.assignment_id != assignment_id:
            raise GradingAccessError("Forbidden")

        rec_job = self._repository.get_recommendation_job_by_id(rec_job_id)
        if rec_job is None or rec_job.job_id != job_id:
            raise GradingAccessError("Forbidden")

        result: RecommendationResult | None = None
        if rec_job.status == "completed":
            result_record = self._repository.get_recommendation_result(rec_job_id)
            if result_record is not None:
                result = self._to_recommendation_result(result_record)

        is_confirmed = self._repository.get_confirmed_recommendation(rec_job_id) is not None
        return self._to_recommendation_job_with_result(rec_job, result, is_confirmed)

    def confirm_recommendations(
        self,
        actor_user_id: str,
        actor_org_id: str,
        assignment_id: str,
        job_id: str,
        rec_job_id: str,
        topics: list[dict[str, str]],
    ) -> ConfirmedRecommendation:
        job = self._repository.get_grading_job_by_id(job_id)
        if job is None:
            raise GradingAccessError("Forbidden")
        if job.org_id != actor_org_id or job.teacher_user_id != actor_user_id:
            raise GradingAccessError("Forbidden")
        if job.assignment_id != assignment_id:
            raise GradingAccessError("Forbidden")

        rec_job = self._repository.get_recommendation_job_by_id(rec_job_id)
        if rec_job is None or rec_job.job_id != job_id:
            raise GradingAccessError("Forbidden")
        if rec_job.status != "completed":
            raise GradingStateError("Recommendation job must be completed before confirming")

        result_record = self._repository.get_recommendation_result(rec_job_id)
        weakness_signals_by_topic: dict[str, str] = {}
        if result_record is not None:
            for item in result_record.topics:
                weakness_signals_by_topic[item.get("topic", "")] = item.get("weakness_signal", "")

        normalized_topics: list[dict[str, str]] = []
        for item in topics:
            topic_name = item.get("topic", "")
            weakness_signal = item.get("weakness_signal")
            if not weakness_signal:
                weakness_signal = weakness_signals_by_topic.get(topic_name, "teacher_confirmed")
            normalized_topics.append(
                {
                    "topic": topic_name,
                    "suggestion": item.get("suggestion", ""),
                    "weakness_signal": weakness_signal,
                }
            )

        now = datetime.now(UTC).isoformat()
        record = self._repository.upsert_confirmed_recommendation(
            rec_job_id=rec_job_id,
            job_id=job_id,
            student_id=rec_job.student_id,
            topics=normalized_topics,
            confirmed_by=actor_user_id,
            confirmed_at=now,
        )
        return self._to_confirmed_recommendation(record)

    def get_confirmed_recommendation(
        self,
        actor_user_id: str,
        actor_org_id: str,
        assignment_id: str,
        job_id: str,
        rec_job_id: str,
    ) -> ConfirmedRecommendation:
        job = self._repository.get_grading_job_by_id(job_id)
        if job is None:
            raise GradingAccessError("Forbidden")
        if job.org_id != actor_org_id or job.teacher_user_id != actor_user_id:
            raise GradingAccessError("Forbidden")
        if job.assignment_id != assignment_id:
            raise GradingAccessError("Forbidden")

        rec_job = self._repository.get_recommendation_job_by_id(rec_job_id)
        if rec_job is None or rec_job.job_id != job_id:
            raise GradingAccessError("Forbidden")

        record = self._repository.get_confirmed_recommendation(rec_job_id)
        if record is None:
            raise GradingAccessError("Forbidden")

        return self._to_confirmed_recommendation(record)

    def _to_recommendation_job(self, record: RecommendationJobRecord) -> RecommendationJob:
        return RecommendationJob(
            rec_job_id=record.rec_job_id,
            job_id=record.job_id,
            assignment_id=record.assignment_id,
            student_id=record.student_id,
            status=record.status,
            attempt_count=record.attempt_count,
            submitted_at=record.submitted_at,
            completed_at=record.completed_at,
        )

    def _to_recommendation_result(self, record: RecommendationResultRecord) -> RecommendationResult:
        return RecommendationResult(
            rec_job_id=record.rec_job_id,
            job_id=record.job_id,
            student_id=record.student_id,
            topics=record.topics,
            generated_at=record.generated_at,
        )

    def _to_recommendation_job_with_result(
        self,
        record: RecommendationJobRecord,
        result: RecommendationResult | None,
        is_confirmed: bool,
    ) -> RecommendationJobWithResult:
        return RecommendationJobWithResult(
            rec_job_id=record.rec_job_id,
            job_id=record.job_id,
            assignment_id=record.assignment_id,
            student_id=record.student_id,
            status=record.status,
            attempt_count=record.attempt_count,
            submitted_at=record.submitted_at,
            completed_at=record.completed_at,
            result=result,
            is_confirmed=is_confirmed,
        )

    def _to_confirmed_recommendation(self, record: ConfirmedRecommendationRecord) -> ConfirmedRecommendation:
        return ConfirmedRecommendation(
            rec_job_id=record.rec_job_id,
            job_id=record.job_id,
            student_id=record.student_id,
            topics=record.topics,
            confirmed_by=record.confirmed_by,
            confirmed_at=record.confirmed_at,
        )


def _extract_weakness_topics(rubric_mapping: dict[str, str]) -> list[dict[str, str]]:
    """Return practice topics for any dimension that did not exceed expectations."""
    topics = []
    for dimension, rating in rubric_mapping.items():
        if rating not in STRONG_RATINGS:
            topics.append({
                "topic": dimension.replace("_", " ").title(),
                "suggestion": _RECOMMENDATION_SUGGESTIONS.get(
                    dimension,
                    f"Additional practice on {dimension.replace('_', ' ')} is recommended.",
                ),
                "weakness_signal": rating,
            })
    return topics


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
    is_approved: bool = False


@dataclass(frozen=True)
class GradeApproval:
    job_id: str
    approved_score: str
    approved_feedback: str
    approver_user_id: str
    approved_at: str
    version: int


@dataclass(frozen=True)
class GradeVersion:
    job_id: str
    version: int
    approved_score: str
    approved_feedback: str
    editor_user_id: str
    edited_at: str
    is_approved: bool


@dataclass(frozen=True)
class RecommendationJob:
    rec_job_id: str
    job_id: str
    assignment_id: str
    student_id: str
    status: str
    attempt_count: int
    submitted_at: str
    completed_at: str | None


@dataclass(frozen=True)
class RecommendationResult:
    rec_job_id: str
    job_id: str
    student_id: str
    topics: list[dict[str, str]]
    generated_at: str


@dataclass(frozen=True)
class RecommendationJobWithResult:
    rec_job_id: str
    job_id: str
    assignment_id: str
    student_id: str
    status: str
    attempt_count: int
    submitted_at: str
    completed_at: str | None
    result: RecommendationResult | None
    is_confirmed: bool = False


@dataclass(frozen=True)
class ConfirmedRecommendation:
    rec_job_id: str
    job_id: str
    student_id: str
    topics: list[dict[str, str]]
    confirmed_by: str
    confirmed_at: str
