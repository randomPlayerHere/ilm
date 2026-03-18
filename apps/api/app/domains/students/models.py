from dataclasses import dataclass


@dataclass(frozen=True)
class GuardianStudentLink:
    link_id: str
    guardian_id: str
    student_id: str
    org_id: str
    linked_by: str
    created_at: str
