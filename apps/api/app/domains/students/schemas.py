from pydantic import BaseModel, Field


class GuardianStudentLinkCreateRequest(BaseModel):
    guardian_id: str = Field(..., min_length=1)


class GuardianStudentLinkResponse(BaseModel):
    link_id: str
    guardian_id: str
    student_id: str
    org_id: str
    linked_by: str
    created_at: str


class GuardianStudentLinkListResponse(BaseModel):
    links: list[GuardianStudentLinkResponse]
