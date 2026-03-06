# Story 1.2: Email/Password Sign-In for Organization Users

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a school user,  
I want to sign in with email and password,  
so that I can securely access Teacher OS.

## Acceptance Criteria

1. Given an active user account with valid credentials, when the user submits email/password, then the system authenticates and returns a valid session token, and the user lands on their role-appropriate home view.
2. Given invalid credentials, when the user attempts sign-in, then access is denied, and the error response does not reveal whether email or password was incorrect.

## Tasks / Subtasks

- [x] Implement credential sign-in API in `apps/api` (AC: 1, 2)
  - [x] Add `POST /auth/login` endpoint with request schema (`email`, `password`) and strict validation.
  - [x] Lookup user by normalized email and require `status=active` before issuing token.
  - [x] Verify password using a secure hash strategy (Argon2id or bcrypt as architecture allows).
  - [x] Return JWT access token and metadata needed for role-aware client routing.
- [x] Enforce secure failure behavior and anti-enumeration responses (AC: 2)
  - [x] Use a single generic auth failure response for invalid email/password combinations.
  - [x] Ensure status code and message do not leak account existence.
  - [x] Add conservative login throttling/rate-limit hook points for brute-force protection.
- [x] Implement role-appropriate post-login destination contract (AC: 1)
  - [x] Include role and org context claims required for role-based home routing.
  - [x] Define canonical role-to-home mapping in one shared location to avoid drift.
  - [x] Validate that unauthorized or deactivated users cannot obtain valid session tokens.
- [x] Add automated tests for auth and security behavior (AC: 1, 2)
  - [x] Unit tests: password verification, status checks, token payload composition.
  - [x] Integration tests: success login, invalid password, unknown user, inactive user.
  - [x] Security test: failed responses are indistinguishable for wrong email vs wrong password.
- [x] Update implementation docs and handoff notes (AC: 1, 2)
  - [x] Document environment variables and token settings for local development.
  - [x] Document endpoint contract and expected client routing behavior.

## Dev Notes

- Story scope is email/password authentication only; Google OAuth belongs to Story 1.3.
- Keep tenant-safe and role-safe posture from day one: auth success must carry org + role context required by policy checks.
- Centralize security behavior (hash verification, token generation, auth error shape) to avoid inconsistent implementations later.

### Technical Requirements

- Backend is FastAPI in `apps/api`.
- Use JWT-based sessions with short-lived access tokens, consistent with architecture security baseline.
- Enforce role-based access prerequisites and organization scoping claims at sign-in boundary.
- Require active account status before granting token.

### Architecture Compliance

- Implement within `apps/api/app/domains/auth` and shared security utilities under `app/core/*` per architecture guidance.
- Keep auth policy and tenant checks centralized; do not duplicate authorization logic in endpoints.
- Preserve anti-enumeration behavior for failed sign-in attempts.
- Keep implementation compatible with future Google sign-in account mapping in Story 1.3.

### Library / Framework Requirements

- FastAPI for API endpoint implementation.
- Pydantic models for request/response validation.
- JWT for auth tokens (with expiry controls).
- Password hashing via Argon2id or bcrypt; avoid plaintext or reversible storage.

### File Structure Requirements

- API implementation under `apps/api` with explicit boundaries:
  - Domain logic in `app/domains/auth/*`
  - Shared security helpers in `app/core/*`
  - Tests under `apps/api/tests/*`
- Keep endpoint/version routing aligned with architecture API boundary (`/auth/*`).
- If shared auth contracts are needed by multiple apps, place types/contracts in `packages/contracts`.

### Testing Requirements

- Add API integration tests covering success and all denial paths.
- Add tests that assert generic failure messaging for invalid credentials.
- Add tests that assert inactive users are denied.
- Add tests confirming token payload includes role and org claims required for downstream authorization.

### Previous Story Intelligence

- Story 1.1 established monorepo baseline and app/package boundaries; continue using existing structure instead of introducing new workspace layouts.
- Root tooling uses Turborepo task orchestration; new API tests should plug into existing workspace scripts.
- Story 1.1 had environment-dependent install issues (`EAI_AGAIN`), so keep this story's validation focused on deterministic local checks and explicit command logs.

### Git Intelligence Summary

- Repository history is currently minimal (`Initial update`), so rely primarily on architecture and story docs for conventions.

### Project Context Reference

- No `project-context.md` found; guidance derived from PRD, architecture, UX spec, epics, and Story 1.1 artifact.

### References

- [Source: _bmad-output/implementation-artifacts/epics.md#Story 1.2: Email/Password Sign-In for Organization Users]
- [Source: _bmad-output/implementation-artifacts/architecture.md#Security and Compliance Baseline]
- [Source: _bmad-output/implementation-artifacts/architecture.md#Authentication & Security]
- [Source: _bmad-output/implementation-artifacts/architecture.md#API Boundaries (MVP)]
- [Source: _bmad-output/planning-artifacts/prd.md#MVP – Minimum Viable Product]
- [Source: _bmad-output/planning-artifacts/prd.md#RBAC Matrix]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#UX Requirements]
- [Source: _bmad-output/implementation-artifacts/1-1-initialize-project-from-approved-starter-template.md]

## Story Completion Status

- Story status set to `done`.
- Completion note: Code review findings resolved; throttling, role enforcement, and schema validation coverage added with passing tests.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Sprint status parsed from `_bmad-output/implementation-artifacts/sprint-status.yaml`
- Story source extracted from `_bmad-output/implementation-artifacts/epics.md`
- Architecture constraints extracted from `_bmad-output/implementation-artifacts/architecture.md`
- PRD and UX constraints extracted from `_bmad-output/planning-artifacts/prd.md` and `_bmad-output/planning-artifacts/ux-design-specification.md`
- Previous story intelligence extracted from `_bmad-output/implementation-artifacts/1-1-initialize-project-from-approved-starter-template.md`
- Updated sprint tracking: `1-2-email-password-sign-in-for-organization-users` moved to `in-progress`
- Implemented auth module scaffolding under `apps/api/app/{core,domains/auth}` with `/auth/login` route, service, schemas, and security helpers
- Added unit/integration tests under `apps/api/tests/*` for success, invalid password, unknown user, inactive user, and anti-enumeration behavior
- Validation attempt: `python3 -m pytest -q` (from `apps/api`) failed due missing deps (`fastapi`, `bcrypt`)
- Dependency install attempt: `python3 -m pip install -e 'apps/api[dev]'` failed (externally-managed environment)
- Dependency install attempt: `python3 -m venv .venv && .venv/bin/pip install -e 'apps/api[dev]'` failed (offline DNS resolution for package index)
- Syntax validation: `python3 -m compileall apps/api/app apps/api/tests` passed
- Monorepo checks: `pnpm test`, `pnpm lint`, `pnpm typecheck`, `pnpm build` passed
- Validation run (with venv): `python -m pytest apps/api/tests -q` passed (7 passed)
- Root-cause/fix: integration test hangs traced to sync dependency execution path in this runtime; auth dependency was updated to async and integration tests switched to `httpx.ASGITransport`
- Code review fix: implemented in-memory login attempt throttling (429 after repeated failures) and reset hook for tests
- Code review fix: enforced supported role validation before token issuance
- Code review fix: replaced static fallback JWT secret with ephemeral process-local secret when `JWT_SECRET` is missing
- Validation run (post-fixes): `python -m pytest apps/api/tests -q` passed (10 passed)
- Monorepo checks (post-fixes): `pnpm test`, `pnpm lint`, `pnpm typecheck`, `pnpm build` passed

### Completion Notes List

- Created implementation-ready Story 1.2 context file with explicit auth/security guardrails.
- Added acceptance-criteria-aligned task breakdown for API implementation and testing.
- Captured architectural constraints for token handling, anti-enumeration behavior, and role/org claim propagation.
- Implemented initial Story 1.2 backend code for email/password sign-in with centralized security and role-home mapping contract.
- Added API and service tests for authentication flows and generic failure responses.
- Completed API docs update for auth environment variables and endpoint behavior.
- Resolved runtime test hang and validated full Story 1.2 Python test suite in `.venv`.
- Fixed code-review findings for rate limiting, role safety, and payload validation test coverage.
- Updated auth README secret guidance to match runtime behavior.

### File List

- _bmad-output/implementation-artifacts/1-2-email-password-sign-in-for-organization-users.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- README.md
- apps/api/README.md
- apps/api/app/__init__.py
- apps/api/app/core/__init__.py
- apps/api/app/core/roles.py
- apps/api/app/core/rate_limit.py
- apps/api/app/core/security.py
- apps/api/app/core/settings.py
- apps/api/app/domains/__init__.py
- apps/api/app/domains/auth/__init__.py
- apps/api/app/domains/auth/models.py
- apps/api/app/domains/auth/repository.py
- apps/api/app/domains/auth/router.py
- apps/api/app/domains/auth/schemas.py
- apps/api/app/domains/auth/service.py
- apps/api/app/main.py
- apps/api/pyproject.toml
- apps/api/tests/__init__.py
- apps/api/tests/test_auth_login_api.py
- apps/api/tests/test_auth_service.py
- package.json

### Change Log

- 2026-03-06: Started Story 1.2 implementation, added auth endpoint/service/tests, moved status to in-progress, and logged dependency/network blocker for Python test execution.
- 2026-03-06: Completed Story 1.2 implementation and testing; set story status to review.
- 2026-03-06: Addressed code-review findings and set story status to done.
