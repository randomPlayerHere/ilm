# Story 1.3: Google Sign-In for Organization Users

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a school user,  
I want to sign in with Google,  
so that I can access the platform using my institution account.

## Acceptance Criteria

1. Given a user is authorized for Google sign-in in their org, when they complete OAuth successfully, then the system creates or maps their account and starts an authenticated session, and applies the user's existing org membership and role.
2. Given Google sign-in succeeds but no authorized org membership exists, when access is evaluated, then the system blocks protected access, and shows an access-request/contact-admin message.

## Tasks / Subtasks

- [x] Implement Google OAuth callback flow in `apps/api` (AC: 1, 2)
  - [x] Add Google sign-in endpoint(s) under `/auth/*` (for auth URL start and/or callback/token exchange).
  - [x] Validate Google token/claims (issuer, audience/client ID, expiry, email verification).
  - [x] Normalize and extract identity keys (`google_sub`, `email`) for account mapping.
- [x] Implement account mapping and authorized membership checks (AC: 1, 2)
  - [x] Map Google identity to existing user account by stable identity strategy.
  - [x] Apply org membership + role from platform data on successful mapping.
  - [x] Block session issuance when no authorized org membership exists.
  - [x] Return explicit access-request/contact-admin guidance for blocked-but-authenticated Google users.
- [x] Reuse centralized session issuance + role-home routing (AC: 1)
  - [x] Reuse existing JWT token creation utilities from Story 1.2.
  - [x] Reuse existing role-to-home mapping contract from `app/core/roles.py`.
  - [x] Ensure unsupported roles and inactive users are rejected consistently with auth policy.
- [x] Enforce secure failure and anti-enumeration patterns (AC: 2)
  - [x] Keep external auth failures generic where identity disclosure is sensitive.
  - [x] Distinguish only authorized-vs-not-authorized outcomes needed by product UX.
  - [x] Apply login throttling/abuse controls consistently with Story 1.2 auth endpoints.
- [x] Add automated tests for Google sign-in behavior (AC: 1, 2)
  - [x] Unit tests for Google claim validation + identity mapping decisions.
  - [x] API integration tests for successful mapped login path.
  - [x] API integration tests for no-membership blocked path with contact-admin message.
  - [x] Security tests for invalid/expired token and unsupported issuer/audience paths.
- [x] Update implementation docs and handoff notes (AC: 1, 2)
  - [x] Document required Google OAuth env vars and callback URL configuration.
  - [x] Document expected API responses for success vs blocked-no-membership cases.

## Dev Notes

- Story 1.2 already established core session/token and role-home routing behavior. Reuse that flow; do not fork auth semantics.
- Keep tenant and role policy centralized in auth service/policy helpers; avoid scattering authorization logic across handlers.
- Google auth here is identity proof; platform authorization remains controlled by org membership and role records.

### Technical Requirements

- Backend is FastAPI in `apps/api`.
- Use Google OIDC/OAuth token verification with strict claim checks.
- Reuse JWT session model from Story 1.2 (`sub`, `org_id`, `role`, `exp`) for successful authorized users.
- Enforce active-user + supported-role checks before issuing platform session.

### Architecture Compliance

- Implement within `apps/api/app/domains/auth` and shared helpers in `app/core/*`.
- Preserve anti-enumeration and rate-limit behavior already introduced in Story 1.2.
- Keep Google provider-specific logic isolated behind domain service/helper boundary for future provider expansion.
- Maintain tenant/org isolation model by requiring org membership authorization after Google identity validation.

### Library / Framework Requirements

- FastAPI for API endpoints and dependency wiring.
- Pydantic for request/response and claim validation models.
- Existing JWT + bcrypt stack remains authoritative for platform session issuance.
- Use a Google-compatible OIDC verification approach (JWT signature + issuer/audience checks) aligned to official Google docs.

### File Structure Requirements

- Extend existing auth implementation paths:
  - `apps/api/app/domains/auth/*` for endpoint/service/repository logic
  - `apps/api/app/core/*` for shared security/policy utilities where needed
  - `apps/api/tests/*` for unit + integration coverage
- Keep endpoint namespace under `/auth/*`.
- If frontend/shared contract updates are needed, add schema contracts in `packages/contracts`.

### Testing Requirements

- Add tests for successful Google auth mapping into existing org role context.
- Add tests for blocked users with valid Google auth but no authorized org membership.
- Add tests for invalid token claims (`exp`, `iss`, `aud`) and verify denial behavior.
- Add tests confirming no session token is issued for blocked/no-membership flow.

### Previous Story Intelligence

- Story 1.2 delivered:
  - Central JWT issuance and role-home response contract.
  - Supported-role enforcement and active-user checks.
  - In-memory login rate limiter with 429 behavior.
  - Auth tests running in `.venv` via `python -m pytest apps/api/tests -q`.
- Keep these patterns and naming conventions; avoid introducing parallel auth mechanisms.

### Git Intelligence Summary

- Repository commit history remains minimal; implementation conventions are primarily established by Story 1.2 files in `apps/api`.

### Project Context Reference

- No `project-context.md` found. Guidance derived from epics, architecture, PRD, UX, and Story 1.2 implementation artifact.

### References

- [Source: _bmad-output/implementation-artifacts/epics.md#Story 1.3: Google Sign-In for Organization Users]
- [Source: _bmad-output/implementation-artifacts/architecture.md#Authentication & Security]
- [Source: _bmad-output/implementation-artifacts/architecture.md#API Boundaries (MVP)]
- [Source: _bmad-output/planning-artifacts/prd.md#MVP – Minimum Viable Product]
- [Source: _bmad-output/planning-artifacts/prd.md#RBAC Matrix]
- [Source: _bmad-output/implementation-artifacts/1-2-email-password-sign-in-for-organization-users.md]

## Story Completion Status

- Story status set to `ready-for-dev`.
- Completion note: Ultimate context engine analysis completed - comprehensive developer guide created.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Sprint status parsed from `_bmad-output/implementation-artifacts/sprint-status.yaml`
- Story source extracted from `_bmad-output/implementation-artifacts/epics.md`
- Architecture constraints extracted from `_bmad-output/implementation-artifacts/architecture.md`
- PRD and UX constraints extracted from `_bmad-output/planning-artifacts/prd.md` and `_bmad-output/planning-artifacts/ux-design-specification.md`
- Previous story intelligence extracted from `_bmad-output/implementation-artifacts/1-2-email-password-sign-in-for-organization-users.md`
- Added Google OIDC verifier module and `/auth/google` endpoint implementation in `apps/api/app/domains/auth/*`
- Updated auth repository/service schemas to support Google `sub` mapping and org-membership authorization outcomes
- Added Google claim and mapping tests; unit tests pass in local `.venv`
- Resolved API test harness hang by migrating endpoint tests away from `TestClient`/pytest-anyio path to stable `httpx.ASGITransport` + `asyncio.run` pattern
- Full API regression executed successfully via `.venv` (`24 passed`)

### Completion Notes List

- Created implementation-ready Story 1.3 context with Google OAuth mapping and org-membership authorization guardrails.
- Added AC-aligned tasks for token verification, membership gating, session issuance reuse, and blocked-access UX response.
- Captured test expectations for success path, blocked path, and token validation failures.
- Implemented `POST /auth/google` with strict claim checks (issuer/audience/expiry/email verification) through provider-isolated verifier logic.
- Implemented stable identity mapping strategy: `google_sub` first, fallback to normalized email, then persisted sub-link on first successful match.
- Implemented membership-gated behavior: explicit 403 contact-admin guidance when Google identity is valid but no authorized org membership exists.
- Reused Story 1.2 session issuance and role-home routing contract for successful Google login.
- Added security tests for invalid issuer/audience/expiry/email verification and service tests for mapping and authorization decisions.
- Updated API docs with required Google OAuth/OIDC environment variables and backend token-exchange expectations.
- Removed the runtime-specific API test hang blocker and validated full `apps/api` pytest suite pass.
- Addressed code-review findings: declared RSA crypto runtime dependency for Google JWT verification, hardened stable `google_sub` binding to prevent silent rebinding, strengthened invalid-token rate-limiting resistance, and added policy/regression tests for Google auth path.

### File List

- _bmad-output/implementation-artifacts/1-3-google-sign-in-for-organization-users.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- apps/api/app/core/settings.py
- apps/api/app/domains/auth/google_oidc.py
- apps/api/app/domains/auth/models.py
- apps/api/app/domains/auth/repository.py
- apps/api/app/domains/auth/router.py
- apps/api/app/domains/auth/schemas.py
- apps/api/app/domains/auth/service.py
- apps/api/tests/test_auth_google_api.py
- apps/api/tests/test_google_oidc.py
- apps/api/tests/test_auth_service.py
- apps/api/README.md
- apps/api/pyproject.toml

## Change Log

- 2026-03-05: Started Story 1.3 implementation, moved sprint status to `in-progress`, implemented Google auth endpoint/service/repository updates, and added Google-focused tests.
- 2026-03-05: Resolved ASGI test harness hang by refactoring API tests to `httpx.ASGITransport` + `asyncio.run`; full `apps/api` regression now passing; story moved to `review`.
- 2026-03-05: Code review fixes applied; all review findings resolved and full regression re-run (`28 passed`); story moved to `done`.

## Senior Developer Review (AI)

### Review Date

2026-03-05

### Reviewer

GPT-5 Codex

### Outcome

Approved

### Findings Resolved

- [x] [High] Added `cryptography` runtime dependency required for RS256/JWK verification in Google auth flow.
- [x] [High] Prevented silent Google identity rebinding by rejecting mismatched existing `google_sub` links.
- [x] [Medium] Strengthened invalid-token throttling by keying unknown Google failures to requester client host (not token hash).
- [x] [Medium] Added missing Google-path policy/rate-limit regression tests (inactive-user denial, rotating-invalid-token throttling, sub-rebinding safety, unsupported-role service denial).

### Validation Evidence

- `cd apps/api && ../../.venv/bin/python -m pytest -q`
- Result: `28 passed, 1 warning`
