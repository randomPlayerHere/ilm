# Story 3.2: Outcome Explanations and Trend Visualization

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a guardian or student,
I want scores with explanations and trend views,
so that I understand whether improvement is occurring.

## Acceptance Criteria

1. **Explanation context gate:** Each approved grade response includes `assignment_title` alongside `approved_score` and `approved_feedback`, giving human-readable context to the numeric result.

2. **Feedback reflects approval:** The `approved_feedback` field in the grade response equals the value set by the teacher's approval action (Story 2.5). No override or transformation occurs in the progress layer.

3. **Chronological trend ordering:** `GET /progress/students/{student_id}/grades` returns grades sorted by `approved_at` ascending (oldest → newest), enabling clients to display longitudinal progression.

4. **Performance target compliance:** The grades endpoint must respond within the SRS NFR-001 threshold (p95 ≤ 700 ms for student read endpoints). In-memory repo ensures this; no async work or external calls are introduced.

5. **Unchanged access control:** All existing auth/authz rules from Story 3.1 (`_require_parent_or_student`, org isolation, role exclusion, 401/403/404 responses) remain fully intact.

## Tasks / Subtasks

- [x] Task 1: Enrich `ApprovedGradeRecord` with `assignment_title` (AC: 1)
  - [x] In `apps/api/app/domains/grading/repository.py`, add `assignment_title: str` field to `ApprovedGradeRecord` dataclass after `assignment_id`
  - [x] In `list_approved_grades_for_student`, fetch `assignment = self.__class__._assignments.get(artifact.assignment_id)` and pass `assignment_title=assignment.title if assignment else ""` when constructing `ApprovedGradeRecord`
  - [x] Sort the `results` list by `approved_at` ascending before returning: `return sorted(results, key=lambda r: r.approved_at)`
  - [x] ISO 8601 strings (from `datetime.now(UTC).isoformat()`) sort correctly lexicographically — no datetime parsing required

- [x] Task 2: Enrich `ApprovedGradeResponse` schema (AC: 1)
  - [x] In `apps/api/app/domains/progress/schemas.py`, add `assignment_title: str` to `ApprovedGradeResponse` after `assignment_id`

- [x] Task 3: Pass `assignment_title` through progress router (AC: 1)
  - [x] In `apps/api/app/domains/progress/router.py`, add `assignment_title=r.assignment_title` to the `ApprovedGradeResponse(...)` constructor call inside `get_student_grades`

- [x] Task 4: Write tests in `apps/api/tests/test_progress_api.py` (AC: 1, 2, 3, 5)
  - [x] Add test: single grade response includes `assignment_title` matching the title passed to `create_assignment`
  - [x] Add test: multiple grades returned sorted by `approved_at` ascending — create two assignment/artifact/approval pipelines with explicit `approved_at` strings (e.g. `"2024-01-01T00:00:00+00:00"` and `"2024-02-01T00:00:00+00:00"`), verify order in response
  - [x] Verify existing 237 tests still pass (no regressions)

### Review Follow-ups (AI)

- [x] [AI-Review][Medium] Update Story 3.2 narrative claim "Modified files only — no new files needed" to reflect newly added `apps/api/app/domains/progress/__init__.py`. [_bmad-output/implementation-artifacts/3-2-outcome-explanations-and-trend-visualization.md:199]
- [x] [AI-Review][Medium] Reconcile Dev Agent Record `File List` with actual changed source/docs; include `apps/api/app/main.py`, `apps/api/README.md`, and `apps/api/app/domains/progress/__init__.py` or remove unrelated edits from this story branch. [_bmad-output/implementation-artifacts/3-2-outcome-explanations-and-trend-visualization.md:237]
- [x] [AI-Review][Medium] Harden chronological sort by normalizing/parsing `approved_at` before ordering to avoid mixed-offset timestamp misordering edge cases. [apps/api/app/domains/grading/repository.py:565]
- [x] [AI-Review][Medium] Add an explicit AC4 performance guard (targeted benchmark or contract/perf test) for `/progress/students/{student_id}/grades` against p95 ≤ 700 ms. [apps/api/tests/test_progress_api.py:1]
- [x] [AI-Review][Low] Replace silent missing-assignment fallback (`assignment_title=""`) with explicit handling (e.g., sentinel label or integrity warning) to preserve explanation context quality. [apps/api/app/domains/grading/repository.py:557]
- [x] [AI-Review][Medium] Add `assert grades[0]["assignment_id"] == assignment.assignment_id` to `test_grade_response_includes_assignment_title` — current test verifies only the new field and feedback but not that the existing `assignment_id` field is correctly attributed, leaving a regression gap. [apps/api/tests/test_progress_api.py:655]
- [x] [AI-Review][Low] Fix confusing line-number reference in Dev Notes "Regression Risk" section: claims `GradeVersionRecord` is at line ~122, but line 122 is `ApprovedGradeRecord` (the one modified in this story); `GradeVersionRecord` is at line ~78. Update note to avoid future reviewer confusion. [_bmad-output/implementation-artifacts/3-2-outcome-explanations-and-trend-visualization.md:196]
- [x] [AI-Review][Low] Note for items [AI-Review][Medium] #1 and #2 above: `apps/api/app/main.py`, `apps/api/README.md`, and `apps/api/app/domains/progress/__init__.py` appearing in git diff are Story 3.1 artifacts not yet committed — Story 3.2 File List is accurate for its own scope. Resolve by committing Story 3.1 work, or add a note in the story clarifying these are prior-story uncommitted changes.

## Dev Notes

### What Changed vs Story 3.1

Story 3.1 built access control and the two progress endpoints. This story enriches the grade response for display and orders for trend visualization. **Do not re-implement access control logic** — `_require_parent_or_student` is untouched.

### Exact Code Changes

**`apps/api/app/domains/grading/repository.py`** — `ApprovedGradeRecord` dataclass:

```python
@dataclass(frozen=True)
class ApprovedGradeRecord:
    job_id: str
    artifact_id: str
    assignment_id: str
    assignment_title: str   # ← NEW
    student_id: str
    approved_score: str
    approved_feedback: str
    approved_at: str
    approver_user_id: str
    version: int
```

**`list_approved_grades_for_student` update:**

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
        assignment = self.__class__._assignments.get(artifact.assignment_id)
        results.append(ApprovedGradeRecord(
            job_id=job_id,
            artifact_id=artifact.artifact_id,
            assignment_id=artifact.assignment_id,
            assignment_title=assignment.title if assignment else "",
            student_id=student_id,
            approved_score=approval.approved_score,
            approved_feedback=approval.approved_feedback,
            approved_at=approval.approved_at,
            approver_user_id=approval.approver_user_id,
            version=approval.version,
        ))
    return sorted(results, key=lambda r: r.approved_at)
```

**`apps/api/app/domains/progress/schemas.py`** — add field to `ApprovedGradeResponse`:

```python
class ApprovedGradeResponse(BaseModel):
    job_id: str
    artifact_id: str
    assignment_id: str
    assignment_title: str   # ← NEW
    student_id: str
    approved_score: str
    approved_feedback: str
    approved_at: str
    approver_user_id: str
    version: int
```

**`apps/api/app/domains/progress/router.py`** — inside `get_student_grades`, add one field:

```python
ApprovedGradeResponse(
    job_id=r.job_id,
    artifact_id=r.artifact_id,
    assignment_id=r.assignment_id,
    assignment_title=r.assignment_title,   # ← NEW
    student_id=r.student_id,
    ...
)
```

### Trend Ordering: Why ISO 8601 Sorts Lexicographically

All `approved_at` values are produced by `datetime.now(UTC).isoformat()` which emits e.g. `"2024-03-18T12:34:56.789012+00:00"`. ISO 8601 strings with consistent UTC offset compare correctly as plain strings — no `datetime.fromisoformat()` parsing needed for the sort key.

### Test Pattern for Trend Ordering Test

Use `save_grade_approval` directly on the repo with explicit ISO 8601 `approved_at` strings to control order:

```python
def test_grades_returned_in_chronological_order() -> None:
    reset_progress_state_for_tests()
    reset_auth_state_for_tests()
    repo = InMemoryGradingRepository()

    # First assignment/approval (earlier date)
    asgn_1 = repo.create_assignment(class_id="cls_demo_math_1", org_id="org_demo_1",
                                     teacher_user_id="usr_teacher_1", title="Assignment Alpha")
    art_1 = repo.create_artifact(assignment_id=asgn_1.assignment_id, student_id="usr_student_1",
                                  class_id="cls_demo_math_1", org_id="org_demo_1",
                                  teacher_user_id="usr_teacher_1", file_name="a1.jpg",
                                  media_type="image/jpeg", storage_key="k1")
    job_1 = repo.submit_grading_job(artifact_id=art_1.artifact_id,
                                     assignment_id=asgn_1.assignment_id, org_id="org_demo_1",
                                     student_id="usr_student_1", teacher_user_id="usr_teacher_1")
    repo.save_grading_result(job_id=job_1.job_id, ...)  # as needed
    repo.save_grade_approval(job_id=job_1.job_id, approved_score="B", approved_feedback="Good",
                              approver_user_id="usr_teacher_1", version=1,
                              approved_at="2024-01-01T00:00:00+00:00")

    # Second assignment/approval (later date)
    asgn_2 = repo.create_assignment(..., title="Assignment Beta")
    ...
    repo.save_grade_approval(..., approved_at="2024-02-01T00:00:00+00:00")

    with httpx.Client(app=app, base_url="http://test") as client:
        r = client.get("/progress/students/usr_student_1/grades",
                       headers=_student_headers())
    assert r.status_code == 200
    grades = r.json()["grades"]
    assert len(grades) == 2
    assert grades[0]["assignment_title"] == "Assignment Alpha"
    assert grades[1]["assignment_title"] == "Assignment Beta"
    assert grades[0]["approved_at"] < grades[1]["approved_at"]
```

Note: `save_grading_result` is required before `save_grade_approval` per the existing pipeline — check `test_progress_api.py`'s `_create_approved_grade_pipeline` helper for the correct call sequence. **Reuse or extend that helper** rather than writing new boilerplate.

### Domain Boundary Rule

The `progress` router **must not import from** `app.domains.grading.service`, `app.domains.grading.router`, or `app.domains.students.router`. Only allowed imports:
- `InMemoryGradingRepository` from `app.domains.grading.repository`
- `InMemoryStudentsRepository` from `app.domains.students.repository`
- `ActorContext`, `require_authenticated_actor` from `app.domains.auth.dependencies`

[Source: apps/api/README.md#Domain-Boundary-Rule]

### Regression Risk

`ApprovedGradeRecord` is a `frozen=True` dataclass — adding `assignment_title` is a **positional break** if any existing code constructs it with positional args. Check all construction sites:
- `list_approved_grades_for_student` in `repository.py` — must add `assignment_title=`
- The `GradeVersionRecord` dataclass at line ~78 is separate; do NOT modify it (it is not `ApprovedGradeRecord`). `ApprovedGradeRecord` itself is at line ~122.
- No other construction sites exist outside the repo method

### Performance Note (SRS NFR-001)

Grades endpoint must respond p95 ≤ 700 ms. In-memory repo + `sorted()` on a small list is O(n log n) and well within target. No caching, external I/O, or async ops are added by this story.

### Project Structure Notes

- Modified files only — Story 3.2 itself does not create new files.
- `apps/api/app/domains/grading/repository.py` — update `ApprovedGradeRecord` + `list_approved_grades_for_student`
- `apps/api/app/domains/progress/schemas.py` — add `assignment_title` to `ApprovedGradeResponse`
- `apps/api/app/domains/progress/router.py` — pass `assignment_title` in response construction
- `apps/api/tests/test_progress_api.py` — add 2 new tests (assignment_title present, chronological order)
- **Note:** `apps/api/app/domains/progress/__init__.py`, `apps/api/app/main.py`, and `apps/api/README.md` may appear in `git diff` as untracked/modified — these are Story 3.1 artifacts that were not yet committed when Story 3.2 was started; they are not part of Story 3.2's scope.

### References

- Story 3.2 ACs and user story: [Source: _bmad-output/implementation-artifacts/epics.md#Story-3.2]
- FR21 (explanatory context), FR22 (longitudinal trends): [Source: _bmad-output/planning-artifacts/prd.md#FR21]
- FR-020 (student historical performance timeline): [Source: _bmad-output/planning-artifacts/srs.md#FR-020]
- NFR-001 (API p95 ≤ 700ms for student read endpoints): [Source: _bmad-output/planning-artifacts/srs.md#NFR-001]
- ApprovedGradeRecord current definition: [Source: apps/api/app/domains/grading/repository.py:122]
- list_approved_grades_for_student current impl: [Source: apps/api/app/domains/grading/repository.py:538]
- Progress router get_student_grades: [Source: apps/api/app/domains/progress/router.py:51]
- Test helper _create_approved_grade_pipeline: [Source: apps/api/tests/test_progress_api.py]
- Domain Boundary Rule: [Source: apps/api/README.md#Domain-Boundary-Rule]
- Story 3.1 (access control foundation, 237 tests): [Source: _bmad-output/implementation-artifacts/3-1-linked-guardian-and-student-progress-access.md]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Added `assignment_title: str` field to `ApprovedGradeRecord` dataclass (keyword arg, frozen dataclass — no positional-arg breaks)
- Updated `list_approved_grades_for_student` to join `_assignments[assignment_id].title` and sort results by `approved_at` ascending; ISO 8601 lexicographic sort — no datetime parsing needed
- Added `assignment_title: str` to `ApprovedGradeResponse` Pydantic schema
- Passed `assignment_title=r.assignment_title` in `get_student_grades` router response construction
- Added `test_grade_response_includes_assignment_title` (test 21): verifies `assignment_title == "Math Quiz"`, `assignment_id` attribution, and `approved_feedback` round-trips correctly
- Added `test_grades_returned_in_chronological_order` (test 22): inserts Beta (Feb) before Alpha (Jan) and confirms Alpha appears first — validates sort not insertion order
- Full suite: 239/239 passed (was 237/237); zero regressions
- Access control logic (`_require_parent_or_student`, org isolation, 401/403/404 gates) untouched per AC5
- **Code review follow-ups addressed (2026-03-18):** Addressed code review findings — 8 items resolved:
  - ✅ Resolved review finding [Medium]: Hardened `approved_at` sort to use `datetime.fromisoformat()` parse key instead of raw string comparison
  - ✅ Resolved review finding [Low]: Replaced silent `assignment_title=""` fallback with `"[Assignment Not Found]"` sentinel label
  - ✅ Resolved review finding [Medium]: Added `assert grades[0]["assignment_id"] == assignment.assignment_id` to test 21
  - ✅ Resolved review finding [Medium]: Added `test_grades_endpoint_responds_within_p95_700ms` (test 23) — AC4 NFR-001 perf contract
  - ✅ Resolved review finding [Medium]: Updated "Project Structure Notes" to clarify Story 3.1 uncommitted files not in Story 3.2 scope
  - ✅ Resolved review finding [Medium]: Added clarification note in Dev Notes for `apps/api/app/main.py`, `README.md`, `__init__.py` being Story 3.1 artifacts
  - ✅ Resolved review finding [Low]: Fixed "Regression Risk" line-number reference — GradeVersionRecord is at ~78, ApprovedGradeRecord at ~122
  - ✅ Resolved review finding [Low]: Added Story 3.1 uncommitted-artifacts clarification note per review item #8
- Full suite after review follow-ups: 240/240 passed; zero regressions

### File List

- `apps/api/app/domains/grading/repository.py` — added `assignment_title` field to `ApprovedGradeRecord`; updated `list_approved_grades_for_student` to join assignment title, use `"[Assignment Not Found]"` sentinel, and sort by `datetime.fromisoformat(approved_at)`
- `apps/api/app/domains/progress/schemas.py` — added `assignment_title: str` to `ApprovedGradeResponse`
- `apps/api/app/domains/progress/router.py` — passed `assignment_title=r.assignment_title` in `ApprovedGradeResponse` construction
- `apps/api/tests/test_progress_api.py` — added `test_grade_response_includes_assignment_title` (test 21), `test_grades_returned_in_chronological_order` (test 22), and `test_grades_endpoint_responds_within_max_700ms` (test 23)
- `_bmad-output/implementation-artifacts/3-2-outcome-explanations-and-trend-visualization.md` — updated Dev Notes, Completion Notes, File List, and marked all review follow-ups resolved

## Change Log

- Initial implementation (Stories 3.2 Tasks 1–4): enriched `ApprovedGradeRecord` and `ApprovedGradeResponse` with `assignment_title`; sort by `approved_at` ascending; tests 21–22 added (Date: 2026-03-17)
- Addressed code review findings — 8 items resolved: hardened sort to datetime parse, sentinel label for missing assignment, assignment_id regression assertion, AC4 perf test (test 23), Dev Notes corrections, narrative clarifications (Date: 2026-03-18)
- Code review (Senior Developer AI, 2026-03-18): 3 MEDIUM + 5 LOW issues found; all 3 MEDIUM fixed automatically: sort stability secondary key `(datetime, job_id)`, perf test warm-up added, max-latency semantics corrected; 5 LOW items created as action items. Story promoted to **done**.

## Senior Developer Review (AI)

**Review Date:** 2026-03-18
**Outcome:** Approved (after fixes)
**Issues Fixed:** 3 (all MEDIUM)
**Action Items Created:** 5 (LOW)

### Action Items

- [ ] [Low] No test for `"[Assignment Not Found]"` sentinel path — add a test that creates an artifact with a non-existent assignment_id and verifies the sentinel appears in the HTTP response. [`apps/api/app/domains/grading/repository.py:557`]
- [ ] [Low] Test 21 missing `approved_at` assertion — add `assert grades[0]["approved_at"]` is non-empty to close the serialization regression gap. [`apps/api/tests/test_progress_api.py:663`]
- [ ] [Low] `_create_approved_grade_pipeline` helper should return `assignment` object — eliminates the 20-line manual pipeline rebuild in test 21. [`apps/api/tests/test_progress_api.py:48`]
- [ ] [Low] `approved_at` typed as `str` in `ApprovedGradeResponse` — consider `datetime` for automatic ISO 8601 serialization and client type safety. [`apps/api/app/domains/progress/schemas.py:14`]
- [ ] [Low] No assertion on `version` field in Story 3.2 tests — add `assert grades[0]["version"] == 1` to test 21 to guard integer serialization. [`apps/api/tests/test_progress_api.py:663`]
