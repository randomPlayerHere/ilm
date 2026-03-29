from __future__ import annotations

from dataclasses import dataclass, field
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
    # Confidence fields (added Story 5.1) — defaults for backward compatibility
    confidence_level: str = "high"  # "high" | "medium" | "low"
    confidence_score: float = 0.9  # 0.0 – 1.0
    confidence_reason: str | None = None
    practice_recommendations: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class GradeApprovalRecord:
    job_id: str
    approved_score: str
    approved_feedback: str
    approver_user_id: str
    approved_at: str
    version: int
    practice_recommendations: list[str] = field(default_factory=list)


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
    student_id: str  # denormalized from artifact at submit time
    status: str  # pending | processing | completed | failed
    attempt_count: int
    submitted_at: str
    completed_at: str | None


@dataclass(frozen=True)
class RecommendationResultRecord:
    rec_job_id: str
    job_id: str
    student_id: str
    topics: list[
        dict[str, str]
    ]  # [{"topic": str, "suggestion": str, "weakness_signal": str}]
    generated_at: str


@dataclass(frozen=True)
class ConfirmedRecommendationRecord:
    rec_job_id: str
    job_id: str
    student_id: str
    topics: list[dict[str, str]]  # possibly edited by teacher at confirm time
    confirmed_by: str
    confirmed_at: str


@dataclass(frozen=True)
class TopicInsightRecord:
    topic: str
    status: str  # always "weakness" in MVP
    weakness_signal: str
    guidance: str  # from topics[].suggestion
    rec_job_id: str  # for client deep-linking
    confirmed_at: str  # ISO 8601; used for de-duplication ordering


@dataclass(frozen=True)
class ApprovedGradeRecord:
    job_id: str
    artifact_id: str
    assignment_id: str
    assignment_title: str
    student_id: str
    approved_score: str
    approved_feedback: str
    approved_at: str
    approver_user_id: str
    version: int
    practice_recommendations: list[str] = field(default_factory=list)


class InMemoryGradingRepository:
    _classes: dict[str, ClassContextRecord] = {}
    _students: dict[str, StudentContextRecord] = {}
    _assignments: dict[str, AssignmentRecord] = {}
    _artifacts: dict[str, ArtifactRecord] = {}
    _grading_jobs: dict[str, GradingJobRecord] = {}
    _grading_results: dict[str, GradingResultRecord] = {}
    _grading_dlq: dict[str, dict[str, str]] = {}
    _artifact_job_index: dict[str, str] = {}  # artifact_id → job_id
    _grade_approvals: dict[str, GradeApprovalRecord] = {}  # job_id → latest approval
    _grade_versions: dict[str, list[GradeVersionRecord]] = (
        {}
    )  # job_id → ordered versions
    _recommendation_jobs: dict[str, RecommendationJobRecord] = {}  # rec_job_id → record
    _recommendation_results: dict[str, RecommendationResultRecord] = (
        {}
    )  # rec_job_id → result
    _confirmed_recommendations: dict[str, ConfirmedRecommendationRecord] = (
        {}
    )  # rec_job_id → confirmed
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
            "usr_student_1": StudentContextRecord(
                student_id="usr_student_1",
                org_id="org_demo_1",
                teacher_user_id="usr_teacher_1",
                class_id="cls_demo_math_1",
            ),
        }
        cls._assignments = {}
        cls._artifacts = {}
        cls._grading_jobs = {}
        cls._grading_results = {}
        cls._grading_dlq = {}
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

    def list_assignments_for_class(
        self, class_id: str, org_id: str
    ) -> list[AssignmentRecord]:
        return [
            a
            for a in self.__class__._assignments.values()
            if a.class_id == class_id and a.org_id == org_id
        ]

    def create_artifact(
        self,
        assignment_id: str,
        student_id: str,
        class_id: str,
        org_id: str,
        teacher_user_id: str,
        file_name: str,
        media_type: str,
        storage_key: str | None = None,
    ) -> ArtifactRecord:
        self.__class__._artifact_seq += 1
        artifact_id = f"artf_{self.__class__._artifact_seq}"
        now = datetime.now(UTC).isoformat()
        if storage_key is None:
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
            a
            for a in self.__class__._artifacts.values()
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
        confidence_level: str = "high",
        confidence_score: float = 0.9,
        confidence_reason: str | None = None,
        practice_recommendations: list[str] | None = None,
    ) -> GradingResultRecord:
        now = datetime.now(UTC).isoformat()
        record = GradingResultRecord(
            job_id=job_id,
            proposed_score=proposed_score,
            rubric_mapping=rubric_mapping,
            draft_feedback=draft_feedback,
            generated_at=now,
            confidence_level=confidence_level,
            confidence_score=confidence_score,
            confidence_reason=confidence_reason,
            practice_recommendations=list(practice_recommendations or []),
        )
        self.__class__._grading_results[job_id] = record
        return record

    def get_grading_result(self, job_id: str) -> GradingResultRecord | None:
        return self.__class__._grading_results.get(job_id)

    def route_grading_job_to_dlq(
        self,
        job_id: str,
        error_code: str,
        reason: str,
    ) -> None:
        self.__class__._grading_dlq[job_id] = {
            "error_code": error_code,
            "reason": reason,
        }

    def is_grading_job_in_dlq(self, job_id: str) -> bool:
        return job_id in self.__class__._grading_dlq

    # --- Grade approval methods ---

    def upsert_grade_approval(
        self,
        job_id: str,
        approved_score: str,
        approved_feedback: str,
        approver_user_id: str,
        version: int,
        approved_at: str,
        practice_recommendations: list[str] | None = None,
    ) -> GradeApprovalRecord:
        record = GradeApprovalRecord(
            job_id=job_id,
            approved_score=approved_score,
            approved_feedback=approved_feedback,
            approver_user_id=approver_user_id,
            approved_at=approved_at,
            version=version,
            practice_recommendations=practice_recommendations if practice_recommendations is not None else [],
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

    def get_recommendation_job_by_id(
        self, rec_job_id: str
    ) -> RecommendationJobRecord | None:
        return self.__class__._recommendation_jobs.get(rec_job_id)

    def get_recommendation_job_for_grading_job(
        self, job_id: str
    ) -> RecommendationJobRecord | None:
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

    def get_recommendation_result(
        self, rec_job_id: str
    ) -> RecommendationResultRecord | None:
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

    def get_confirmed_recommendation(
        self, rec_job_id: str
    ) -> ConfirmedRecommendationRecord | None:
        return self.__class__._confirmed_recommendations.get(rec_job_id)

    def list_approved_grades_for_student(
        self, student_id: str, org_id: str
    ) -> list[ApprovedGradeRecord]:
        student_artifacts = [
            a
            for a in self.__class__._artifacts.values()
            if a.student_id == student_id and a.org_id == org_id
        ]
        results = []
        for artifact in student_artifacts:
            job_id = self.__class__._artifact_job_index.get(artifact.artifact_id)
            if job_id is None:
                continue
            approval = self.__class__._grade_approvals.get(job_id)
            if approval is None:
                continue
            assignment = self.__class__._assignments.get(artifact.assignment_id)
            results.append(
                ApprovedGradeRecord(
                    job_id=job_id,
                    artifact_id=artifact.artifact_id,
                    assignment_id=artifact.assignment_id,
                    assignment_title=(
                        assignment.title if assignment else "[Assignment Not Found]"
                    ),
                    student_id=student_id,
                    approved_score=approval.approved_score,
                    approved_feedback=approval.approved_feedback,
                    approved_at=approval.approved_at,
                    approver_user_id=approval.approver_user_id,
                    version=approval.version,
                    practice_recommendations=approval.practice_recommendations,
                )
            )
        return sorted(
            results, key=lambda r: (datetime.fromisoformat(r.approved_at), r.job_id)
        )

    def list_confirmed_recommendations_for_student(
        self, student_id: str, org_id: str
    ) -> list[ConfirmedRecommendationRecord]:
        results = []
        for rec in self.__class__._confirmed_recommendations.values():
            if rec.student_id != student_id:
                continue
            rec_job = self.__class__._recommendation_jobs.get(rec.rec_job_id)
            if rec_job is None or rec_job.org_id != org_id:
                continue
            results.append(rec)
        return results

    def list_topic_insights_for_student(
        self, student_id: str, org_id: str
    ) -> tuple[list[TopicInsightRecord], bool]:
        # Sufficient-data gate: any approved grade for this student+org?
        has_grade = any(
            (job_id := self.__class__._artifact_job_index.get(a.artifact_id))
            is not None
            and self.__class__._grade_approvals.get(job_id) is not None
            for a in self.__class__._artifacts.values()
            if a.student_id == student_id and a.org_id == org_id
        )
        if not has_grade:
            return [], False

        # Reuse existing org-isolation logic — do NOT duplicate it inline
        recs = self.list_confirmed_recommendations_for_student(student_id, org_id)

        # Flatten topics; keep latest confirmed_at per topic (de-duplicate)
        # Use datetime.fromisoformat() to avoid mixed-offset string misordering (per Story 3.2 lesson)
        # Secondary key rec_job_id ensures stable sort when timestamps are equal
        recs_sorted = sorted(
            recs,
            key=lambda r: (datetime.fromisoformat(r.confirmed_at), r.rec_job_id),
            reverse=True,
        )
        seen_topics: set[str] = set()
        insights: list[TopicInsightRecord] = []
        for rec in recs_sorted:
            for entry in rec.topics:
                topic = entry.get("topic", "")
                if not topic or topic in seen_topics:
                    continue
                seen_topics.add(topic)
                insights.append(
                    TopicInsightRecord(
                        topic=topic,
                        status="weakness",
                        weakness_signal=entry.get("weakness_signal", ""),
                        guidance=entry.get("suggestion", ""),
                        rec_job_id=rec.rec_job_id,
                        confirmed_at=rec.confirmed_at,
                    )
                )
        return insights, True
