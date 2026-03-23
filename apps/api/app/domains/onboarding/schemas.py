from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


class ClassCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, StringConstraints(min_length=1, max_length=100)]
    subject: Annotated[str, StringConstraints(min_length=1, max_length=100)]


class ClassResponse(BaseModel):
    class_id: str
    org_id: str
    teacher_user_id: str
    name: str
    subject: str
    join_code: str
    student_count: int
    created_at: str


class ClassListResponse(BaseModel):
    classes: list[ClassResponse]


class StudentCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, StringConstraints(min_length=1, max_length=200)]
    grade_level: Annotated[str, StringConstraints(min_length=1, max_length=50)]


class StudentResponse(BaseModel):
    student_id: str
    name: str
    grade_level: str
    org_id: str
    created_at: str


class RosterResponse(BaseModel):
    class_id: str
    students: list[StudentResponse]


class CsvImportRowResult(BaseModel):
    row: int
    success: bool
    student_name: str | None
    error: str | None


class CsvImportResponse(BaseModel):
    total_rows: int
    successful: int
    failed: int
    results: list[CsvImportRowResult]


class InviteLinkResponse(BaseModel):
    invite_id: str
    token: str
    url: str          # "ilm://invite/{token}"
    student_id: str
    expires_at: str


class InviteLinkResolveResponse(BaseModel):
    valid: bool
    reason: str | None  # "already_used" | "expired" | None (if valid=True)
    student_name: str | None
    class_name: str | None
    subject: str | None


class JoinCodeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    join_code: Annotated[str, StringConstraints(min_length=1, max_length=6, strip_whitespace=True)]


class JoinCodeResponse(BaseModel):
    class_id: str
    class_name: str
    subject: str


class GuardianStudentLinkResponse(BaseModel):
    link_id: str
    student_id: str
    student_name: str
