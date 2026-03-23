# Story 4.10: COPPA Consent Confirmation Gate

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an admin,
I want to confirm that parental consent has been collected before activating accounts for children under 13,
so that the platform meets COPPA compliance requirements.

## Acceptance Criteria

**AC1 — Under-13 detection and consent gate**
Given a student is flagged as under 13 (based on grade level: Kindergarten through Grade/Year 7)
When an admin has not confirmed parental consent for that student
Then the student record carries `consent_status = "pending"`
And `GET /onboarding/parent/children` returns the child with `consent_status = "pending"` (visible gate for parent app)

**AC2 — Admin consent confirmation**
Given an admin views a student requiring consent confirmation (consent_status = "pending")
When they call `POST /admin/organizations/{org_id}/students/{student_id}/consent`
Then the consent status is updated to "confirmed"
And the response includes admin identity (`confirmed_by`) and timestamp (`confirmed_at`)

**AC3 — Auditable consent record**
Given consent has been confirmed
When the consent record is queried
Then the confirmation is auditable with actor (admin user_id), timestamp (ISO 8601 UTC), and student identity
And the consent status is visible via `GET /admin/organizations/{org_id}/students/pending-consent`

## Tasks / Subtasks

- [x] Task 1: Extend StudentRecord with consent fields and detection logic (AC: #1)
  - [x] 1.1 Add `consent_status: str = "not_required"`, `consent_confirmed_by: str | None = None`, `consent_confirmed_at: str | None = None` to `StudentRecord` in `apps/api/app/domains/onboarding/models.py` — see exact dataclass pattern in Dev Notes
  - [x] 1.2 Add `import dataclasses` and `_requires_parental_consent(grade_level: str) -> bool` helper in `apps/api/app/domains/onboarding/repository.py` — see exact implementation in Dev Notes (helper lives in repository, NOT service)
  - [x] 1.3 Update `InMemoryOnboardingRepository.get_or_create_student()` in `apps/api/app/domains/onboarding/repository.py` to set `consent_status = "pending"` when `_requires_parental_consent(grade_level)` returns True — see exact placement in Dev Notes

- [x] Task 2: Add repository methods for consent operations (AC: #2, #3)
  - [x] 2.1 Add `list_students_for_org(org_id: str) -> list[StudentRecord]` to `OnboardingRepository` Protocol and `InMemoryOnboardingRepository` in `apps/api/app/domains/onboarding/repository.py`
  - [x] 2.2 Add `confirm_student_consent(student_id: str, confirmed_by: str, confirmed_at: str) -> StudentRecord` to Protocol and implementation — see exact `dataclasses.replace()` pattern in Dev Notes

- [x] Task 3: Add consent_status to parent children response (AC: #1)
  - [x] 3.1 Add `consent_status: str` field to `LinkedChildResponse` Pydantic schema in `apps/api/app/domains/onboarding/schemas.py`
  - [x] 3.2 Update `get_linked_children()` in `apps/api/app/domains/onboarding/service.py` to include `consent_status` from student record — use `student.name` (NOT `student.student_name`) and `student.consent_status`
  - [x] 3.3 Update `LinkedChildResponse` in `packages/contracts/src/onboarding.ts` to add `consent_status: string`
  - [x] 3.4 Do NOT add `consent_status` to `StudentResponse` — teacher roster view intentionally omits consent status in this story

- [x] Task 4: Extend AdminService with consent operations (AC: #2, #3)
  - [x] 4.1 Add `onboarding_repository: InMemoryOnboardingRepository` parameter to `AdminService.__init__()` in `apps/api/app/domains/admin/service.py` — see exact pattern in Dev Notes
  - [x] 4.2 Add `confirm_consent(student_id, admin_user_id, org_id) -> ConsentConfirmed` method to `AdminService` — must raise for BOTH `"confirmed"` AND `"not_required"` statuses
  - [x] 4.3 Add `list_students_pending_consent(org_id: str) -> list[StudentConsentSummary]` method to `AdminService`
  - [x] 4.4 Add `ConsentConfirmed`, `StudentConsentSummary` dataclasses to `apps/api/app/domains/admin/service.py`
  - [x] 4.5 Add `StudentNotFoundForConsentError` and `ConsentAlreadyConfirmedError` exception classes

- [x] Task 5: Add consent endpoints to admin router (AC: #2, #3)
  - [x] 5.1 Add `ConsentConfirmResponse`, `StudentConsentSummaryResponse`, `PendingConsentListResponse` to `apps/api/app/domains/admin/schemas.py`
  - [x] 5.2 Update `_admin_service` singleton in `apps/api/app/domains/admin/router.py` to pass `InMemoryOnboardingRepository()` — see exact pattern in Dev Notes
  - [x] 5.3 Update `reset_admin_state_for_tests()` to call `InMemoryOnboardingRepository.reset_state()` directly — do NOT import from `onboarding.router` (circular import risk)
  - [x] 5.4 Add `POST /admin/organizations/{org_id}/students/{student_id}/consent` endpoint — admin-only, org-scoped
  - [x] 5.5 Add `GET /admin/organizations/{org_id}/students/pending-consent` endpoint — admin-only, org-scoped

- [x] Task 6: Tests and typecheck (AC: all)
  - [x] 6.1 Add consent tests to `apps/api/tests/test_admin_api.py` — see exact test scenarios in Dev Notes
  - [x] 6.2 Update `GET /onboarding/parent/children` tests in `apps/api/tests/test_onboarding_api.py` to assert `consent_status` field is present in each child in the response
  - [x] 6.3 Run `pnpm typecheck` — zero TypeScript errors required
  - [x] 6.4 Run `python -m pytest apps/api/tests/ -v` — all tests must pass

## Dev Notes

### Overview

This story adds COPPA parental consent tracking to the platform. The consent gate is **entirely backend**. No mobile screen changes — the parent app already handles `LinkedChildResponse`; adding `consent_status` allows it to show a "Consent pending" banner (mobile implementation is not in scope for this story). Admin web UI is Epic 9. Full data-access blocking (denying API calls for unconsented students) is Epic 11 Story 11.5.

**Scope boundary**: Implements consent record creation + admin confirmation + audit visibility only. Does NOT block login for parent/student auth users — that is Epic 11.5.

**Do NOT add `consent_status` to `StudentResponse`** — teacher roster view is out of scope for consent visibility. Adding it would expand scope into teacher UX and TypeScript contract changes beyond what's needed.

---

### Task 1 Detail: StudentRecord Consent Fields and Detection Logic

#### Step 1.1 — Extend StudentRecord (`onboarding/models.py`)

`StudentRecord` is a frozen dataclass. Fields with defaults MUST come after fields without defaults:

```python
@dataclass(frozen=True)
class StudentRecord:
    student_id: str      # e.g., "stu_1"
    org_id: str
    name: str            # full name, e.g., "Jane Smith"
    grade_level: str     # e.g., "Grade 5", "Year 7", "10th Grade", "Grade K"
    created_at: str
    consent_status: str = "not_required"   # "not_required" | "pending" | "confirmed"
    consent_confirmed_by: str | None = None
    consent_confirmed_at: str | None = None
```

#### Step 1.2 — Grade level under-13 detection in `repository.py`

> **CRITICAL PLACEMENT**: This helper goes in `apps/api/app/domains/onboarding/repository.py`, NOT in `service.py`. It must be in `repository.py` because `InMemoryOnboardingRepository.get_or_create_student()` (where StudentRecord is created) lives in the repository. Putting it in service.py would require a service→repository circular import or code duplication.

Add at the top of `repository.py` (after imports, before `_generate_join_code`):

```python
import dataclasses
import re

_KINDERGARTEN_KEYWORDS: frozenset[str] = frozenset({"k", "kg", "kindergarten", "kinder"})

def _requires_parental_consent(grade_level: str) -> bool:
    """Return True if the grade level indicates the student may be under 13 (COPPA threshold).

    COPPA conservative: unknown grade formats return True (safer than missing a minor).
    Handles: "K", "KG", "Kindergarten", "Grade K", "Grade 5", "Year 7", "10th Grade", etc.
    """
    gl = grade_level.lower().strip()
    # Split on spaces, hyphens, slashes — handle "Grade K", "Year K", "K-2", "Grade-5"
    tokens = re.split(r"[\s\-/]+", gl)
    for token in tokens:
        token_clean = re.sub(r"[^a-z0-9]", "", token)
        if token_clean in _KINDERGARTEN_KEYWORDS:
            return True
        # Numeric token: grade <= 7 is under 13
        if token_clean.isdigit() and int(token_clean) <= 7:
            return True
    # No numeric or kindergarten token found — COPPA conservative default: treat as requiring consent
    return True
```

> **Why `return True` as default**: COPPA requires erring on the side of caution. If a grade level string is unrecognizable (e.g., "Advanced", "Honors"), it's safer to flag for consent than to miss a minor. If this causes false positives for clearly adult contexts, those students can be handled by the admin confirming or ignoring the pending status.

#### Step 1.3 — Update `InMemoryOnboardingRepository.get_or_create_student()` (`repository.py`)

The existing method (lines ~129–144) creates `StudentRecord` without consent fields. Update the record creation block only — do NOT change the dedup check at the top:

```python
def get_or_create_student(self, org_id: str, name: str, grade_level: str) -> StudentRecord:
    # Reuse student if same name+grade already exists in org (idempotent CSV imports)
    for student in self.__class__._students.values():
        if student.org_id == org_id and student.name == name and student.grade_level == grade_level:
            return student
    student_id = f"stu_{self.__class__._student_seq}"
    self.__class__._student_seq += 1
    consent_status = "pending" if _requires_parental_consent(grade_level) else "not_required"
    record = StudentRecord(
        student_id=student_id,
        org_id=org_id,
        name=name,
        grade_level=grade_level,
        created_at=datetime.now(UTC).isoformat(),
        consent_status=consent_status,
    )
    self.__class__._students[student_id] = record
    return record
```

---

### Task 2 Detail: Repository Consent Methods

#### Step 2.1 — `list_students_for_org`

Add to **both** Protocol and `InMemoryOnboardingRepository`:

```python
# Protocol:
def list_students_for_org(self, org_id: str) -> list[StudentRecord]: ...

# InMemoryOnboardingRepository:
def list_students_for_org(self, org_id: str) -> list[StudentRecord]:
    return [s for s in self.__class__._students.values() if s.org_id == org_id]
```

#### Step 2.2 — `confirm_student_consent`

Uses `dataclasses.replace()` (already imported in Step 1.2). Note: existing code in this file uses full constructor re-instantiation (see `accept_invite_link`). `dataclasses.replace()` is cleaner and preferred for this new method:

```python
# Protocol:
def confirm_student_consent(self, student_id: str, confirmed_by: str, confirmed_at: str) -> StudentRecord: ...

# InMemoryOnboardingRepository:
def confirm_student_consent(
    self, student_id: str, confirmed_by: str, confirmed_at: str
) -> StudentRecord:
    student = self.__class__._students.get(student_id)
    if student is None:
        raise KeyError(f"Student not found: {student_id}")
    updated = dataclasses.replace(
        student,
        consent_status="confirmed",
        consent_confirmed_by=confirmed_by,
        consent_confirmed_at=confirmed_at,
    )
    self.__class__._students[student_id] = updated
    return updated
```

---

### Task 3 Detail: `consent_status` in Linked Children Response

#### Step 3.1 — Update `LinkedChildResponse` schema (`onboarding/schemas.py`)

```python
class LinkedChildResponse(BaseModel):
    link_id: str
    student_id: str
    student_name: str
    class_name: str | None
    subject: str | None
    consent_status: str  # "not_required" | "pending" | "confirmed"
```

#### Step 3.2 — Update `get_linked_children()` (`onboarding/service.py`)

The existing `get_linked_children()` method builds `LinkedChildResponse` at lines ~388–396. Add `consent_status` to the construction. Use `student.name` (the `StudentRecord` field name is `.name`, not `.student_name`):

```python
result.append(
    LinkedChildResponse(
        link_id=link.link_id,
        student_id=link.student_id,
        student_name=student.name,           # StudentRecord.name — NOT student.student_name
        class_name=class_record.name if class_record else None,
        subject=class_record.subject if class_record else None,
        consent_status=student.consent_status,  # ADD — new field from StudentRecord
    )
)
```

#### Step 3.3 — Update TypeScript contract (`packages/contracts/src/onboarding.ts`)

```typescript
export interface LinkedChildResponse {
  link_id: string;
  student_id: string;
  student_name: string;
  class_name: string | null;
  subject: string | null;
  consent_status: string;  // ADD — "not_required" | "pending" | "confirmed"
}
```

`packages/contracts/src/index.ts` uses `export * from "./onboarding"` — no manual re-export needed.

---

### Task 4 Detail: AdminService Consent Operations

#### Step 4.1 — Add `onboarding_repository` to `AdminService` (`admin/service.py`)

```python
from app.domains.onboarding.repository import InMemoryOnboardingRepository

class AdminService:
    def __init__(
        self,
        repository: InMemoryAuthRepository,
        onboarding_repository: InMemoryOnboardingRepository,  # ADD
    ) -> None:
        self._repository = repository
        self._onboarding_repository = onboarding_repository  # ADD
```

Both `InMemoryAuthRepository` and `InMemoryOnboardingRepository` use class-level state — instantiating them in both admin and onboarding routers is correct; they share the same class-level dicts.

#### Step 4.2 — New exceptions and dataclasses (`admin/service.py`, after existing dataclasses)

```python
class StudentNotFoundForConsentError(Exception):
    pass

class ConsentAlreadyConfirmedError(Exception):
    pass

@dataclass(frozen=True)
class ConsentConfirmed:
    student_id: str
    org_id: str
    consent_status: str       # "confirmed"
    confirmed_by: str         # admin user_id
    confirmed_at: str         # ISO 8601 UTC

@dataclass(frozen=True)
class StudentConsentSummary:
    student_id: str
    name: str
    grade_level: str
    consent_status: str       # "pending" | "confirmed" | "not_required"
    org_id: str
```

#### Step 4.3 — `confirm_consent` method

Raises for both `"confirmed"` AND `"not_required"` — admins should only call this for `"pending"` students:

```python
def confirm_consent(
    self,
    student_id: str,
    admin_user_id: str,
    org_id: str,
) -> ConsentConfirmed:
    student = self._onboarding_repository.get_student(student_id)
    if student is None:
        raise StudentNotFoundForConsentError(f"Student not found: {student_id}")
    if student.org_id != org_id:
        raise StudentNotFoundForConsentError("Student does not belong to this organization")
    if student.consent_status in {"confirmed", "not_required"}:
        raise ConsentAlreadyConfirmedError(
            "Consent not required or already confirmed for this student"
        )
    confirmed_at = datetime.now(UTC).isoformat()
    updated = self._onboarding_repository.confirm_student_consent(
        student_id=student_id,
        confirmed_by=admin_user_id,
        confirmed_at=confirmed_at,
    )
    # assert narrows str | None → str (fields were just set by confirm_student_consent)
    assert updated.consent_confirmed_by is not None
    assert updated.consent_confirmed_at is not None
    return ConsentConfirmed(
        student_id=updated.student_id,
        org_id=updated.org_id,
        consent_status=updated.consent_status,
        confirmed_by=updated.consent_confirmed_by,
        confirmed_at=updated.consent_confirmed_at,
    )
```

> `from datetime import UTC, datetime` — already imported in this file (used by existing code).

#### Step 4.4 — `list_students_pending_consent` method

```python
def list_students_pending_consent(self, org_id: str) -> list[StudentConsentSummary]:
    students = self._onboarding_repository.list_students_for_org(org_id)
    return [
        StudentConsentSummary(
            student_id=s.student_id,
            name=s.name,
            grade_level=s.grade_level,
            consent_status=s.consent_status,
            org_id=s.org_id,
        )
        for s in students
        if s.consent_status == "pending"
    ]
```

---

### Task 5 Detail: Admin Router Endpoints

#### Step 5.1 — New schemas (`admin/schemas.py`)

```python
class ConsentConfirmResponse(BaseModel):
    student_id: str
    org_id: str
    consent_status: str
    confirmed_by: str
    confirmed_at: str

class StudentConsentSummaryResponse(BaseModel):
    student_id: str
    name: str
    grade_level: str
    consent_status: str
    org_id: str

class PendingConsentListResponse(BaseModel):
    students: list[StudentConsentSummaryResponse]
```

#### Step 5.2 — Update admin router singleton (`admin/router.py`)

```python
from app.domains.onboarding.repository import InMemoryOnboardingRepository

_admin_service = AdminService(
    repository=InMemoryAuthRepository(),
    onboarding_repository=InMemoryOnboardingRepository(),  # ADD
)
```

#### Step 5.3 — Update `reset_admin_state_for_tests()` — direct call, no cross-router import

```python
def reset_admin_state_for_tests() -> None:
    InMemoryAuthRepository.reset_state()
    InMemoryOnboardingRepository.reset_state()  # ADD — direct classmethod call, no import from onboarding.router
```

> **Why direct call**: Importing `reset_onboarding_state_for_tests` from `app.domains.onboarding.router` would create a cross-router import between sibling modules both registered in `main.py`. `InMemoryOnboardingRepository.reset_state()` is already a public classmethod — use it directly.

#### Step 5.4 — POST consent endpoint

```python
from app.domains.admin.service import ConsentAlreadyConfirmedError, StudentNotFoundForConsentError

@router.post(
    "/organizations/{org_id}/students/{student_id}/consent",
    response_model=ConsentConfirmResponse,
)
async def confirm_student_consent(
    org_id: str,
    student_id: str,
    actor: ActorContext = Depends(require_admin_actor),
    service: AdminService = Depends(get_admin_service),
) -> ConsentConfirmResponse:
    if actor.org_id != org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    try:
        result = service.confirm_consent(
            student_id=student_id,
            admin_user_id=actor.user_id,
            org_id=org_id,
        )
    except StudentNotFoundForConsentError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConsentAlreadyConfirmedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ConsentConfirmResponse(
        student_id=result.student_id,
        org_id=result.org_id,
        consent_status=result.consent_status,
        confirmed_by=result.confirmed_by,
        confirmed_at=result.confirmed_at,
    )
```

#### Step 5.5 — GET pending-consent endpoint

```python
@router.get(
    "/organizations/{org_id}/students/pending-consent",
    response_model=PendingConsentListResponse,
)
async def list_students_pending_consent(
    org_id: str,
    actor: ActorContext = Depends(require_admin_actor),
    service: AdminService = Depends(get_admin_service),
) -> PendingConsentListResponse:
    if actor.org_id != org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    students = service.list_students_pending_consent(org_id=org_id)
    return PendingConsentListResponse(
        students=[
            StudentConsentSummaryResponse(
                student_id=s.student_id,
                name=s.name,
                grade_level=s.grade_level,
                consent_status=s.consent_status,
                org_id=s.org_id,
            )
            for s in students
        ]
    )
```

---

### Task 6 Detail: Tests

#### Update `setup_function` in `test_admin_api.py`

```python
from app.domains.onboarding.repository import InMemoryOnboardingRepository

def setup_function():
    reset_auth_state_for_tests()
    InMemoryOnboardingRepository.reset_state()  # ADD — direct call, avoids circular import
    app.dependency_overrides.clear()
```

#### Test helper functions (add to `test_admin_api.py`)

```python
def _teacher_headers_for_consent_tests() -> dict[str, str]:
    token, _ = create_access_token(subject="usr_teacher_1", org_id="org_demo_1", role="teacher")
    return {"Authorization": f"Bearer {token}"}

def _parent_headers_for_consent_tests() -> dict[str, str]:
    token, _ = create_access_token(subject="usr_parent_1", org_id="org_demo_1", role="parent")
    return {"Authorization": f"Bearer {token}"}
```

#### Student creation endpoint for tests

Confirmed path: `POST /onboarding/classes/{class_id}/students` (line 106, `onboarding/router.py`).
Use the seed class `cls_1` (org_id: `org_demo_1`, teacher: `usr_teacher_1`) — always present after `reset_state()`.

#### Required test cases

**Test 1 — `test_confirm_consent_success`**: Under-13 student → confirm → 200 with correct fields

```python
def test_confirm_consent_success():
    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            student_resp = await client.post(
                "/onboarding/classes/cls_1/students",
                headers=_teacher_headers_for_consent_tests(),
                json={"name": "Young Student", "grade_level": "Grade 5"},
            )
            assert student_resp.status_code == 201
            student_id = student_resp.json()["student_id"]

            confirm = await client.post(
                f"/admin/organizations/org_demo_1/students/{student_id}/consent",
                headers=_admin_headers(),
            )
            assert confirm.status_code == 200
            body = confirm.json()
            assert body["consent_status"] == "confirmed"
            assert body["confirmed_by"] == "usr_admin_1"
            assert body["student_id"] == student_id
            assert "confirmed_at" in body
    asyncio.run(scenario())
```

**Test 2 — `test_confirm_consent_not_required_raises_409`**: Over-13 student (`"Grade 10"` is above threshold) → confirm → 409

> Note: `_requires_parental_consent("Grade 10")` extracts `10 > 7` → returns `False` → `consent_status = "not_required"`. Confirming consent on a `"not_required"` student raises `ConsentAlreadyConfirmedError` → 409.

```python
def test_confirm_consent_not_required_raises_409():
    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            student_resp = await client.post(
                "/onboarding/classes/cls_1/students",
                headers=_teacher_headers_for_consent_tests(),
                json={"name": "Older Student", "grade_level": "Grade 10"},
            )
            assert student_resp.status_code == 201
            student_id = student_resp.json()["student_id"]

            confirm = await client.post(
                f"/admin/organizations/org_demo_1/students/{student_id}/consent",
                headers=_admin_headers(),
            )
            assert confirm.status_code == 409
    asyncio.run(scenario())
```

**Test 3 — `test_confirm_consent_already_confirmed_raises_409`**: Confirm twice → second → 409

**Test 4 — `test_confirm_consent_wrong_org_forbidden`**: Admin from `org_demo_1` confirms student in `org_demo_2` → 403

**Test 5 — `test_confirm_consent_non_admin_forbidden`**: Teacher or parent token → 403

**Test 6 — `test_list_pending_consent_returns_under_13_only`**: Create Grade 5 + Grade K + Grade 10 students → GET pending-consent → returns 2 (Grade 5 + Grade K)

**Test 7 — `test_confirm_consent_removes_from_pending_list`**: Create Grade 5 student, confirm consent → GET pending-consent → empty list

---

### Repository Access Rules

`AdminService` uses only protocol methods — never direct attribute access on repositories:

| Need | Method |
| ---- | ------ |
| Get student by ID | `self._onboarding_repository.get_student(student_id)` |
| List org students | `self._onboarding_repository.list_students_for_org(org_id)` |
| Confirm consent | `self._onboarding_repository.confirm_student_consent(student_id, confirmed_by, confirmed_at)` |

Never: `InMemoryOnboardingRepository._students`, `self._onboarding_repository._students`

---

### What NOT To Implement

- **Full data access blocking** for unconsented students — Epic 11.5 (COPPA/FERPA controls)
- **Parent/student auth account deactivation** based on consent — no cross-domain link between `StudentRecord` and auth `UserRecord` exists; Epic 11 scope
- **`consent_status` on `StudentResponse`** — teacher roster view intentionally omits this in Epic 4
- **Admin web portal UI** — Epic 9
- **Mobile wizard changes** — `consent_status` in `LinkedChildResponse` is a contract addition only
- **CSV import consent** — individual consent only; bulk is out of scope
- **Consent withdrawal / revocation** — no revocation endpoint in this story
- **Push notifications** for consent requests — Epic 8

---

### File Structure Impact

Files to **modify**:

- `apps/api/app/domains/onboarding/models.py` (add consent fields to `StudentRecord`)
- `apps/api/app/domains/onboarding/repository.py` (add `import dataclasses`, `import re`, `_requires_parental_consent` helper; update `get_or_create_student`; add `list_students_for_org`, `confirm_student_consent` to Protocol + implementation)
- `apps/api/app/domains/onboarding/service.py` (update `get_linked_children` to pass `consent_status=student.consent_status`)
- `apps/api/app/domains/onboarding/schemas.py` (add `consent_status: str` to `LinkedChildResponse`)
- `apps/api/app/domains/admin/service.py` (add `onboarding_repository` param; add dataclasses + exceptions; add `confirm_consent`, `list_students_pending_consent` methods)
- `apps/api/app/domains/admin/router.py` (update singleton; add `InMemoryOnboardingRepository.reset_state()` to reset function; add consent endpoints)
- `apps/api/app/domains/admin/schemas.py` (add `ConsentConfirmResponse`, `StudentConsentSummaryResponse`, `PendingConsentListResponse`)
- `packages/contracts/src/onboarding.ts` (add `consent_status: string` to `LinkedChildResponse`)
- `apps/api/tests/test_admin_api.py` (update `setup_function`; add consent test cases)
- `apps/api/tests/test_onboarding_api.py` (update linked children tests to assert `consent_status` field present)

### Project Structure Notes

- Admin domain already exists at `apps/api/app/domains/admin/` — follow all existing patterns
- `InMemoryOnboardingRepository` class-level state: safe to instantiate in both admin + onboarding routers
- `packages/contracts/src/index.ts` uses `export * from "./onboarding"` — `LinkedChildResponse` update auto-exported
- `_requires_parental_consent` is a module-level private function in `repository.py` (underscore prefix = internal)

### References

- Epic 4 / Story 4.10 requirements: [Source: `_bmad-output/planning-artifacts/epics.md` #Story 4.10]
- Architecture domain model (students + consent fields): [Source: `_bmad-output/planning-artifacts/architecture.md` #Core Domain Model]
- Architecture security + COPPA gate: [Source: `_bmad-output/planning-artifacts/architecture.md` #Security]
- `StudentRecord` model: [Source: `apps/api/app/domains/onboarding/models.py`]
- `InMemoryOnboardingRepository.get_or_create_student()`: [Source: `apps/api/app/domains/onboarding/repository.py:129`]
- `InMemoryOnboardingRepository.reset_state()`: [Source: `apps/api/app/domains/onboarding/repository.py:101`]
- `OnboardingService.get_linked_children()`: [Source: `apps/api/app/domains/onboarding/service.py:368`]
- Existing `accept_invite_link` frozen record update pattern: [Source: `apps/api/app/domains/onboarding/repository.py:217`]
- Admin service pattern: [Source: `apps/api/app/domains/admin/service.py`]
- Admin router pattern: [Source: `apps/api/app/domains/admin/router.py`]
- Test patterns (admin): [Source: `apps/api/tests/test_admin_api.py`]
- Test patterns (onboarding): [Source: `apps/api/tests/test_onboarding_api.py`]
- Previous story learnings (4.9): [Source: `_bmad-output/implementation-artifacts/4-9-guided-onboarding-wizards-per-role.md`]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None.

### Completion Notes List

- Implemented COPPA consent gate: StudentRecord extended with consent_status/confirmed_by/confirmed_at fields
- `_requires_parental_consent()` helper added to repository.py — grade ≤ 7 or kindergarten keywords → "pending"; grade > 7 (numeric found) → "not_required"; unrecognizable grade → conservative True
- Grade parsing now also handles ordinal formats (e.g., "10th Grade") and correctly marks those as `not_required`
- AdminService now requires `onboarding_repository` — updated test_admin_service.py with `_make_service()` factory to avoid repetition
- Added consent-record query endpoint `GET /admin/organizations/{org_id}/students/{student_id}/consent` so confirmed consent actor/timestamp are queryable for audit
- All consent API tests pass; full API suite now passes (351 tests)
- TypeScript: zero errors (pnpm typecheck clean)

### File List

- apps/api/app/domains/onboarding/models.py
- apps/api/app/domains/onboarding/repository.py
- apps/api/app/domains/onboarding/router.py
- apps/api/app/domains/onboarding/schemas.py
- apps/api/app/domains/onboarding/service.py
- apps/api/app/domains/admin/service.py
- apps/api/app/domains/admin/schemas.py
- apps/api/app/domains/admin/router.py
- packages/contracts/src/index.ts
- packages/contracts/src/onboarding.ts
- apps/api/tests/test_auth_login_api.py
- apps/api/tests/test_auth_google_api.py
- apps/api/tests/test_admin_api.py
- apps/api/tests/test_admin_service.py
- apps/api/tests/test_onboarding_api.py

## Senior Developer Review (AI)

### Reviewer

GitHub Copilot (GPT-5.3-Codex)

### Review Date

2026-03-23

### Outcome

High and Medium review findings fixed; story approved.

### Validation Evidence

- `pnpm typecheck` ✅
- `/home/cybernyx/teemo.ai/ilm/.venv/bin/python -m pytest apps/api/tests/ -q` ✅ (351 passed)
