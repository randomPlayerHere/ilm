# Story 2.1: Generate AI Draft Lesson and Curriculum Content

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a teacher,
I want to generate draft lesson and curriculum content with AI,
so that I can reduce planning time.

## Acceptance Criteria

1. Given an authenticated teacher with class context, when the teacher requests AI lesson generation, then the system creates a draft plan, and stores it as editable teacher-owned content.
2. Given generation fails, when the request is processed, then the teacher receives a clear retryable error, and no partial published content is created.

## Tasks / Subtasks

- [x] Implement teacher-scoped lesson draft generation endpoint and orchestration flow (AC: 1, 2)
- [x] Add a new courses domain with route and service boundaries (`apps/api/app/domains/courses/*`) aligned to architecture API boundaries.
- [x] Add endpoint for draft generation (recommended: `POST /courses/drafts/generate`) guarded by authenticated teacher role and org scope checks.
- [x] Validate class context exists in caller org before generation begins.

- [x] Implement AI generation request lifecycle with safe failure handling (AC: 1, 2)
- [x] Build request/response schemas with Pydantic v2 (`extra=forbid`) for input prompt/context and returned draft payload.
- [x] Implement service-layer generation adapter boundary (stubbed provider acceptable for initial story) returning deterministic draft structure.
- [x] Ensure failure responses are retryable and explicit (e.g., `503` provider unavailable / `502` upstream error) with no persisted half-created published records.

- [x] Persist editable teacher-owned draft lesson records (AC: 1)
- [x] Add repository persistence for generated drafts with ownership fields (`org_id`, `teacher_user_id`, `class_id`, timestamps).
- [x] Persist generated output as `draft` state only; do not publish in this story.
- [x] Ensure generated content is retrievable for later story 2.2 editing workflow.

- [x] Add authorization and tenant isolation safeguards (AC: 1, 2)
- [x] Reuse centralized auth/policy dependency patterns from Epic 1 (`require_protected_actor`, role checks, org scoping).
- [x] Deny non-teacher role access to generation endpoint with consistent `403` semantics.
- [x] Ensure cross-tenant class IDs are rejected fail-closed.

- [x] Add tests for generation success path and failure safety (AC: 1, 2)
- [x] Unit tests for service behavior: valid generation, provider failure mapping, and draft-only persistence rules.
- [x] API tests for authenticated teacher success, invalid class context, non-teacher denial, and cross-tenant denial.
- [x] API tests confirming generation failure returns retryable error and does not create a published record.

- [x] Document API and domain contract decisions
- [x] Update `apps/api/README.md` with generation endpoint, payloads, and draft-state semantics.
- [x] Add short notes for next story (2.2) on editable draft retrieval/update expectations.

### Review Follow-ups (AI)

- [x] [AI-Review][High] Normalize class lookup denial semantics to prevent tenant/resource enumeration (`class not found` currently returns 400 while cross-tenant class returns 403). Return a single fail-closed response pattern for unauthorized/unknown class access. [apps/api/app/domains/courses/service.py:73]
- [x] [AI-Review][Medium] Remove cross-domain auth dependency from courses router (`app.domains.admin.router`) and move shared actor/auth dependency to a neutral shared module under `app/core` or `app/domains/auth`. [apps/api/app/domains/courses/router.py:5]
- [x] [AI-Review][Medium] Add explicit API authorization tests for `GET /courses/drafts` and `GET /courses/drafts/{draft_id}` to verify non-teacher roles are denied and access control remains fail-closed. [apps/api/tests/test_courses_api.py:52]

## Dev Notes

- This is the first story of Epic 2 and establishes the curriculum generation baseline consumed by 2.2 and later teacher workflow stories.
- Story scope is draft generation only; publish flow and student-specific variant editing are out of scope for 2.1.
- Keep architecture consistency with existing domain layering from Epic 1 (router/service/repository separation, centralized authorization checks).

### Technical Requirements

- Implement backend in FastAPI under `apps/api` with explicit domain boundaries.
- Enforce authenticated teacher + tenant-scoped class access before generation.
- Persist generated output as editable teacher-owned draft content.
- Provide retryable, non-ambiguous errors on generation failures.
- Do not expose generated content to parent/student surfaces in this story.

### Architecture Compliance

- Follow architecture sections: `API Boundaries (MVP)`, `Authentication & Security`, and `Implementation Patterns & Consistency Rules`.
- Route layer should do request validation and dependency injection only.
- Service layer should orchestrate generation, validation, and failure mapping.
- Repository layer should own persistence and tenant-scoped queries.
- Keep endpoint and payload naming consistent with existing conventions.

### Library / Framework Requirements

- FastAPI stays within configured range `>=0.115.0,<1.0.0`.
- Pydantic v2 schema validation for request/response models.
- PyJWT-based auth flow must remain compatible with existing auth stack.
- Uvicorn/dev runtime assumptions unchanged.
- Avoid introducing new AI SDK dependency in this story unless required; isolate provider behind adapter boundary.

### File Structure Requirements

- New domain files (recommended):
- `apps/api/app/domains/courses/__init__.py`
- `apps/api/app/domains/courses/router.py`
- `apps/api/app/domains/courses/service.py`
- `apps/api/app/domains/courses/schemas.py`
- `apps/api/app/domains/courses/repository.py`
- API route registration updates in:
- `apps/api/app/main.py`
- Test coverage additions in:
- `apps/api/tests/test_courses_api.py`
- `apps/api/tests/test_courses_service.py`

### Testing Requirements

- AC-mapped tests for successful draft generation and persistence under teacher context.
- Authorization tests for non-teacher and cross-tenant attempts.
- Failure tests proving retryable error responses and no published/partial record creation.
- Regression checks ensuring existing auth/admin tests remain green.

### Git Intelligence Summary

- Existing implementation patterns are concentrated in `auth` and `admin` domains from Epic 1.
- Use the same dependency-based authorization and layered structure patterns rather than introducing ad-hoc policy checks.

### Latest Tech Information

- FastAPI release notes show latest published entry `0.135.1` in current release list, and the project's dependency range already permits compatible updates inside `<1.0.0`.
  Source: <https://fastapi.tiangolo.com/release-notes/>
- Pydantic changelog currently lists `v2.12.5` in the v2 series; project range `>=2.8.0,<3.0.0` remains compatible.
  Source: <https://docs.pydantic.dev/changelog/>
- PyJWT changelog currently lists `v2.11.0`; project range `>=2.9.0,<3.0.0` remains compatible.
  Source: <https://pyjwt.readthedocs.io/en/stable/changelog.html>

### Project Context Reference

- No `project-context.md` file was found. Story context is grounded in epics, PRD, UX design spec, architecture, and existing Epic 1 implementation artifacts.

### References

- [Source: _bmad-output/implementation-artifacts/epics.md#Story 2.1: Generate AI Draft Lesson and Curriculum Content]
- [Source: _bmad-output/planning-artifacts/prd.md#Functional Requirements]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Core Flows]
- [Source: _bmad-output/implementation-artifacts/architecture.md#API Boundaries (MVP)]
- [Source: _bmad-output/implementation-artifacts/architecture.md#Authentication & Security]
- [Source: _bmad-output/implementation-artifacts/architecture.md#Implementation Patterns & Consistency Rules]
- [Source: _bmad-output/implementation-artifacts/1-6-baseline-safety-and-content-control-configuration.md]
- [Source: https://fastapi.tiangolo.com/release-notes/]
- [Source: https://docs.pydantic.dev/changelog/]
- [Source: https://pyjwt.readthedocs.io/en/stable/changelog.html]

## Story Completion Status

- Story status set to `done`.
- Completion note: Story implemented and review follow-ups resolved; code review approved.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Implementation Plan

- Added a new `courses` domain with router/service/repository layers to match existing Epic 1 architecture patterns.
- Implemented authenticated teacher-only draft generation and retrieval paths with org and class ownership guards.
- Added deterministic stub generator with explicit retryable provider-unavailable path and draft-only persistence.
- Added unit and API tests covering success, authorization, tenant isolation, invalid class context, and provider failure safety.

### Debug Log References

- Sprint status parsed from `_bmad-output/implementation-artifacts/sprint-status.yaml`
- Story source extracted from `_bmad-output/implementation-artifacts/epics.md`
- Architecture constraints extracted from `_bmad-output/implementation-artifacts/architecture.md`
- PRD and UX constraints extracted from `_bmad-output/planning-artifacts/prd.md` and `_bmad-output/planning-artifacts/ux-design-specification.md`
- Latest framework/library references captured from official FastAPI, Pydantic, and PyJWT changelog pages
- Red phase validation: `cd apps/api && ../../.venv/bin/python -m pytest -q tests/test_courses_service.py tests/test_courses_api.py` (failed: missing `app.domains.courses`)
- Green phase validation: `cd apps/api && ../../.venv/bin/python -m pytest -q tests/test_courses_service.py tests/test_courses_api.py` (passed: 6)
- Regression suite: `cd apps/api && ../../.venv/bin/python -m pytest -q` (passed: 59)
- Workspace quality gates: `pnpm -s lint && pnpm -s test && pnpm -s typecheck` (passed)

### Completion Notes List

- Selected next backlog story from sprint status: `2-1-generate-ai-draft-lesson-and-curriculum-content`.
- Implemented `POST /courses/drafts/generate` with teacher-role gating and tenant-safe class validation.
- Added draft retrieval endpoints (`GET /courses/drafts/{draft_id}`, `GET /courses/drafts`) to support Story 2.2 editing workflows.
- Implemented deterministic stub AI generation adapter with retryable provider-unavailable behavior and no partial persistence on failure.
- Added `courses` repository persistence for draft-only lesson plans with owner/org/class metadata.
- Added service-level and API-level tests for success, invalid class context, non-teacher denial, cross-tenant denial, and provider failure safety.
- Updated API README and story metadata (`tool.ilm`) to reflect Story 2.1 scope.
- ✅ Resolved review finding [High]: fail-closed class lookup behavior now returns forbidden semantics for unknown and cross-tenant classes.
- ✅ Resolved review finding [Medium]: moved shared actor/auth dependency into `app.domains.auth.dependencies` and removed courses->admin dependency.
- ✅ Resolved review finding [Medium]: added read-endpoint authorization tests for `GET /courses/drafts` and `GET /courses/drafts/{draft_id}`.

### File List

- _bmad-output/implementation-artifacts/2-1-generate-ai-draft-lesson-and-curriculum-content.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- apps/api/README.md
- apps/api/pyproject.toml
- apps/api/app/main.py
- apps/api/app/domains/admin/router.py
- apps/api/app/domains/auth/dependencies.py
- apps/api/app/domains/courses/__init__.py
- apps/api/app/domains/courses/repository.py
- apps/api/app/domains/courses/router.py
- apps/api/app/domains/courses/schemas.py
- apps/api/app/domains/courses/service.py
- apps/api/tests/test_courses_api.py
- apps/api/tests/test_courses_service.py

## Change Log

- 2026-03-10: Implemented Story 2.1 teacher-scoped AI lesson draft generation with draft-state persistence, authorization guardrails, and comprehensive API/service tests.
- 2026-03-10: Senior adversarial code review completed; 1 high and 2 medium issues identified, with AI review follow-up tasks added.
- 2026-03-10: Addressed code review findings - 3 items resolved (High: 1, Medium: 2); story returned to review.
- 2026-03-10: Final adversarial review pass completed with approval; story moved to done.

## Senior Developer Review (AI)

### Review Date

2026-03-10

### Reviewer

GPT-5 Codex

### Outcome

Approved

### Summary

- Findings identified: 0 High, 0 Medium, 0 Low (after follow-up fixes)
- Git/story discrepancy check: no critical mismatch; source file list aligns with current implementation scope.
- Acceptance Criteria validation: fully implemented and verified via tests.

### Key Findings

- Resolved: fail-closed class lookup behavior now uses uniform forbidden semantics for unknown and cross-tenant class access.
- Resolved: shared auth dependency moved to `app.domains.auth.dependencies`, removing cross-domain courses->admin dependency.
- Resolved: explicit authorization coverage added for `GET /courses/drafts` and `GET /courses/drafts/{draft_id}` (non-teacher and unauthenticated denial).
