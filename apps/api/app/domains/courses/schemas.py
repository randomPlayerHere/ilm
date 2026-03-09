from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


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
    status: str
    created_at: str
    updated_at: str


class LessonDraftListResponse(BaseModel):
    drafts: list[LessonDraftResponse]
