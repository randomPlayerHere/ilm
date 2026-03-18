# Story 3.1: Linked Guardian and Student Progress Access

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a guardian or student,
I want to access only authorized progress dashboards,
so that I can view relevant progress safely.

## Acceptance Criteria

1. **Guardian linked-student gate:** A parent actor with a `GuardianStudentLink` for a given student
   receives approved grade and confirmed recommendation data for that student.
   Unlinked student IDs → `404` (not `403`, to prevent enumeration).

2. **Student self-access gate:** A student actor whose `actor.user_id == student_id` receives their own
   approved grade and confirmed recommendation data.
   Any `student_id` that does not match `actor.user_id` → `403`.

3. **Role exclusion:** Any role other than `parent` or `student` (e.g. `teacher`, `admin`) → `403`.

4. **Unauthenticated requests** → `401`.

5. **Approved-only gate:** Grades returned only when a `GradeApprovalRecord` exists for the job
   (i.e. teacher has approved via Story 2.5). No approval record → grade not surfaced.

6. **Confirmed-only gate:** Recommendations returned only from `ConfirmedRecommendationRecord`
   (i.e. teacher has confirmed via Story 2.6). No confirmation → not surfaced.

7. **Org isolation:** A parent in `org_demo_2` cannot see data for a student in `org_demo_1`.
   Cross-org student_id → `404`.

8. **Empty-state:** If no approved grades or confirmed recommendations exist for the student,
   both lists return empty (`[]`); response is still `200`.

9. **Two read endpoints:**
   - `GET /progress/students/{student_id}/grades` → approved grade list
   - `GET /progress/students/{student_id}/recommendations` → confirmed recommendation list

## Tasks / Subtasks

- [x] Task 1: Add `usr_student_1` student context to grading repo seed data (AC: 2, 5, 6)
  - [x] In `InMemoryGradingRepository._ensure_seed_data()`, add entry for `usr_student_1` in `cls._students`
    enrolled in `cls_demo_math_1`, org `org_demo_1`, teacher `usr_teacher_1`
  - [x] This bridges the auth-layer user identity (`usr_student_1`) to the grading-layer student context

- [x] Task 2: Add list query methods to `InMemoryGradingRepository` (AC: 5, 6, 7)
  - [x] Add `list_approved_grades_for_student(student_id: str, org_id: str) -> list[ApprovedGradeRecord]`
    Traversal: `_artifacts` → `_artifact_job_index` → `_grade_approvals`; include only entries with an
    approval record; attach assignment_id and artifact_id from artifact
  - [x] Define a `ApprovedGradeRecord` dataclass (in `repository.py`) to hold the joined fields:
    `job_id`, `artifact_id`, `assignment_id`, `student_id`, `approved_score`, `approved_feedback`,
    `approved_at`, `approver_user_id`, `version`
  - [x] Add `list_confirmed_recommendations_for_student(student_id: str, org_id: str) -> list[ConfirmedRecommendationRecord]`
    Traversal: `_confirmed_recommendations.values()` filtered by `student_id`;
    verify `org_id` through `_recommendation_jobs[rec_job_id].org_id`

- [x] Task 3: Create `app/domains/progress/` domain (AC: 1, 2, 3, 4, 7, 8, 9)
  - [x] Create `app/domains/progress/__init__.py` (empty, matches all other domains)
  - [x] Create `app/domains/progress/schemas.py` with:
    - `ApprovedGradeResponse` (job_id, artifact_id, assignment_id, student_id, approved_score,
      approved_feedback, approved_at, approver_user_id, version)
    - `ApprovedGradeListResponse` (grades: list[ApprovedGradeResponse])
    - `ConfirmedRecommendationResponse` (rec_job_id, job_id, student_id, topics, confirmed_by, confirmed_at)
    - `ConfirmedRecommendationListResponse` (recommendations: list[ConfirmedRecommendationResponse])
  - [x] Create `app/domains/progress/router.py` with:
    - Module-level `_grading_repo = InMemoryGradingRepository()` and `_students_repo = InMemoryStudentsRepository()`
    - `router = APIRouter(prefix="/progress", tags=["progress"])`
    - `_require_parent_or_student(actor, student_id)` helper — see access logic below
    - `GET /progress/students/{student_id}/grades` endpoint
    - `GET /progress/students/{student_id}/recommendations` endpoint
    - `reset_progress_state_for_tests()` calling both repo reset methods

- [x] Task 4: Register progress router in `app/main.py` (AC: 9)
  - [x] Import and `app.include_router(progress_router)` after students router

- [x] Task 5: Write tests in `apps/api/tests/test_progress_api.py` (AC: 1–9)
  - [x] `setup_function()` resets auth state, grading state, students state
  - [x] Helper to create full grading pipeline state (assignment → artifact → job → approve)
    via direct repo calls (not HTTP) to keep tests fast and isolated
  - [x] Helper to create guardian-student link via HTTP POST `/students/{student_id}/guardian-links`
  - [x] At minimum 12 tests covering: parent success, student self-success, parent unlinked → 404,
    student wrong id → 403, unauthenticated → 401, teacher role → 403, org isolation, empty state,
    unapproved grade not returned, unconfirmed recommendation not returned,
    recommendation endpoint parent/student access

### Review Follow-ups (AI)

- [x] [AI-Review][High] Add endpoint-level cross-org isolation test coverage for `GET /progress/students/{student_id}/grades` and `GET /progress/students/{student_id}/recommendations` to validate AC7 over HTTP path, not only repo-layer validation. [apps/api/tests/test_progress_api.py:278]
- [x] [AI-Review][Medium] Update story File List to include all changed files in this story cycle, including README change. [apps/api/README.md:1]
- [x] [AI-Review][Medium] Re-run full suite to completion and update completion notes with current exact pass count (replace stale `229/229` claim). [_bmad-output/implementation-artifacts/3-1-linked-guardian-and-student-progress-access.md:247]
- [x] [AI-Review][Medium] Remove hardcoded `assignment_id="asgn_1"` from recommendation pipeline test helper and use the created assignment ID from setup flow. [apps/api/tests/test_progress_api.py:96]
- [x] [AI-Review][Low] Remove unused `_wrong_student_headers` helper or add a test that exercises it. [apps/api/tests/test_progress_api.py:35]

## Dev Notes

### Access Control Logic

`_require_parent_or_student(actor: ActorContext, student_id: str, students_repo, grading_repo)`:

```python
if actor.role == "student":
    if actor.user_id != student_id:
        raise HTTPException(403, "Forbidden")
elif actor.role == "parent":
    links = students_repo.get_links_for_guardian(actor.user_id, actor.org_id)
    if not any(link.student_id == student_id for link in links):
        raise HTTPException(404, "Student not found")  # 404 not 403 — avoid enumeration
else:
    raise HTTPException(403, "Forbidden")
```

Additional org-isolation check for student role: verify the student context is in `actor.org_id`
(query `grading_repo` for the student context; if absent or different org → 404 to prevent enumeration).

### Domain Boundary Rule

The `progress` router **must not import from `app.domains.grading.service`** or
`app.domains.grading.router` or `app.domains.students.router`. It may only import:
- `InMemoryGradingRepository` from `app.domains.grading.repository`
- `InMemoryStudentsRepository` from `app.domains.students.repository`
- `ActorContext`, `require_authenticated_actor` from `app.domains.auth.dependencies`

This is explicitly mandated by the Domain Boundary Rule in `apps/api/README.md`.

### `is_approved` / `is_confirmed` Gates (from Stories 2.5 and 2.6)

- A grade is surfaced **only** if a `GradeApprovalRecord` exists for the job in `_grade_approvals`.
  The traversal: artifact.student_id + artifact_job_index + grade_approvals dict.
- A recommendation is surfaced **only** if a `ConfirmedRecommendationRecord` exists in
  `_confirmed_recommendations`. Filter by `student_id` and verify `org_id` via `_recommendation_jobs`.

### Grading Repo Traversal Pattern for Grades

```python
def list_approved_grades_for_student(self, student_id: str, org_id: str) -> list[ApprovedGradeRecord]:
    student_artifacts = [
        a for a in self.__class__._artifacts.values()
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
        results.append(ApprovedGradeRecord(
            job_id=job_id,
            artifact_id=artifact.artifact_id,
            assignment_id=artifact.assignment_id,
            student_id=student_id,
            approved_score=approval.approved_score,
            approved_feedback=approval.approved_feedback,
            approved_at=approval.approved_at,
            approver_user_id=approval.approver_user_id,
            version=approval.version,
        ))
    return results
```

### Test Setup Strategy

Tests use direct repo mutation (not HTTP) to set up grading state, because the full
teacher grading pipeline (create assignment → upload artifact → submit job → background process →
approve) requires many HTTP calls. Instead:

1. Directly call `InMemoryGradingRepository()` methods to create assignment, artifact, grading job,
   grading result, grade approval, recommendation job, recommendation result, confirmed recommendation.
2. Use HTTP POST to create guardian-student link (requires auth as teacher).
3. Then test the progress endpoint with parent/student JWTs.

Key seed IDs after Task 1 change:
- `usr_student_1` in grading repo: org=`org_demo_1`, class=`cls_demo_math_1`, teacher=`usr_teacher_1`
- `usr_parent_1` in auth repo: org=`org_demo_1`, role=`parent`
- `usr_student_1` in auth repo: org=`org_demo_1`, role=`student`

### Module-Level Repo Singleton Pattern

Matches existing pattern from `app/domains/students/router.py` and `app/domains/grading/router.py`:

```python
_grading_repo = InMemoryGradingRepository()
_students_repo = InMemoryStudentsRepository()
```

The `reset_progress_state_for_tests()` function in progress/router.py should call both:
```python
def reset_progress_state_for_tests() -> None:
    InMemoryGradingRepository.reset_state()
    InMemoryStudentsRepository.reset_state()
```

### JWT / Token Pattern for Tests

Same mismatched-role trick for 403 tests (from test_students_api.py): use a token with
`role="teacher"` for a user whose DB role is `parent` → `require_authenticated_actor` cross-check
will fail with 403 before reaching the endpoint handler.

For genuine `parent` 403 (wrong role): use a `teacher` role token for `usr_teacher_1` (stored as teacher
in auth repo) calling the progress endpoint → endpoint handler enforces `_require_parent_or_student`.

### Org Isolation in Tests

Grading repo seed has `stu_other_org_1` (org=`org_other_1`). A parent with org=`org_demo_1` and a
guardian link to `stu_other_org_1` would still fail the org check in the grading repo traversal.
This can be tested at the repo method level directly (not necessarily via HTTP) with a comment
similar to test_students_api.py test 16 noting single-org HTTP test limitation.

### Project Structure Notes

- New domain at: `apps/api/app/domains/progress/`
- Files: `__init__.py`, `schemas.py`, `router.py` (no `models.py` needed — uses repo records directly)
- No `service.py` needed — logic is simple enough for the router helpers
- New test file: `apps/api/tests/test_progress_api.py`
- Modified files:
  - `apps/api/app/domains/grading/repository.py` — add `ApprovedGradeRecord` dataclass + 2 new methods
  - `apps/api/app/main.py` — register `progress_router`
  - `apps/api/README.md` — update Story Scope section and Endpoint-Level Role Summary table to include progress endpoints

### References

- Epic 3 story 3.1 ACs: [Source: _bmad-output/implementation-artifacts/epics.md#Story-3.1]
- FR19, FR20, FR25, FR26: [Source: _bmad-output/planning-artifacts/prd.md#Parent-and-Student-Progress-Transparency]
- Domain Boundary Rule: [Source: apps/api/README.md#Domain-Boundary-Rule]
- Tenant Isolation Rules: [Source: apps/api/README.md#Tenant-Isolation]
- Guardian-Student link repo: [Source: apps/api/app/domains/students/repository.py]
- `is_approved` flag: [Source: apps/api/app/domains/grading/service.py#GradingJobWithResult]
- `is_confirmed` flag: [Source: apps/api/app/domains/grading/service.py#RecommendationJobWithResult]
- Grading repo seed data: [Source: apps/api/app/domains/grading/repository.py#_ensure_seed_data]
- Auth repo seed data (usr_parent_1, usr_student_1): [Source: apps/api/app/domains/auth/repository.py#_ensure_seed_data]
- `GradeApprovalRecord` structure: [Source: apps/api/app/domains/grading/repository.py]
- `ConfirmedRecommendationRecord` structure: [Source: apps/api/app/domains/grading/repository.py]
- Module-level singleton pattern: [Source: apps/api/app/domains/students/router.py#_repo]
- Test harness pattern: [Source: apps/api/tests/test_students_api.py#setup_function]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Implemented `progress` domain with two read endpoints: `GET /progress/students/{student_id}/grades` and `GET /progress/students/{student_id}/recommendations`
- Added `ApprovedGradeRecord` dataclass and `list_approved_grades_for_student` / `list_confirmed_recommendations_for_student` methods to `InMemoryGradingRepository`
- Added `usr_student_1` to grading repo seed data bridging auth-layer identity to grading-layer student context
- `_require_parent_or_student` helper enforces: student self-access only (403 on mismatch), parent via GuardianStudentLink (404 on no link — avoids enumeration), all other roles 403
- Org isolation enforced: student role checks `grading_repo.get_student_context` for org match; parent guardian-link lookup is already scoped to `actor.org_id`; repo list methods filter by `org_id`
- 20 tests pass covering all ACs (8 added in code review cycles); 237/237 full suite passes with zero regressions
- Code review cycle 1 fixes: added defense-in-depth org check to parent path; fixed hardcoded `assignment_id="asgn_1"`; added AC3 admin role test, AC7 HTTP cross-org tests, AC8 recommendations empty-state test, recommendations unauthenticated test, mismatched-role auth-layer test
- Code review cycle 2 fixes: updated stale test-7 comment; added teacher→/recommendations test; added principal role test (mismatched-role pattern); clarified side-effect-only helper call sites

### File List

- `apps/api/app/domains/grading/repository.py` — added `ApprovedGradeRecord` dataclass, `usr_student_1` seed entry, `list_approved_grades_for_student`, `list_confirmed_recommendations_for_student`
- `apps/api/app/domains/progress/__init__.py` — new (empty)
- `apps/api/app/domains/progress/schemas.py` — new: `ApprovedGradeResponse`, `ApprovedGradeListResponse`, `ConfirmedRecommendationResponse`, `ConfirmedRecommendationListResponse`
- `apps/api/app/domains/progress/router.py` — new: progress router with two GET endpoints and `reset_progress_state_for_tests`
- `apps/api/app/main.py` — registered `progress_router`
- `apps/api/tests/test_progress_api.py` — new: 20 tests covering all ACs (8 added across two code review cycles)
- `apps/api/README.md` — added progress endpoints to Story Scope and Endpoint-Level Role Summary table
