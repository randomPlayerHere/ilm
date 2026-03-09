from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol


@dataclass(frozen=True)
class ClassContextRecord:
    class_id: str
    org_id: str
    teacher_user_id: str
    title: str
    grade_level: str
    subject: str


@dataclass(frozen=True)
class LessonDraftRecord:
    draft_id: str
    org_id: str
    teacher_user_id: str
    class_id: str
    unit_title: str
    prompt: str
    generated_outline: tuple[str, ...]
    suggested_assessments: tuple[str, ...]
    status: str
    created_at: str
    updated_at: str


class CoursesRepository(Protocol):
    def get_class_context(self, class_id: str) -> ClassContextRecord | None:
        ...

    def create_lesson_draft(
        self,
        org_id: str,
        teacher_user_id: str,
        class_id: str,
        unit_title: str,
        prompt: str,
        generated_outline: list[str],
        suggested_assessments: list[str],
    ) -> LessonDraftRecord:
        ...

    def get_lesson_draft(self, draft_id: str) -> LessonDraftRecord | None:
        ...

    def list_lesson_drafts_for_teacher(self, org_id: str, teacher_user_id: str) -> list[LessonDraftRecord]:
        ...


class InMemoryCoursesRepository:
    _classes: dict[str, ClassContextRecord] = {}
    _drafts: dict[str, LessonDraftRecord] = {}
    _draft_seq: int = 0
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
                title="Grade 6 Mathematics",
                grade_level="6",
                subject="Mathematics",
            ),
            "cls_other_org_1": ClassContextRecord(
                class_id="cls_other_org_1",
                org_id="org_other_1",
                teacher_user_id="usr_teacher_9",
                title="Grade 7 Science",
                grade_level="7",
                subject="Science",
            ),
        }
        cls._drafts = {}
        cls._draft_seq = 0

    @classmethod
    def reset_state(cls) -> None:
        cls._seeded = False
        cls._ensure_seed_data()

    def get_class_context(self, class_id: str) -> ClassContextRecord | None:
        return self.__class__._classes.get(class_id)

    def create_lesson_draft(
        self,
        org_id: str,
        teacher_user_id: str,
        class_id: str,
        unit_title: str,
        prompt: str,
        generated_outline: list[str],
        suggested_assessments: list[str],
    ) -> LessonDraftRecord:
        self.__class__._draft_seq += 1
        draft_id = f"draft_{self.__class__._draft_seq}"
        now = datetime.now(UTC).isoformat()
        record = LessonDraftRecord(
            draft_id=draft_id,
            org_id=org_id,
            teacher_user_id=teacher_user_id,
            class_id=class_id,
            unit_title=unit_title,
            prompt=prompt,
            generated_outline=tuple(generated_outline),
            suggested_assessments=tuple(suggested_assessments),
            status="draft",
            created_at=now,
            updated_at=now,
        )
        self.__class__._drafts[draft_id] = record
        return record

    def get_lesson_draft(self, draft_id: str) -> LessonDraftRecord | None:
        return self.__class__._drafts.get(draft_id)

    def list_lesson_drafts_for_teacher(self, org_id: str, teacher_user_id: str) -> list[LessonDraftRecord]:
        drafts = [
            draft
            for draft in self.__class__._drafts.values()
            if draft.org_id == org_id and draft.teacher_user_id == teacher_user_id
        ]
        drafts.sort(key=lambda draft: draft.created_at)
        return drafts
