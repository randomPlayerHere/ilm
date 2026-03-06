# Story 1.6: Baseline Safety and Content Control Configuration

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an admin,  
I want to configure baseline safety and content settings,  
so that organization defaults align with policy requirements.

## Acceptance Criteria

1. Given an authorized admin, when they set baseline safety/content controls for an organization, then the settings are saved and versioned, and new relevant workflows use those defaults.
2. Given a non-admin user, when they attempt to modify safety/content controls, then the system denies the action, and no configuration change is applied.

## Tasks / Subtasks

- [x] Implement baseline safety/content configuration API and service flow (AC: 1)
- [x] Add admin endpoint to create/update organization safety controls (recommended: `PUT /admin/organizations/{org_id}/safety-controls`).
- [x] Define typed request/response schemas for control payloads using Pydantic v2 with `extra=forbid`.
- [x] Validate payload and normalize persisted defaults (for example: moderation mode, blocked categories, age-safety level, max response tone strictness).
- [x] Persist control configuration as organization-scoped versioned records.

- [x] Enforce role and tenant authorization for configuration mutations (AC: 2)
- [x] Reuse centralized admin authorization dependency from story 1.5 (`require_admin_actor`) for write operations.
- [x] Ensure org scope is enforced server-side (`actor.org_id == target org_id`) and fails closed.
- [x] Return consistent denial semantics (`401` missing/invalid auth, `403` unauthorized).

- [x] Make safety controls consumable as defaults by downstream workflows (AC: 1)
- [x] Add service/repository read path to fetch latest effective safety controls for an org.
- [x] Expose safe read endpoint for authorized org actors (recommended: `GET /admin/organizations/{org_id}/safety-controls`).
- [x] Ensure read responses do not leak cross-tenant configuration.

- [x] Add versioning and auditability safeguards (AC: 1)
- [x] Record version metadata (`version`, `updated_by`, `updated_at`, `org_id`).
- [x] Add immutable audit event for control changes (`action: org.safety_controls.updated`).
- [x] Reject no-op invalid transitions or malformed payloads with explicit `400` validation errors.

- [x] Add tests for authorization, tenant isolation, and version behavior (AC: 1, 2)
- [x] Unit tests for validation rules and version increment behavior in service layer.
- [x] API tests for successful admin update/read and persisted defaults retrieval.
- [x] API tests proving non-admin denial (`403`) and unauthenticated rejection (`401`).
- [x] API tests proving cross-tenant access/update attempts fail closed (`403`) and never return foreign org data.

- [x] Update docs and handoff notes
- [x] Document new safety controls endpoints/contracts and defaulting behavior in `apps/api/README.md`.
- [x] Document configuration shape and extension guidance for upcoming AI stories (Epic 2).

## Dev Notes

- This story completes Epic 1 control-plane baseline before AI generation/grading stories in Epic 2.
- Keep implementation in current in-memory repository pattern; preserve interfaces so PostgreSQL migration can replace storage without route contract breaks.
- Do not introduce ad-hoc authorization checks inside route handlers; use centralized dependencies and service-layer policy paths.
- Safety controls are organization policy, not user preference; every record must be tenant-scoped and auditable.

### Technical Requirements

- Backend implementation under `apps/api` (FastAPI + Pydantic v2).
- Follow existing JWT claims contract (`sub`, `org_id`, `role`, `exp`) and persisted actor validation patterns.
- Persist versioned safety controls per organization with deterministic latest-version retrieval.
- New workflows that need baseline moderation/content defaults must consume latest effective org controls.
- Denial responses must preserve anti-enumeration and avoid leaking foreign tenant configuration.

### Architecture Compliance

- Align with architecture sections: `Security and Compliance Baseline`, `Authentication & Security`, `Implementation Patterns & Consistency Rules`.
- Route layer: request validation + dependency wiring only.
- Service layer: policy enforcement, versioning rules, business validation.
- Repository layer: org-scoped persistence and audit event recording.
- Keep naming and API semantics consistent with existing admin/auth endpoints.

### Library / Framework Requirements

- FastAPI range remains `>=0.115.0,<1.0.0`.
- Pydantic v2 request/response models and validation constraints.
- PyJWT path remains compatible with existing `pyjwt>=2.9.0,<3.0.0` security utilities.
- No new dependency required for this story.

### File Structure Requirements

- Implement API transport/service logic in:
- `apps/api/app/domains/admin/router.py`
- `apps/api/app/domains/admin/service.py`
- `apps/api/app/domains/admin/schemas.py`
- Extend persistence/audit paths in:
- `apps/api/app/domains/auth/repository.py`
- `apps/api/app/domains/auth/models.py` (if new record type needed)
- Add coverage in:
- `apps/api/tests/test_admin_api.py`
- `apps/api/tests/test_admin_service.py`

### Testing Requirements

- AC-mapped tests for create/update/read safety controls and versioning behavior.
- Authorization regression tests for non-admin and unauthenticated mutation attempts.
- Cross-tenant fail-closed tests for both read and write paths.
- Keep deterministic test setup with `InMemoryAuthRepository.reset_state()` and existing async API harness.

### Previous Story Intelligence

- Story 1.5 review hardened auth by requiring persisted actor role/org match and centralized protected org checks; reuse that exact pattern instead of route-local checks.
- Story 1.5 added role/membership mutation endpoints and proved stale-role tokens must be denied via persisted actor comparison; safety controls must rely on persisted actor state the same way.
- Story 1.4 and 1.5 established audit event recording conventions; keep sensitive admin mutations auditable with actor/target/org metadata.

### Git Intelligence Summary

- Repository history remains minimal (`015692c Initial update`), so implementation conventions should follow existing source layout and completed story artifacts.
- Current sprint progression indicates stories 1.1-1.5 are complete; story 1.6 should preserve backward compatibility with these implemented contracts and tests.

### Latest Tech Information

- FastAPI release notes list `0.135.1` in latest entries while project keeps compatibility range `>=0.115.0,<1.0.0`.  
  Source: <https://fastapi.tiangolo.com/release-notes/>
- Pydantic changelog lists `v2.12.5` (2025-11-26) in latest v2 line.  
  Source: <https://docs.pydantic.dev/changelog/>
- PyJWT stable changelog lists `v2.11.0` as latest released version.  
  Source: <https://pyjwt.readthedocs.io/en/stable/changelog.html>

### Project Context Reference

- No `project-context.md` file was found. Guidance derived from epics, architecture, PRD, UX specification, and completed stories 1.4-1.5.

### References

- [Source: _bmad-output/implementation-artifacts/epics.md#Story 1.6: Baseline Safety and Content Control Configuration]
- [Source: _bmad-output/implementation-artifacts/architecture.md#Security and Compliance Baseline]
- [Source: _bmad-output/implementation-artifacts/architecture.md#Authentication & Security]
- [Source: _bmad-output/implementation-artifacts/architecture.md#Implementation Patterns & Consistency Rules]
- [Source: _bmad-output/planning-artifacts/prd.md#Functional Requirements]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#MVP Screens]
- [Source: _bmad-output/implementation-artifacts/1-5-role-assignment-and-tenant-scoped-authorization-enforcement.md]
- [Source: https://fastapi.tiangolo.com/release-notes/]
- [Source: https://docs.pydantic.dev/changelog/]
- [Source: https://pyjwt.readthedocs.io/en/stable/changelog.html]

## Story Completion Status

- Story status set to `done`.
- Completion note: Implemented safety-controls configuration with review-driven authorization and validation hardening.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Sprint status parsed from `_bmad-output/implementation-artifacts/sprint-status.yaml`
- Story source extracted from `_bmad-output/implementation-artifacts/epics.md`
- Architecture constraints extracted from `_bmad-output/implementation-artifacts/architecture.md`
- PRD and UX constraints extracted from `_bmad-output/planning-artifacts/prd.md` and `_bmad-output/planning-artifacts/ux-design-specification.md`
- Previous story intelligence extracted from `_bmad-output/implementation-artifacts/1-5-role-assignment-and-tenant-scoped-authorization-enforcement.md`
- Latest framework/library references captured from official FastAPI, Pydantic, and PyJWT changelog pages
- Story scaffold generated and marked `ready-for-dev` with AC-mapped tasks and implementation guardrails.
- Updated sprint status for story `1-6` to `in-progress` at start of implementation.
- Added failing tests first for safety controls API/service flows (versioning, authn/authz, tenant fail-closed behavior).
- Implemented safety controls schemas, API endpoints, service validation/policy logic, and repository versioned persistence/audit recording.
- Validation run: `cd apps/api && ../../.venv/bin/python -m pytest -q tests/test_admin_service.py tests/test_admin_api.py` -> `24 passed`.
- Validation run: `cd apps/api && ../../.venv/bin/python -m pytest -q` -> `52 passed`.
- Validation run: `pnpm -s lint && pnpm -s test && pnpm -s typecheck` -> passed.
- Review fix: restricted safety-controls read endpoint to org-scoped `admin|principal|teacher` roles.
- Review fix: decoupled `SafetyControlsValidationError` from user-lifecycle error hierarchy.
- Added API regression test for no-op update rejection (`400`) and student-role safety-controls read denial (`403`).
- Validation run after review fixes: `cd apps/api && ../../.venv/bin/python -m pytest -q` -> `53 passed`.

### Completion Notes List

- Selected next backlog story from sprint status: `1-6-baseline-safety-and-content-control-configuration`.
- Generated implementation-ready story with explicit API, service, repository, and test expectations.
- Included prior-story review learnings to prevent authorization regressions and route-local policy drift.
- Added architecture and compliance constraints to guide secure baseline safety-control implementation.
- Implemented `PUT /admin/organizations/{org_id}/safety-controls` and `GET /admin/organizations/{org_id}/safety-controls` with strict org-scope enforcement.
- Added versioned safety-controls persistence with immutable audit event `org.safety_controls.updated`.
- Added no-op and malformed payload rejection with `400` semantics for invalid safety-controls changes.
- Added service and API regression tests for version increment, non-admin/unauthenticated denial, and cross-tenant fail-closed behavior.
- Updated API story metadata and README documentation for Story 1.6 contracts.
- ✅ Resolved review finding [High]: tightened safety-controls read authorization scope to explicit allowed roles to reduce policy disclosure.
- ✅ Resolved review finding [Medium]: removed cross-domain exception inheritance coupling for safety-controls validation errors.
- ✅ Resolved review finding [Medium]: added missing API-level regression coverage for no-op write rejection and student-role read denial.

### File List

- _bmad-output/implementation-artifacts/1-6-baseline-safety-and-content-control-configuration.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- apps/api/README.md
- apps/api/pyproject.toml
- apps/api/app/domains/admin/router.py
- apps/api/app/domains/admin/schemas.py
- apps/api/app/domains/admin/service.py
- apps/api/app/domains/auth/models.py
- apps/api/app/domains/auth/repository.py
- apps/api/tests/test_admin_api.py
- apps/api/tests/test_admin_service.py

## Change Log

- 2026-03-06: Created Story 1.6 implementation context with comprehensive acceptance criteria mapping, technical guardrails, and test requirements.
- 2026-03-06: Implemented Story 1.6 baseline safety-controls APIs with versioned org-scoped persistence, authorization safeguards, regression tests, and documentation updates.
- 2026-03-06: Senior adversarial code review completed; fixed all high/medium findings and re-ran full regression suite.

## Senior Developer Review (AI)

### Review Date

2026-03-06

### Reviewer

GPT-5 Codex

### Outcome

Approved

### Summary

- Findings identified: 1 High, 2 Medium, 0 Low
- Findings fixed in this review pass: 3
- Acceptance Criteria validation: all ACs implemented
- Task audit validation: all checked tasks verified against implementation

### Findings Resolved

- [x] [High] Safety-controls read endpoint allowed any authenticated same-org actor (including student role), expanding policy disclosure surface beyond intended operational roles.
- [x] [Medium] `SafetyControlsValidationError` inherited from `UserLifecycleError`, creating unnecessary domain coupling and confusing error taxonomy.
- [x] [Medium] Missing API-level regression for no-op update rejection and explicit student-role read denial on safety-controls endpoint.

### Validation Evidence

- `cd apps/api && ../../.venv/bin/python -m pytest -q` -> `53 passed`
- `pnpm -s lint` -> passed
- `pnpm -s test` -> passed
- `pnpm -s typecheck` -> passed
