# Story 1.4: Organization and User Lifecycle Administration

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an admin,  
I want to create organizations and manage user lifecycle states,  
so that I can onboard and control access for schools and staff.

## Acceptance Criteria

1. Given an admin with org-management permission, when they create an organization, then the org is persisted with a unique identifier, and is available for membership assignment.
2. Given an admin managing users, when they invite, activate, or deactivate a user, then the lifecycle state is updated successfully, and deactivated users cannot access protected resources.
3. Given an invited user accepts onboarding, when org membership is assigned, then their account is linked to the target organization.

## Tasks / Subtasks

- [x] Implement admin organization management API surface in `apps/api` (AC: 1)
- [x] Add `POST /admin/organizations` with request validation for org identity fields and uniqueness constraints.
- [x] Add service/repository flow that persists org records with stable `org_id`.
- [x] Add response contract suitable for downstream membership assignment workflows.
- [x] Implement user lifecycle management operations (AC: 2)
- [x] Add admin endpoint(s) for invite, activate, and deactivate lifecycle transitions (`/admin/users/*`).
- [x] Define user status transition rules in one service layer (no ad-hoc route logic).
- [x] Ensure deactivated users are blocked across both `POST /auth/login` and `POST /auth/google`.
- [x] Implement invitation acceptance and org membership assignment (AC: 3)
- [x] Add onboarding acceptance path that binds invited account to the target organization.
- [x] Enforce fail-closed behavior when invitation token is invalid/expired/already used.
- [x] Record audit-ready metadata for lifecycle and membership changes (actor, org, timestamp, action).
- [x] Add automated tests for AC coverage and regressions (AC: 1, 2, 3)
- [x] API tests for org creation success + duplicate conflict path.
- [x] API/service tests for invite, activate, deactivate transitions and invalid transition attempts.
- [x] Auth regression tests proving deactivated users cannot obtain tokens from email/password or Google flows.
- [x] Invitation acceptance tests for success, expired token, wrong-org token, and replay protection.
- [x] Update API docs and developer notes
- [x] Document new admin endpoints and expected role/permission requirements in `apps/api/README.md`.
- [x] Document lifecycle state model and membership assignment contract for future stories (1.5/1.6 dependencies).

## Dev Notes

- This story extends the existing auth baseline from Stories 1.2 and 1.3 and must not fork token semantics or role-home mapping contracts.
- Keep authorization and tenant checks centralized; avoid embedding policy rules directly in route handlers.
- Story 1.5 depends on this story's organization/user lifecycle primitives. Keep APIs and status transitions explicit and test-backed.
- Current implementation is in-memory-first. Preserve repository interfaces so persistence migration to PostgreSQL can be introduced without route contract churn.

### Technical Requirements

- Backend implementation in FastAPI under `apps/api`.
- Preserve existing auth claims model (`sub`, `org_id`, `role`, `exp`) issued by shared security utilities.
- Lifecycle statuses must be explicit and validated (at minimum: invited, active, deactivated).
- Admin-only operations require server-side role checks before mutation.
- Deactivated users must fail authentication uniformly (no leakage of account status details).
- Invitation acceptance flow must prevent token replay and cross-org assignment.

### Architecture Compliance

- Follow architecture decision: centralized policy enforcement for role + tenant checks.
- Keep domain boundaries clear:
- Route layer: request validation + transport concerns.
- Service layer: lifecycle and permission decisions.
- Repository layer: persistence operations and uniqueness constraints.
- Respect API boundary patterns in architecture (`/auth/*`, `/admin/*`, `/users/*`) and keep contracts consistent with normalized error envelope conventions where introduced.
- Record auditable events for role/user/org lifecycle changes consistent with compliance baseline (FR35-FR37 direction).

### Library / Framework Requirements

- FastAPI (existing range: `>=0.115.0,<1.0.0`) for endpoints/dependencies.
- Pydantic v2 models for admin request/response schemas and lifecycle validation.
- Existing JWT + bcrypt + Google OIDC integrations remain authoritative for authentication.
- Keep dependency additions minimal and justified; reuse established project libraries before introducing new ones.

### File Structure Requirements

- Keep new implementation under `apps/api` with existing project organization:
- `apps/api/app/main.py` for router registration.
- `apps/api/app/domains/admin/*` for org/user lifecycle endpoints and services.
- `apps/api/app/domains/auth/*` only for targeted auth-guard changes needed to block deactivated users.
- `apps/api/tests/*` for API/service regressions.
- If shared schema contracts are required by clients, place generated/shared contracts under `packages/contracts`.

### Testing Requirements

- Add AC-mapped tests for organization creation uniqueness and lifecycle transitions.
- Add auth regression coverage confirming deactivated users are denied in both login paths.
- Add invitation acceptance tests for one-time token use and org-link correctness.
- Keep test harness aligned with current stable pattern (`httpx.ASGITransport` + async tests where applicable).
- Keep deterministic local tests with no dependency on live external providers.

### Previous Story Intelligence

- Story 1.3 established stable Google identity linking rules (`google_sub` immutability) and role/active-user checks; do not bypass these checks in admin lifecycle changes.
- Story 1.3 hardened invalid-token throttling keyed by requester host. Preserve rate-limit behavior and avoid introducing alternate failure channels that leak internals.
- Story 1.2 established centralized JWT issuance and role-home mapping contracts. Reuse existing helpers rather than adding parallel token code.
- Existing codebase uses in-memory repository patterns for auth domain. Match that abstraction style for admin/org lifecycle to enable incremental persistence.

### Git Intelligence Summary

- Repository commit history is minimal (`015692c Initial update`); conventions should be taken from current code and existing completed story artifacts rather than commit evolution.

### Latest Tech Information

- FastAPI official release notes currently list `0.121.1` (newer than project minimum range baseline). Keep implementation compatible with current `>=0.115.0,<1.0.0` constraint unless explicit upgrade is planned.
- Pydantic official changelog currently lists `v2.12.5`; continue using Pydantic v2 idioms already present in the codebase.
- PyJWT official changelog currently lists `v2.11.0`; ensure token handling changes stay compatible with the existing `pyjwt>=2.9.0,<3.0.0` range.
- For this story, do not introduce dependency upgrades as side effects; prioritize lifecycle feature delivery and regression safety.

### Project Context Reference

- No `project-context.md` found. Guidance derived from epics, architecture, PRD, UX specification, and Story 1.3 artifact.

### References

- [Source: _bmad-output/implementation-artifacts/epics.md#Story 1.4: Organization and User Lifecycle Administration]
- [Source: _bmad-output/implementation-artifacts/architecture.md#API Boundaries (MVP)]
- [Source: _bmad-output/implementation-artifacts/architecture.md#Authentication & Security]
- [Source: _bmad-output/implementation-artifacts/architecture.md#Implementation Patterns & Consistency Rules]
- [Source: _bmad-output/planning-artifacts/prd.md#Functional Requirements]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Information Architecture]
- [Source: _bmad-output/implementation-artifacts/1-3-google-sign-in-for-organization-users.md]
- [Source: https://fastapi.tiangolo.com/release-notes/]
- [Source: https://docs.pydantic.dev/latest/changelog/]
- [Source: https://pyjwt.readthedocs.io/en/latest/changelog.html]

## Story Completion Status

- Story status set to `review`.
- Completion note: Implemented admin organization and user lifecycle APIs with invitation onboarding and auth enforcement regression coverage.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Sprint status parsed from `_bmad-output/implementation-artifacts/sprint-status.yaml`
- Story source extracted from `_bmad-output/implementation-artifacts/epics.md`
- Architecture constraints extracted from `_bmad-output/implementation-artifacts/architecture.md`
- PRD and UX constraints extracted from `_bmad-output/planning-artifacts/prd.md` and `_bmad-output/planning-artifacts/ux-design-specification.md`
- Previous story intelligence extracted from `_bmad-output/implementation-artifacts/1-3-google-sign-in-for-organization-users.md`
- Repository/package constraints checked from `apps/api/pyproject.toml` and current auth implementation files
- Added failing tests first in `apps/api/tests/test_admin_api.py` for organization creation, lifecycle transitions, invitation acceptance, and fail-closed cases.
- Implemented admin domain under `apps/api/app/domains/admin/*` with role-gated endpoints and service orchestration.
- Extended `InMemoryAuthRepository` to support organizations, invitations, lifecycle state changes, and audit-event recording.
- Wired admin router in `apps/api/app/main.py` and added test-state reset helper in auth router for deterministic runs.
- Added admin service unit tests in `apps/api/tests/test_admin_service.py`.
- Validation run: `cd apps/api && ../../.venv/bin/python -m pytest -q` -> `37 passed`.
- Validation run: `pnpm -s lint && pnpm -s test && pnpm -s typecheck` -> passed.

### Completion Notes List

- Implemented `POST /admin/organizations`, `POST /admin/users/invite`, `POST /admin/users/{user_id}/activate`, `POST /admin/users/{user_id}/deactivate`, and `POST /admin/invitations/accept` with admin-role server-side enforcement.
- Added in-memory organization persistence with unique slug checks and stable `org_id` generation for membership assignment workflows.
- Implemented invite -> accept onboarding path that links invited users to target organizations and transitions user status to `active`.
- Added fail-closed invitation handling for invalid, expired, wrong-org, and replayed tokens.
- Implemented lifecycle transitions (`invited`, `active`, `deactivated`) in a centralized service/repository path, preventing ad-hoc route-level state logic.
- Added audit-event recording metadata for organization and user lifecycle actions.
- Verified auth regressions: deactivated users are denied via both email/password and Google sign-in endpoints.
- Added/updated API and service tests to cover AC flows and edge cases.
- Updated API README and module metadata to document story 1.4 contracts.
- ✅ Resolved review finding [High]: enforce persisted-actor validation in admin authorization to block stale/deactivated admin tokens.
- ✅ Resolved review finding [Medium]: validate JWT subject exists and remains admin in repository before granting admin access.
- ✅ Resolved review finding [Medium]: return `404` (not generic `400`) for unknown user lifecycle targets.

### File List

- _bmad-output/implementation-artifacts/1-4-organization-and-user-lifecycle-administration.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- apps/api/README.md
- apps/api/pyproject.toml
- apps/api/app/main.py
- apps/api/app/domains/admin/__init__.py
- apps/api/app/domains/admin/router.py
- apps/api/app/domains/admin/schemas.py
- apps/api/app/domains/admin/service.py
- apps/api/app/domains/auth/models.py
- apps/api/app/domains/auth/repository.py
- apps/api/app/domains/auth/router.py
- apps/api/tests/test_admin_api.py
- apps/api/tests/test_admin_service.py
- apps/api/tests/test_auth_google_api.py
- apps/api/tests/test_auth_login_api.py

## Change Log

- 2026-03-06: Implemented Story 1.4 admin organization and user lifecycle APIs, added invitation onboarding flow, enforced auth-state deactivation behavior, and added full regression/unit coverage.
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

- [x] [High] Admin endpoints accepted stale/deactivated admin JWTs without checking persisted actor state, allowing protected access until token expiry.
- [x] [Medium] Admin authorization trusted role claim without verifying the `sub` identity existed and remained admin in persisted data.
- [x] [Medium] Lifecycle endpoints returned ambiguous `400` responses for unknown users instead of `404`, reducing client correctness and observability.

### Validation Evidence

- `cd apps/api && ../../.venv/bin/python -m pytest -q` -> `40 passed`
- `pnpm -s lint` -> passed
- `pnpm -s test` -> passed
- `pnpm -s typecheck` -> passed
