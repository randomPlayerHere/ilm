from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class ClassContextRecord:
    class_id: str
    org_id: str
    teacher_user_id: str


@dataclass(frozen=True)
class StudentContextRecord:
    student_id: str
    org_id: str
    teacher_user_id: str
    class_id: str


@dataclass(frozen=True)
class AssignmentRecord:
    assignment_id: str
    class_id: str
    org_id: str
    teacher_user_id: str
    title: str
    created_at: str


@dataclass(frozen=True)
class ArtifactRecord:
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


@dataclass(frozen=True)
class GradingJobRecord:
    job_id: str
    artifact_id: str
    assignment_id: str
    org_id: str
    teacher_user_id: str
    status: str  # pending | processing | completed | failed
    attempt_count: int
    submitted_at: str
    completed_at: str | None


@dataclass(frozen=True)
class GradingResultRecord:
    job_id: str
    proposed_score: str
    rubric_mapping: dict[str, str]
    draft_feedback: str
    generated_at: str


@dataclass(frozen=True)
class GradeApprovalRecord:
    job_id: str
    approved_score: str
    approved_feedback: str
    approver_user_id: str
    approved_at: str
    version: int


@dataclass(frozen=True)
class GradeVersionRecord:
    job_id: str
    version: int
    approved_score: str
    approved_feedback: str
    editor_user_id: str
    edited_at: str
    is_approved: bool


@dataclass(frozen=True)
class RecommendationJobRecord:
    rec_job_id: str
    job_id: str
    assignment_id: str
    org_id: str
    teacher_user_id: str
    student_id: str        # denormalized from artifact at submit time
    status: str            # pending | processing | completed | failed
    attempt_count: int
    submitted_at: str
    completed_at: str | None


@dataclass(frozen=True)
class RecommendationResultRecord:
    rec_job_id: str
    job_id: str
    student_id: str
    topics: list[dict[str, str]]  # [{"topic": str, "suggestion": str, "weakness_signal": str}]
    generated_at: str


@dataclass(frozen=True)
class ConfirmedRecommendationRecord:
    rec_job_id: str
    job_id: str
    student_id: str
    topics: list[dict[str, str]]  # possibly edited by teacher at confirm time
    confirmed_by: str
    confirmed_at: str


class InMemoryGradingRepository:
    _classes: dict[str, ClassContextRecord] = {}
    _students: dict[str, StudentContextRecord] = {}
    _assignments: dict[str, AssignmentRecord] = {}
    _artifacts: dict[str, ArtifactRecord] = {}
    _grading_jobs: dict[str, GradingJobRecord] = {}
    _grading_results: dict[str, GradingResultRecord] = {}
    _artifact_job_index: dict[str, str] = {}  # artifact_id → job_id
    _grade_approvals: dict[str, GradeApprovalRecord] = {}  # job_id → latest approval
    _grade_versions: dict[str, list[GradeVersionRecord]] = {}  # job_id → ordered versions
    _recommendation_jobs: dict[str, RecommendationJobRecord] = {}       # rec_job_id → record
    _recommendation_results: dict[str, RecommendationResultRecord] = {} # rec_job_id → result
    _confirmed_recommendations: dict[str, ConfirmedRecommendationRecord] = {}  # rec_job_id → confirmed
    _job_rec_index: dict[str, str] = {}  # job_id → rec_job_id (idempotency)
    _assignment_seq: int = 0
    _artifact_seq: int = 0
    _job_seq: int = 0
    _approval_seq: int = 0
    _rec_job_seq: int = 0
    _seeded: bool = False

    def __init__(self) -> None:
        self._ensure_seed_data()

    @classmethod
    def _ensure_seed_data(cls) -> None:
        if cls._seeded:
            return
        cls._seeded = True
        cls._classes = {
            "cls_demo_math_1": ClassContextRecord(
                class_id="cls_demo_math_1",
                org_id="org_demo_1",
                teacher_user_id="usr_teacher_1",
            ),
            "cls_demo_science_1": ClassContextRecord(
                class_id="cls_demo_science_1",
                org_id="org_demo_1",
                teacher_user_id="usr_teacher_1",
            ),
            "cls_other_org_1": ClassContextRecord(
                class_id="cls_other_org_1",
                org_id="org_other_1",
                teacher_user_id="usr_teacher_9",
            ),
        }
        cls._students = {
            "stu_demo_1": StudentContextRecord(
                student_id="stu_demo_1",
                org_id="org_demo_1",
                teacher_user_id="usr_teacher_1",
                class_id="cls_demo_math_1",
            ),
            "stu_science_1": StudentContextRecord(
                student_id="stu_science_1",
                org_id="org_demo_1",
                teacher_user_id="usr_teacher_1",
                class_id="cls_demo_science_1",
            ),
            "stu_other_org_1": StudentContextRecord(
                student_id="stu_other_org_1",
                org_id="org_other_1",
                teacher_user_id="usr_teacher_9",
                class_id="cls_other_org_1",
            ),
        }
        cls._assignments = {}
        cls._artifacts = {}
        cls._grading_jobs = {}
        cls._grading_results = {}
        cls._artifact_job_index = {}
        cls._grade_approvals = {}
        cls._grade_versions = {}
        cls._recommendation_jobs = {}
        cls._recommendation_results = {}
        cls._confirmed_recommendations = {}
        cls._job_rec_index = {}
        cls._assignment_seq = 0
        cls._artifact_seq = 0
        cls._job_seq = 0
        cls._approval_seq = 0
        cls._rec_job_seq = 0

    @classmethod
    def reset_state(cls) -> None:
        cls._seeded = False
        cls._ensure_seed_data()

    def get_class_context(self, class_id: str) -> ClassContextRecord | None:
        return self.__class__._classes.get(class_id)

    def get_student_context(self, student_id: str) -> StudentContextRecord | None:
        return self.__class__._students.get(student_id)

    def create_assignment(
        self,
        class_id: str,
        org_id: str,
        teacher_user_id: str,
        title: str,
    ) -> AssignmentRecord:
        self.__class__._assignment_seq += 1
        assignment_id = f"asgn_{self.__class__._assignment_seq}"
        now = datetime.now(UTC).isoformat()
        record = AssignmentRecord(
            assignment_id=assignment_id,
            class_id=class_id,
            org_id=org_id,
            teacher_user_id=teacher_user_id,
            title=title,
            created_at=now,
        )
        self.__class__._assignments[assignment_id] = record
        return record

    def get_assignment(self, assignment_id: str) -> AssignmentRecord | None:
        return self.__class__._assignments.get(assignment_id)

    def create_artifact(
        self,
        assignment_id: str,
        student_id: str,
        class_id: str,
        org_id: str,
        teacher_user_id: str,
        file_name: str,
        media_type: str,
    ) -> ArtifactRecord:
        self.__class__._artifact_seq += 1
        artifact_id = f"artf_{self.__class__._artifact_seq}"
        now = datetime.now(UTC).isoformat()
        storage_key = f"s3://stub/{artifact_id}"
        record = ArtifactRecord(
            artifact_id=artifact_id,
            assignment_id=assignment_id,
            student_id=student_id,
            class_id=class_id,
            org_id=org_id,
            teacher_user_id=teacher_user_id,
            file_name=file_name,
            media_type=media_type,
            storage_key=storage_key,
            created_at=now,
        )
        self.__class__._artifacts[artifact_id] = record
        return record

    def get_artifact(self, artifact_id: str) -> ArtifactRecord | None:
        return self.__class__._artifacts.get(artifact_id)

    def list_artifacts_for_assignment(self, assignment_id: str) -> list[ArtifactRecord]:
        artifacts = [
            a for a in self.__class__._artifacts.values()
            if a.assignment_id == assignment_id
        ]
        artifacts.sort(key=lambda a: a.created_at)
        return artifacts

    # --- Grading job methods ---

    def create_grading_job(
        self,
        artifact_id: str,
        assignment_id: str,
        org_id: str,
        teacher_user_id: str,
    ) -> GradingJobRecord:
        self.__class__._job_seq += 1
        job_id = f"gjob_{self.__class__._job_seq}"
        now = datetime.now(UTC).isoformat()
        record = GradingJobRecord(
            job_id=job_id,
            artifact_id=artifact_id,
            assignment_id=assignment_id,
            org_id=org_id,
            teacher_user_id=teacher_user_id,
            status="pending",
            attempt_count=0,
            submitted_at=now,
            completed_at=None,
        )
        self.__class__._grading_jobs[job_id] = record
        self.__class__._artifact_job_index[artifact_id] = job_id
        return record

    def get_grading_job_by_id(self, job_id: str) -> GradingJobRecord | None:
        return self.__class__._grading_jobs.get(job_id)

    def get_grading_job_for_artifact(self, artifact_id: str) -> GradingJobRecord | None:
        job_id = self.__class__._artifact_job_index.get(artifact_id)
        if job_id is None:
            return None
        return self.__class__._grading_jobs.get(job_id)

    def update_grading_job(
        self,
        job_id: str,
        status: str,
        attempt_count: int,
        completed_at: str | None = None,
    ) -> GradingJobRecord:
        existing = self.__class__._grading_jobs.get(job_id)
        if existing is None:
            raise KeyError(f"Grading job not found: {job_id}")
        updated = GradingJobRecord(
            job_id=existing.job_id,
            artifact_id=existing.artifact_id,
            assignment_id=existing.assignment_id,
            org_id=existing.org_id,
            teacher_user_id=existing.teacher_user_id,
            status=status,
            attempt_count=attempt_count,
            submitted_at=existing.submitted_at,
            completed_at=completed_at,
        )
        self.__class__._grading_jobs[job_id] = updated
        return updated

    def save_grading_result(
        self,
        job_id: str,
        proposed_score: str,
        rubric_mapping: dict[str, str],
        draft_feedback: str,
    ) -> GradingResultRecord:
        now = datetime.now(UTC).isoformat()
        record = GradingResultRecord(
            job_id=job_id,
            proposed_score=proposed_score,
            rubric_mapping=rubric_mapping,
            draft_feedback=draft_feedback,
            generated_at=now,
        )
        self.__class__._grading_results[job_id] = record
        return record

    def get_grading_result(self, job_id: str) -> GradingResultRecord | None:
        return self.__class__._grading_results.get(job_id)

    # --- Grade approval methods ---

    def upsert_grade_approval(
        self,
        job_id: str,
        approved_score: str,
        approved_feedback: str,
        approver_user_id: str,
        version: int,
        approved_at: str,
    ) -> GradeApprovalRecord:
        record = GradeApprovalRecord(
            job_id=job_id,
            approved_score=approved_score,
            approved_feedback=approved_feedback,
            approver_user_id=approver_user_id,
            approved_at=approved_at,
            version=version,
        )
        self.__class__._grade_approvals[job_id] = record
        return record

    def get_grade_approval(self, job_id: str) -> GradeApprovalRecord | None:
        return self.__class__._grade_approvals.get(job_id)

    def append_grade_version(
        self,
        job_id: str,
        version: int,
        approved_score: str,
        approved_feedback: str,
        editor_user_id: str,
        is_approved: bool,
    ) -> GradeVersionRecord:
        now = datetime.now(UTC).isoformat()
        record = GradeVersionRecord(
            job_id=job_id,
            version=version,
            approved_score=approved_score,
            approved_feedback=approved_feedback,
            editor_user_id=editor_user_id,
            edited_at=now,
            is_approved=is_approved,
        )
        self.__class__._grade_versions.setdefault(job_id, []).append(record)
        return record

    def list_grade_versions(self, job_id: str) -> list[GradeVersionRecord]:
        versions = self.__class__._grade_versions.get(job_id, [])
        return sorted(versions, key=lambda v: v.version)

    # --- Recommendation job methods ---

    def create_recommendation_job(
        self,
        job_id: str,
        assignment_id: str,
        org_id: str,
        teacher_user_id: str,
        student_id: str,
    ) -> RecommendationJobRecord:
        self.__class__._rec_job_seq += 1
        rec_job_id = f"rec_{self.__class__._rec_job_seq}"
        now = datetime.now(UTC).isoformat()
        record = RecommendationJobRecord(
            rec_job_id=rec_job_id,
            job_id=job_id,
            assignment_id=assignment_id,
            org_id=org_id,
            teacher_user_id=teacher_user_id,
            student_id=student_id,
            status="pending",
            attempt_count=0,
            submitted_at=now,
            completed_at=None,
        )
        self.__class__._recommendation_jobs[rec_job_id] = record
        self.__class__._job_rec_index[job_id] = rec_job_id
        return record

    def get_recommendation_job_by_id(self, rec_job_id: str) -> RecommendationJobRecord | None:
        return self.__class__._recommendation_jobs.get(rec_job_id)

    def get_recommendation_job_for_grading_job(self, job_id: str) -> RecommendationJobRecord | None:
        rec_job_id = self.__class__._job_rec_index.get(job_id)
        if rec_job_id is None:
            return None
        return self.__class__._recommendation_jobs.get(rec_job_id)

    def update_recommendation_job(
        self,
        rec_job_id: str,
        status: str,
        attempt_count: int,
        completed_at: str | None = None,
    ) -> RecommendationJobRecord:
        existing = self.__class__._recommendation_jobs.get(rec_job_id)
        if existing is None:
            raise KeyError(f"Recommendation job not found: {rec_job_id}")
        updated = RecommendationJobRecord(
            rec_job_id=existing.rec_job_id,
            job_id=existing.job_id,
            assignment_id=existing.assignment_id,
            org_id=existing.org_id,
            teacher_user_id=existing.teacher_user_id,
            student_id=existing.student_id,
            status=status,
            attempt_count=attempt_count,
            submitted_at=existing.submitted_at,
            completed_at=completed_at,
        )
        self.__class__._recommendation_jobs[rec_job_id] = updated
        return updated

    def save_recommendation_result(
        self,
        rec_job_id: str,
        job_id: str,
        student_id: str,
        topics: list[dict[str, str]],
    ) -> RecommendationResultRecord:
        now = datetime.now(UTC).isoformat()
        record = RecommendationResultRecord(
            rec_job_id=rec_job_id,
            job_id=job_id,
            student_id=student_id,
            topics=topics,
            generated_at=now,
        )
        self.__class__._recommendation_results[rec_job_id] = record
        return record

    def get_recommendation_result(self, rec_job_id: str) -> RecommendationResultRecord | None:
        return self.__class__._recommendation_results.get(rec_job_id)

    def upsert_confirmed_recommendation(
        self,
        rec_job_id: str,
        job_id: str,
        student_id: str,
        topics: list[dict[str, str]],
        confirmed_by: str,
        confirmed_at: str,
    ) -> ConfirmedRecommendationRecord:
        record = ConfirmedRecommendationRecord(
            rec_job_id=rec_job_id,
            job_id=job_id,
            student_id=student_id,
            topics=topics,
            confirmed_by=confirmed_by,
            confirmed_at=confirmed_at,
        )
        self.__class__._confirmed_recommendations[rec_job_id] = record
        return record

    def get_confirmed_recommendation(self, rec_job_id: str) -> ConfirmedRecommendationRecord | None:
        return self.__class__._confirmed_recommendations.get(rec_job_id)
