# Story 1.5: Role Assignment and Tenant-Scoped Authorization Enforcement

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an admin,  
I want to assign roles and enforce tenant boundaries,  
so that users can only perform actions allowed for their role within their organization.

## Acceptance Criteria

1. Given an admin assigns or updates a user role, when the change is saved, then subsequent authorization checks use the updated role, and forbidden actions return access denied.
2. Given a user requests protected data from another organization, when authorization is evaluated, then the request fails closed, and no cross-tenant data is returned.
3. Given protected API operations, when any request is processed, then server-side role and org-scope checks are always executed, and unauthenticated/unauthorized requests are rejected.

## Tasks / Subtasks

- [x] Implement admin role assignment API and service path (AC: 1)
- [x] Add endpoint to assign/update role for a target user (recommended: `POST /admin/users/{user_id}/role`).
- [x] Validate role values against centralized supported-role map (`app/core/roles.py`) and reject unsupported roles.
- [x] Persist role updates in repository and ensure subsequent auth/authorization logic reads updated role data.
- [x] Add audit event metadata for role changes (`actor_id`, `target_id`, `org_id`, `action`, `occurred_at`).

- [x] Implement tenant membership and org-scope enforcement primitives (AC: 2, 3)
- [x] Add/update membership assignment endpoint(s) to bind users to organizations (recommended: `POST /admin/users/{user_id}/membership`).
- [x] Ensure org-scoped authorization checks are centralized in reusable dependency/policy helpers, not route-local ad-hoc logic.
- [x] Add a protected sample resource endpoint (or guard existing protected endpoint) that enforces `org_id` match from auth context to requested data scope.
- [x] Ensure cross-tenant access attempts fail closed with no data leakage and consistent denial semantics.

- [x] Enforce role + org checks for protected operations end-to-end (AC: 1, 2, 3)
- [x] Ensure protected endpoints reject missing/invalid JWT with `401`.
- [x] Ensure authenticated users lacking role permission or org scope receive `403`.
- [x] Ensure role changes are reflected immediately in downstream authorization decisions (no stale role behavior).
- [x] Keep anti-enumeration behavior and safe auth error semantics from Stories 1.2-1.4.

- [x] Add tests for role assignment, authorization gates, and tenant isolation (AC: 1, 2, 3)
- [x] Unit tests for role update validation and persistence paths in service layer.
- [x] Integration/API tests for forbidden action behavior after role downgrade or unsupported role assignment attempts.
- [x] Integration/API tests for cross-tenant data access attempts proving fail-closed behavior and no payload leakage.
- [x] Regression tests for unauthenticated (`401`) and unauthorized (`403`) handling on protected operations.

- [x] Update docs and handoff notes
- [x] Document role assignment and membership endpoints/contracts in `apps/api/README.md`.
- [x] Document authorization policy expectations for future stories that add protected resources.

## Dev Notes

- Story 1.4 introduced admin lifecycle and invitation flow; reuse those repository/service structures and avoid duplicating identity/admin logic.
- Authorization checks must remain server-side and centralized. Do not trust client role/org claims without persisted actor validation.
- This story is a hard prerequisite for secure implementation of later protected domains (`/students`, `/messages`, `/notifications`, `/org-analytics`).
- Current repository is in-memory-first; preserve interfaces and separation so PostgreSQL migration can swap storage later without route contract breakage.

### Technical Requirements

- Backend implementation under `apps/api` (FastAPI + Pydantic v2).
- Continue using JWT claims (`sub`, `org_id`, `role`, `exp`) from existing security utilities.
- Role enforcement must rely on centralized supported-role definitions and persisted user state.
- Tenant checks must validate request org scope against authenticated actor context and fail closed.
- No protected endpoint may bypass role + org authorization checks.
- Denial responses must not expose unauthorized tenant data or sensitive internals.

### Architecture Compliance

- Align with architecture sections: `Authentication & Security`, `API Boundaries`, `Implementation Patterns & Consistency Rules`.
- Keep domain boundaries clear:
- Route layer: transport + schema validation + dependency wiring only.
- Service/policy layer: role and org-scope authorization decisions.
- Repository layer: role/membership persistence and lookup.
- Follow consistent API naming and error semantics; avoid introducing divergent authz conventions.
- Preserve auditability expectations for sensitive actions (role updates and membership changes).

### Library / Framework Requirements

- FastAPI: project baseline range remains `>=0.115.0,<1.0.0` (current docs list newer releases).
- Pydantic v2 for request/response schemas and validation.
- PyJWT-based token decode path already in use; authorization changes must remain compatible with current `pyjwt>=2.9.0,<3.0.0`.
- No new dependency is required for this story; prefer existing stack.

### File Structure Requirements

- Implement within existing API structure:
- `apps/api/app/domains/admin/*` for admin role/membership mutations.
- `apps/api/app/domains/auth/*` only where auth context and authorization guard reuse is required.
- `apps/api/app/core/*` for shared role/authorization helper utilities.
- `apps/api/tests/*` for unit/integration authorization and tenant-isolation tests.
- Keep `apps/api/app/main.py` router wiring consistent with current module layout.

### Testing Requirements

- Add AC-mapped tests for role assignment and immediate authorization effect.
- Add explicit cross-tenant denial tests for protected resources (no data returned).
- Add tests proving protected endpoints always execute server-side role/org checks.
- Keep deterministic test setup with existing in-memory reset pattern.
- Maintain stable async API test harness pattern (`httpx.ASGITransport` + async client).

### Previous Story Intelligence

- Story 1.4 already added persisted-actor validation for admin endpoints; extend that pattern to role/membership operations.
- Story 1.4 review fixes ensured stale/deactivated admin JWTs are rejected; do not regress this behavior.
- Story 1.3 established Google identity-link integrity and active-user checks; role enforcement must remain consistent across both login paths.
- Story 1.2 established centralized JWT issuance and generic auth failure behavior; keep anti-enumeration and token contract unchanged.

### Git Intelligence Summary

- Git history still shows minimal commit history (`015692c Initial update`), so implementation conventions should continue to follow current source layout and completed story artifacts rather than commit evolution.

### Latest Tech Information

- FastAPI release notes currently show `0.135.1` in latest entries (current project remains pinned to a compatible lower range).  
  Source: <https://fastapi.tiangolo.com/release-notes/>
- Pydantic changelog currently lists `v2.12.5` (2025-11-26) as latest patch release in the 2.12 line.  
  Source: <https://docs.pydantic.dev/changelog/>
- PyJWT stable changelog page currently documents `v2.11.0` as latest released version with additional unreleased fixes listed separately.  
  Source: <https://pyjwt.readthedocs.io/en/stable/changelog.html>

### Project Context Reference

- No `project-context.md` file was found. Guidance derived from epics, architecture, PRD, UX specification, and completed Stories 1.2-1.4.

### References

- [Source: _bmad-output/implementation-artifacts/epics.md#Story 1.5: Role Assignment and Tenant-Scoped Authorization Enforcement]
- [Source: _bmad-output/implementation-artifacts/architecture.md#Authentication & Security]
- [Source: _bmad-output/implementation-artifacts/architecture.md#API Boundaries (MVP)]
- [Source: _bmad-output/implementation-artifacts/architecture.md#Implementation Patterns & Consistency Rules]
- [Source: _bmad-output/planning-artifacts/prd.md#Functional Requirements]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#UX Requirements]
- [Source: _bmad-output/implementation-artifacts/1-4-organization-and-user-lifecycle-administration.md]
- [Source: https://fastapi.tiangolo.com/release-notes/]
- [Source: https://docs.pydantic.dev/changelog/]
- [Source: https://pyjwt.readthedocs.io/en/stable/changelog.html]

## Story Completion Status

- Story status set to `done`.
- Completion note: Implemented role assignment, membership binding, and tenant-scoped protected authorization with review-driven hardening and regression coverage.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Sprint status parsed from `_bmad-output/implementation-artifacts/sprint-status.yaml`
- Story source extracted from `_bmad-output/implementation-artifacts/epics.md`
- Architecture constraints extracted from `_bmad-output/implementation-artifacts/architecture.md`
- PRD and UX constraints extracted from `_bmad-output/planning-artifacts/prd.md` and `_bmad-output/planning-artifacts/ux-design-specification.md`
- Previous story intelligence extracted from `_bmad-output/implementation-artifacts/1-4-organization-and-user-lifecycle-administration.md`
- Latest framework/library context verified from official FastAPI, Pydantic, and PyJWT changelog pages
- Updated sprint status for story `1-5` to `in-progress` at start of implementation.
- Added failing tests first for role assignment, membership assignment, protected resource authn/authz, and cross-tenant denial.
- Implemented repository methods for role update and membership assignment with audit event recording.
- Implemented service-layer role/membership APIs and protected org-summary retrieval.
- Added admin router endpoints for `/admin/users/{user_id}/role`, `/admin/users/{user_id}/membership`, and `/admin/protected/organizations/{org_id}/summary`.
- Added centralized authenticated-actor guard enforcing persisted actor role/org/status with 401/403 separation.
- Validation run: `cd apps/api && ../../.venv/bin/python -m pytest -q` -> `45 passed`.
- Review fix: centralized protected org authorization into reusable dependency (`require_authorized_org_actor`) and removed route-local role/org checks.
- Review fix: tightened admin token requirements to reject missing org scope and enforce strict persisted-org/token-org match.
- Added regression tests for invalid JWT on protected endpoint, stale-role-token denial after role downgrade, and admin token missing org scope rejection.
- Validation run after review fixes: `cd apps/api && ../../.venv/bin/python -m pytest -q` -> `48 passed`.
- Validation run: `pnpm -s lint && pnpm -s test && pnpm -s typecheck` -> passed.

### Completion Notes List

- Implemented `POST /admin/users/{user_id}/role` with supported-role validation and immediate persisted-role effect on authorization checks.
- Implemented `POST /admin/users/{user_id}/membership` to bind users to organizations with org existence validation.
- Implemented `GET /admin/protected/organizations/{org_id}/summary` as a protected sample endpoint enforcing role + org scope (`admin|principal` + matching org).
- Added tenant fail-closed behavior for cross-org access attempts with explicit no-data leakage (`403 Forbidden`).
- Added authn/authz guard behavior guaranteeing protected endpoints return `401` for missing/invalid tokens and `403` for unauthorized actors.
- Added/updated tests covering role assignment, unsupported roles, membership assignment, protected endpoint authorization, and cross-tenant denials.
- Updated API README and module metadata to document Story 1.5 contracts.
- ✅ Resolved review finding [High]: remove route-local protected role/org checks and centralize authorization policy in a reusable dependency helper.
- ✅ Resolved review finding [Medium]: reject admin JWTs missing `org_id` claim and require strict persisted actor org/token org consistency.
- ✅ Resolved review finding [Medium]: add explicit regression coverage for stale role claims after role downgrade and invalid JWT handling.

### File List

- _bmad-output/implementation-artifacts/1-5-role-assignment-and-tenant-scoped-authorization-enforcement.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- apps/api/README.md
- apps/api/pyproject.toml
- apps/api/app/domains/admin/router.py
- apps/api/app/domains/admin/schemas.py
- apps/api/app/domains/admin/service.py
- apps/api/app/domains/auth/repository.py
- apps/api/tests/test_admin_api.py
- apps/api/tests/test_admin_service.py

## Change Log

- 2026-03-06: Implemented role assignment and tenant-scoped authorization enforcement, added protected org-scope endpoint, expanded admin/auth tests, and validated full regression suite.
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

- [x] [High] Protected org-summary route still used ad-hoc route-local role/org checks instead of a reusable centralized authorization dependency.
- [x] [Medium] Admin authorization accepted JWTs without `org_id`, weakening tenant-scope guarantees for admin endpoints.
- [x] [Medium] Missing regression tests for stale-role-token denial after role downgrade and invalid JWT handling on protected endpoint.

### Validation Evidence

- `cd apps/api && ../../.venv/bin/python -m pytest -q` -> `48 passed`
- `pnpm -s lint` -> passed
- `pnpm -s test` -> passed
- `pnpm -s typecheck` -> passed
