from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from app.domains.students.models import GuardianStudentLink


class StudentsRepository(Protocol):
    def create_link(
        self,
        guardian_id: str,
        student_id: str,
        org_id: str,
        linked_by: str,
    ) -> GuardianStudentLink:
        ...

    def get_links_for_guardian(
        self,
        guardian_id: str,
        org_id: str,
    ) -> list[GuardianStudentLink]:
        ...

    def get_links_for_student(
        self,
        student_id: str,
        org_id: str,
    ) -> list[GuardianStudentLink]:
        ...

    def get_link_by_id(self, link_id: str) -> GuardianStudentLink | None:
        ...

    def delete_link(self, link_id: str) -> None:
        ...


class InMemoryStudentsRepository:
    _links: dict[str, GuardianStudentLink] = {}
    _link_seq: int = 1
    _seeded: bool = False

    def __init__(self) -> None:
        self._ensure_seed_data()

    @classmethod
    def _ensure_seed_data(cls) -> None:
        if cls._seeded:
            return
        cls._seeded = True
        cls._links = {}

    @classmethod
    def reset_state(cls) -> None:
        cls._seeded = False
        cls._link_seq = 1
        cls._links = {}
        cls._ensure_seed_data()

    def create_link(
        self,
        guardian_id: str,
        student_id: str,
        org_id: str,
        linked_by: str,
    ) -> GuardianStudentLink:
        for existing in self.__class__._links.values():
            if (
                existing.guardian_id == guardian_id
                and existing.student_id == student_id
                and existing.org_id == org_id
            ):
                raise ValueError("Guardian-student link already exists")
        link_id = f"link_{self.__class__._link_seq}"
        self.__class__._link_seq += 1
        link = GuardianStudentLink(
            link_id=link_id,
            guardian_id=guardian_id,
            student_id=student_id,
            org_id=org_id,
            linked_by=linked_by,
            created_at=datetime.now(UTC).isoformat(),
        )
        self.__class__._links[link_id] = link
        return link

    def get_links_for_guardian(self, guardian_id: str, org_id: str) -> list[GuardianStudentLink]:
        return [link for link in self.__class__._links.values() if link.guardian_id == guardian_id and link.org_id == org_id]

    def get_links_for_student(self, student_id: str, org_id: str) -> list[GuardianStudentLink]:
        return [link for link in self.__class__._links.values() if link.student_id == student_id and link.org_id == org_id]

    def get_link_by_id(self, link_id: str) -> GuardianStudentLink | None:
        return self.__class__._links.get(link_id)

    def delete_link(self, link_id: str) -> None:
        if link_id not in self.__class__._links:
            raise KeyError("Link not found")
        del self.__class__._links[link_id]
