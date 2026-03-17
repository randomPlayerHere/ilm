from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


class LessonDraftGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    class_id: Annotated[str, StringConstraints(min_length=3, max_length=64)]
    unit_title: Annotated[str, StringConstraints(min_length=3, max_length=160)]
    prompt: Annotated[str, StringConstraints(min_length=5, max_length=4_000)]


class LessonDraftResponse(BaseModel):
    draft_id: str
    org_id: str
    teacher_user_id: str
    class_id: str
    unit_title: str
    prompt: str
    generated_outline: list[str]
    suggested_assessments: list[str]
    revision: int
    base_draft_id: str | None
    student_id: str | None
    objectives: list[str]
    pacing_notes: str
    assessments: list[str]
    status: str
    created_at: str
    updated_at: str


class LessonDraftListResponse(BaseModel):
    drafts: list[LessonDraftResponse]


class LessonDraftRevisionResponse(BaseModel):
    revision: int
    objectives: list[str]
    pacing_notes: str
    assessments: list[str]
    updated_by_user_id: str
    updated_at: str


class LessonDraftRevisionListResponse(BaseModel):
    revisions: list[LessonDraftRevisionResponse]


class LessonDraftEditRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objectives: list[Annotated[str, StringConstraints(min_length=1, max_length=300)]] = Field(min_length=1, max_length=20)
    pacing_notes: Annotated[str, StringConstraints(min_length=1, max_length=1_000)]
    assessments: list[Annotated[str, StringConstraints(min_length=1, max_length=300)]] = Field(min_length=1, max_length=20)


class StudentVariantCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    student_id: Annotated[str, StringConstraints(min_length=3, max_length=64)]
    objectives: list[Annotated[str, StringConstraints(min_length=1, max_length=300)]] | None = Field(default=None, min_length=1, max_length=20)
    pacing_notes: Annotated[str, StringConstraints(min_length=1, max_length=1_000)] | None = None
    assessments: list[Annotated[str, StringConstraints(min_length=1, max_length=300)]] | None = Field(default=None, min_length=1, max_length=20)
