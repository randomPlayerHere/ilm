from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.domains.auth.dependencies import ActorContext, require_authenticated_actor
from app.domains.students.models import GuardianStudentLink
from app.domains.students.repository import InMemoryStudentsRepository
from app.domains.students.schemas import (
    GuardianStudentLinkCreateRequest,
    GuardianStudentLinkListResponse,
    GuardianStudentLinkResponse,
)

router = APIRouter(prefix="/students", tags=["students"])

_repo = InMemoryStudentsRepository()


def reset_students_state_for_tests() -> None:
    InMemoryStudentsRepository.reset_state()


def _require_teacher(actor: ActorContext) -> None:
    if actor.role != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


def _to_link_response(link: GuardianStudentLink) -> GuardianStudentLinkResponse:
    return GuardianStudentLinkResponse(
        link_id=link.link_id,
        guardian_id=link.guardian_id,
        student_id=link.student_id,
        org_id=link.org_id,
        linked_by=link.linked_by,
        created_at=link.created_at,
    )


@router.post(
    "/{student_id}/guardian-links",
    response_model=GuardianStudentLinkResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_guardian_link(
    student_id: str,
    payload: GuardianStudentLinkCreateRequest,
    actor: ActorContext = Depends(require_authenticated_actor),
) -> GuardianStudentLinkResponse:
    _require_teacher(actor)
    try:
        link = _repo.create_link(
            guardian_id=payload.guardian_id,
            student_id=student_id,
            org_id=actor.org_id,
            linked_by=actor.user_id,
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Guardian-student link already exists")
    return _to_link_response(link)


@router.get(
    "/{student_id}/guardian-links",
    response_model=GuardianStudentLinkListResponse,
)
async def list_guardian_links(
    student_id: str,
    actor: ActorContext = Depends(require_authenticated_actor),
) -> GuardianStudentLinkListResponse:
    _require_teacher(actor)
    links = _repo.get_links_for_student(student_id=student_id, org_id=actor.org_id)
    return GuardianStudentLinkListResponse(links=[_to_link_response(link) for link in links])


@router.delete(
    "/{student_id}/guardian-links/{link_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_guardian_link(
    student_id: str,
    link_id: str,
    actor: ActorContext = Depends(require_authenticated_actor),
) -> Response:
    _require_teacher(actor)
    link = _repo.get_link_by_id(link_id)
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    if link.org_id != actor.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    if link.student_id != student_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    try:
        _repo.delete_link(link_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
