---
title: Architecture - Teacher OS
author: elephant
status: complete
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
workflowType: architecture
lastStep: 8
completedAt: '2026-03-03'
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
  - _bmad-output/planning-artifacts/epics-and-stories.md
  - _bmad-output/planning-artifacts/srs.md
  - _bmad-output/planning-artifacts/product-brief-ilm-2026-03-03.md
  - _bmad-output/planning-artifacts/product-brief-ilm-2025-03-01.md
  - _bmad-output/planning-artifacts/prd-validation-report-2026-03-03.md
---

# Architecture - Teacher OS

## Stack Decisions
- Backend: FastAPI (Python)
- Database: PostgreSQL
- Mobile UI: React Native
- Cloud: AWS

## High-Level Components
- API Service (FastAPI)
  - Auth and RBAC
  - Course generation orchestration
  - Grading workflow orchestration
  - Messaging/notification APIs
  - Analytics endpoints
- Data Layer (PostgreSQL)
  - Multi-tenant org/school model
  - Users, roles, classes, enrollments
  - Courses, lessons, assignments, submissions
  - Grades, rubric outcomes, risk metrics
  - Message threads, notification events
- Client Apps
  - React Native Teacher/Parent app
  - Web admin portal (initially same API; minimal separate frontend can be added)
- AWS Platform
  - ECS/Fargate or App Runner for API
  - RDS PostgreSQL
  - S3 for assignment images
  - SQS/EventBridge for async jobs/notifications
  - CloudWatch logs/metrics/alerts

## Security and Compliance Baseline
- JWT auth with role-based access control.
- Tenant/org data isolation in queries and policy checks.
- Signed URL upload/download for student work images.
- Audit logs for grade edits and communications.
- PII minimization and encrypted at-rest/in-transit defaults.

## Core Domain Model (MVP)
- users(id, org_id, role, email, password_hash, status)
- students(id, org_id, grade_level, profile)
- guardians(id, user_id)
- teachers(id, user_id)
- classes(id, org_id, teacher_id, subject, state_standard)
- enrollments(class_id, student_id)
- courses(id, class_id, metadata)
- assignments(id, class_id, rubric)
- submissions(id, assignment_id, student_id, image_url)
- grades(id, submission_id, ai_score, teacher_score, approved_at)
- risk_signals(id, student_id, period, score, reason)
- messages(id, thread_id, sender_id, body)
- notifications(id, user_id, type, status, sent_at)

## API Boundaries (MVP)
- /auth/*
- /courses/* (generate, customize, publish)
- /grading/* (upload, ai-assist, review, approve)
- /students/* (analytics, projection, risk)
- /messages/*
- /notifications/*
- /org-analytics/*

## Delivery Environments
- Local: docker compose (api + postgres + localstack optional)
- Staging: AWS managed services with seeded test data
- Prod: same topology with stricter security controls

## Non-Functional Requirements (NFR Targets)

### Performance
- API p95 latency for core read endpoints (`/students/*`, `/org-analytics/*`): <= 500 ms under expected school-hour load.
- API p95 latency for write endpoints (`/grading/*`, `/messages/*`): <= 800 ms excluding async AI processing.
- Dashboard initial load p95 (mobile and web): <= 2.5 s on broadband equivalent.

### Reliability
- Service availability target: 99.5% monthly uptime for MVP.
- Background grading/notification job success rate: >= 99.0%.
- Recovery point objective (RPO): <= 15 minutes.
- Recovery time objective (RTO): <= 60 minutes.

### Scalability
- Support at least 10,000 active students per org and 500 concurrent active users per org in MVP baseline tests.
- Image upload pipeline should sustain 50 uploads/minute per org without data loss.

### Security
- Enforce TLS 1.2+ for all traffic.
- Password hashing with Argon2id or bcrypt (cost tuned for environment).
- JWT expiration <= 60 minutes, refresh tokens revocable.
- Mandatory audit logging for grade approvals/edits and role changes.

### Observability
- Structured logs with correlation/request ID across API and async workers.
- CloudWatch alerts for p95 latency breaches, 5xx rate, and job failure rate.
- Error budget policy: if monthly error budget burn exceeds 50% mid-cycle, freeze non-critical feature releases until stabilized.

## Architecture Risks and Mitigations
- Risk: AI grading inaccuracies
  - Mitigation: mandatory teacher approval gate.
- Risk: notification overload
  - Mitigation: per-user cadence/preferences.
- Risk: scaling media uploads
  - Mitigation: direct S3 upload + async processing.

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
Teacher OS requires a multi-role, tenant-safe platform with 40 functional requirements across identity/access, curriculum generation, AI-assisted grading, analytics, messaging, org reporting, and administration. Architecturally, this implies clear bounded modules with explicit authorization boundaries at every API path and data access layer.
- Identity and access (FR-001..FR-005) require secure auth, robust RBAC, and fail-closed authorization behavior.
- Course workflows (FR-006..FR-011) require AI orchestration with draft/edit/publish states and revision/audit support.
- Grading pipeline (FR-012..FR-019) requires media upload, async AI scoring, confidence handling, teacher override, and immutable approval versions.
- Parent/student analytics (FR-020..FR-025) require trend/risk computation with explanation text and strict linked-student access controls.
- Messaging/notifications (FR-026..FR-032) require context-linked threads, cadence preferences, and reliable multi-channel delivery tracking.
- Org analytics and admin (FR-033..FR-040) require privacy-safe aggregation, role-scoped filtering, and auditable administrative operations.

**Non-Functional Requirements:**
NFRs strongly shape architecture and deployment:
- Performance: p95 API and dashboard responsiveness targets demand indexed query design, caching strategy, and async offloading.
- Reliability: uptime, job success rates, and DR targets require resilient worker topology, retries, idempotency, and backup/restore readiness.
- Scalability: baseline concurrency and upload throughput require horizontally scalable API/worker components and controlled storage pipelines.
- Security/privacy: TLS, token hygiene, hashing, server-side authorization checks, COPPA/FERPA-aligned handling, and data minimization must be enforced by design.
- Observability: structured logs, correlation IDs, alerting, and reliability reviews require first-class telemetry architecture.
- Usability/accessibility: teacher under 2-minute grading cycle, discoverable parent risk status, and WCAG 2.x AA impose measurable UX-performance and accessibility quality gates.

**Scale & Complexity:**
The project is a high-complexity MVP due to multi-role workflows, compliance constraints, AI-assisted grading, and cross-surface UX consistency.
- Primary domain: Full-stack EdTech SaaS (mobile + web + backend + async processing)
- Complexity level: High
- Estimated architectural components: 12-15 core components/services (identity, authorization, tenant policy, course service, grading ingestion, AI orchestration, grade ledger/versioning, analytics computation, messaging, notification service, org analytics, audit/telemetry)

### Technical Constraints & Dependencies

- Mandatory tenant/org isolation on all protected reads/writes.
- No grade release to parent/student before explicit teacher approval.
- COPPA/FERPA-aligned access/disclosure controls and auditable handling.
- React Native mobile surfaces for teacher/parent/student with web admin/leadership console.
- AWS-oriented runtime assumptions (managed compute, PostgreSQL/RDS, S3, async queue/event system).
- Signed URL media upload patterns for assignment artifacts.
- AI quality assumptions with required human-in-the-loop approval.
- Dependency on school roster/class data availability and future integration readiness (for example, Google Classroom/SIS-LMS path).
- Open architectural decisions still noted in SRS (compute flavor, integration timing, retention policy, grading confidence thresholds).

### Cross-Cutting Concerns Identified

- Tenant safety and authorization consistency across every service boundary.
- Privacy-by-default data modeling and response shaping (especially org dashboards and messaging context).
- Auditability and traceability for sensitive changes (grade approvals/edits, role/admin changes, disclosure actions).
- Explainable AI outputs with confidence signaling and enforceable teacher authority.
- Operational observability, incident detection, and measurable SLO/NFR conformance.
- Accessibility and role-focused UX consistency across mobile/web.
- Notification governance to balance timely intervention with alert fatigue.
- Data lifecycle governance: retention, deletion/export, and legal-policy alignment.

## Starter Template Evaluation

### Primary Technology Domain

Full-stack multi-platform (mobile-first + backend API + admin web) based on project requirements analysis.

### Starter Options Considered

1) Expo starter (`create-expo-app`)
- Strong fit for teacher/parent/student mobile apps.
- Official maintained command path supports template selection and TypeScript-ready bootstrap.
- Limitation: does not scaffold backend/API and org admin architecture.

2) FastAPI full-stack template (`fastapi/full-stack-fastapi-template`)
- Officially referenced by FastAPI project generation docs as a maintained full-stack baseline.
- Includes backend security, DB patterns, tests, CI/CD, and web frontend conventions.
- Limitation: web-frontend oriented baseline, not mobile-first React Native by default.

3) Turborepo starter (`create-turbo`)
- Official maintained monorepo starter with current CLI commands.
- Supports monorepo scaling and shared packages across multiple apps.
- Limitation: backend/API specifics and compliance-sensitive patterns must still be designed explicitly.

### Selected Starter: Turborepo (`create-turbo`) as repo foundation

**Rationale for Selection:**
Teacher OS spans mobile apps, backend services, and admin web. A monorepo-first starter best matches cross-surface code sharing, shared contracts, and long-term maintainability. It gives a neutral foundation while allowing explicit FastAPI and React Native architecture decisions.

**Initialization Command:**

```bash
npx create-turbo@latest
```

**Architectural Decisions Provided by Starter:**

**Language & Runtime:**
TypeScript-first workspace baseline for JS/TS apps/packages; Python backend workspace can be added cleanly.

**Styling Solution:**
No hard lock-in; allows admin web and mobile styling alignment with the UX specification.

**Build Tooling:**
Turborepo task orchestration, caching, and workspace pipeline structure for multi-app development.

**Testing Framework:**
Baseline depends on chosen apps/packages; enables shared CI task graph and per-workspace test commands.

**Code Organization:**
Monorepo structure with app/package separation and shared library patterns; suitable for shared domain contracts and UI tokens.

**Development Experience:**
Strong local DX for parallel app/service workflows, incremental builds, and scalable CI execution.

**Note:** Project initialization using this command should be the first implementation story.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Multi-tenant data isolation strategy: shared DB + strict `org_id` scoping + DB-level guards.
- AuthN/AuthZ approach: JWT with refresh token rotation + centralized policy enforcement.
- API contract model: REST-first with OpenAPI as source of truth.
- Async job architecture: queue-driven grading/notification workers with idempotency keys.
- Grade publication rule: immutable approval ledger; no parent/student visibility pre-approval.

**Important Decisions (Shape Architecture):**
- Caching and rate-limiting strategy.
- Admin/reporting read-model strategy for privacy-safe aggregates.
- Monorepo package boundaries and shared contract library.
- Mobile offline behavior and sync conflict policy.
- Observability baseline (structured logs, traces, metrics, SLO alerting).

**Deferred Decisions (Post-MVP):**
- GraphQL federation / BFF specialization.
- Multi-region active-active deployment.
- Schema-per-tenant or DB-per-tenant enterprise isolation path activation.
- Real-time websocket fanout beyond notification-critical paths.

### Data Architecture

- Primary DB: PostgreSQL 18.x line (current supported major), with migration tooling and explicit tenant keys.
- Data modeling: relational core with append-only grade_versions and audit_events tables.
- Validation: Pydantic models at API boundary + DB constraints for invariants.
- Migrations: forward-only migrations in CI; rollback via compensating migration policy.
- Caching: Redis 8.x for short-lived read caches, rate-limit counters, and job dedup hints.

### Authentication & Security

- Authentication: email/password + Google SSO (OIDC) for supported roles.
- Token model: short-lived JWT access tokens, rotating refresh tokens, per-device/session revocation.
- Authorization: policy module enforcing role + tenant + relationship checks on every protected endpoint.
- API security: strict input validation, signed URL upload flow, anti-enumeration responses, and per-endpoint rate limits.
- Encryption: TLS 1.2+ in transit; encrypted storage at rest; scoped secrets management.
- Compliance controls: COPPA/FERPA-aligned access/disclosure workflows and auditable actions.

### API & Communication Patterns

- API style: REST + OpenAPI 3.1 contracts, versioned under `/v1`.
- Error standard: normalized error envelope with machine code + correlation ID.
- Async communication: queue-based workers for AI grading and notification fanout.
- Reliability patterns: idempotency keys, retry policies with backoff, dead-letter queues, and replay tooling.
- Integration boundary: connector layer for SIS/LMS (Google Classroom first), isolated from domain core.

### Frontend Architecture

- Mobile: Expo/React Native app shells per role surface with shared design tokens.
- Web admin: separate web app in monorepo sharing contracts/types with backend.
- State management: server-state/query cache + minimal local state stores.
- Routing/navigation: role-scoped route trees and permission-aware guards.
- Performance: optimistic UI only where safe, background refresh for dashboards, skeleton-first loading.
- Accessibility: WCAG 2.x AA checks as CI gate for primary flows.

### Infrastructure & Deployment

- Repo foundation: Turborepo monorepo with app/package boundaries.
- Backend runtime: containerized FastAPI services on AWS managed compute (ECS/Fargate favored for control).
- Data/storage: RDS PostgreSQL + S3 object storage + queue/event infrastructure.
- CI/CD: pipeline with lint/test/security scans, migration checks, and staged deployment gates.
- Observability: centralized logs, tracing, metrics dashboards, alerting for latency/error/job-failure SLOs.
- Scaling: horizontal API/worker scaling, queue depth autoscaling triggers, and controlled upload throughput limits.

### Decision Impact Analysis

**Implementation Sequence:**
1. Auth/RBAC/tenant policy core
2. Data schema + migration baseline
3. Grading ingest + async pipeline + approval ledger
4. Parent/student analytics read models
5. Messaging/notifications + cadence controls
6. Org analytics + admin governance
7. Observability hardening + compliance workflows

**Cross-Component Dependencies:**
- Tenant policy affects every endpoint, query, cache key, and analytics aggregation.
- Grade approval ledger gates analytics visibility and notification triggers.
- Async pipeline reliability directly impacts teacher throughput and parent trust loops.
- Accessibility and role-based UX constraints shape component contracts across mobile and web.

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:**
18 areas where AI agents could make different choices and break consistency across services and clients.

### Naming Patterns

**Database Naming Conventions:**
- Tables: `snake_case` plural (`users`, `grade_versions`, `risk_signals`).
- Columns: `snake_case` (`org_id`, `created_at`, `approved_by_user_id`).
- PK/FK: primary `id`; foreign keys as `<entity>_id`.
- Indexes: `idx_<table>_<column_list>` (example: `idx_grades_submission_id`).
- Constraints: `ck_<table>_<rule>`, `uq_<table>_<column_list>`, `fk_<table>_<ref_table>`.

**API Naming Conventions:**
- REST resources are plural nouns (`/v1/users`, `/v1/messages`).
- Path params use `{id}` style in OpenAPI and concrete route syntax in framework.
- Query params are `snake_case` in backend contracts.
- Header names follow standard HTTP casing; custom headers prefixed with `X-TeacherOS-`.

**Code Naming Conventions:**
- Python modules/functions/variables: `snake_case`; classes: `PascalCase`.
- TypeScript vars/functions: `camelCase`; types/components: `PascalCase`.
- File naming:
  - Python: `snake_case.py`
  - TS/RN components: `PascalCase.tsx`
  - Non-component TS files: `kebab-case.ts`.

### Structure Patterns

**Project Organization:**
- Organize by bounded feature domain first, then by layer.
- Backend per-domain layout: `api/`, `service/`, `repo/`, `schemas/`, `policies/`.
- Shared cross-app contracts in dedicated package (`packages/contracts`).
- Tenant policy checks live in reusable policy module, never inline ad-hoc checks.

**File Structure Patterns:**
- Tests:
  - Backend: `tests/` mirror of source paths.
  - Frontend: co-located `*.test.ts(x)` for components/hooks.
- Config:
  - Root-level for monorepo/global tooling.
  - App-local config inside each app directory.
- Documentation:
  - Architecture decisions in planning artifacts.
  - API contracts generated from OpenAPI as canonical source.

### Format Patterns

**API Response Formats:**
- Success envelope:
  - Read: `{ "data": ..., "meta": ... }`
  - Mutations: `{ "data": ..., "meta": { "request_id": "..." } }`
- Error envelope:
  - `{ "error": { "code": "STRING_CODE", "message": "Human readable", "details": {...}, "request_id": "..." } }`
- Status code discipline:
  - `2xx` success, `4xx` client/auth/validation, `5xx` server/unexpected only.

**Data Exchange Formats:**
- External API JSON fields: `snake_case` (matches backend contracts).
- UI mapping layer converts to frontend-native naming if needed.
- Timestamps: ISO-8601 UTC (`YYYY-MM-DDTHH:MM:SSZ`).
- Booleans as true/false only.
- Null policy explicit in schemas (avoid optional+nullable ambiguity).

### Communication Patterns

**Event System Patterns:**
- Event names: `domain.entity.action.v1` (example: `grading.submission.approved.v1`).
- Payload baseline:
  - `event_id`, `event_name`, `occurred_at`, `org_id`, `actor_id`, `entity_id`, `version`, `data`.
- Events are immutable and versioned; schema changes require new version suffix.
- Consumers must be idempotent using `event_id`.

**State Management Patterns:**
- Server state via query cache library; UI state local/store only when not server-derived.
- State updates are immutable.
- Action names are verb-first (`approveGrade`, `setNotificationCadence`).
- Derived selectors live near domain state modules.

### Process Patterns

**Error Handling Patterns:**
- Validation errors are structured and field-addressable.
- AuthZ failures return safe generic messages without leakage.
- User-facing messages are non-technical; detailed diagnostics go to logs.
- Correlation/request IDs included in all errors and logs.

**Loading State Patterns:**
- Use explicit async states: `idle | loading | success | error`.
- Skeletons for first-load, subtle spinners for background refresh.
- Disable destructive/conflicting actions during in-flight mutations.
- Retry UX standardized (inline retry + fallback support path).

### Enforcement Guidelines

**All AI Agents MUST:**
- Reuse shared contracts/schemas; do not invent endpoint or payload variants.
- Apply tenant and authorization checks through central policy utilities.
- Follow naming/format conventions exactly before opening PRs.

**Pattern Enforcement:**
- CI checks: lint, format, schema validation, API contract diff checks, test suites.
- PR template includes "pattern compliance" checklist.
- Violations logged as architecture notes and fixed in same PR unless explicitly waived.
- Pattern updates require architecture doc update before code divergence.

### Pattern Examples

**Good Examples:**
- Endpoint: `GET /v1/students/{student_id}/risk-signals?from=...&to=...`
- Error:
  `{ "error": { "code": "FORBIDDEN", "message": "Access denied", "request_id": "req_123" } }`
- Event:
  `notifications.digest.generated.v1` with immutable payload including `org_id`.

**Anti-Patterns:**
- Mixed naming (`userId` in one API, `user_id` in another).
- Direct DB query in handler bypassing policy module.
- Unversioned event names (`GradeApproved`) with unstable payload shapes.
- Frontend assuming grade visibility before approval gate is satisfied.

## Project Structure & Boundaries

### Complete Project Directory Structure

```text
ilm/
├── README.md
├── LICENSE
├── .gitignore
├── .editorconfig
├── .env.example
├── .env.local.example
├── turbo.json
├── package.json
├── pnpm-workspace.yaml
├── pyproject.toml
├── Makefile
├── docker-compose.yml
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── security.yml
│       └── release.yml
├── apps/
│   ├── mobile/
│   │   ├── app.json
│   │   ├── package.json
│   │   ├── babel.config.js
│   │   ├── tsconfig.json
│   │   ├── app/
│   │   │   ├── (teacher)/
│   │   │   ├── (parent)/
│   │   │   ├── (student)/
│   │   │   ├── auth/
│   │   │   └── _layout.tsx
│   │   ├── src/
│   │   │   ├── features/
│   │   │   │   ├── auth/
│   │   │   │   ├── courses/
│   │   │   │   ├── grading/
│   │   │   │   ├── analytics/
│   │   │   │   ├── messages/
│   │   │   │   └── notifications/
│   │   │   ├── components/
│   │   │   ├── state/
│   │   │   ├── services/
│   │   │   ├── hooks/
│   │   │   └── utils/
│   │   └── __tests__/
│   ├── admin-web/
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── next.config.js
│   │   ├── src/
│   │   │   ├── app/
│   │   │   ├── features/
│   │   │   │   ├── org-analytics/
│   │   │   │   ├── communication-health/
│   │   │   │   ├── users-roles/
│   │   │   │   └── safety-config/
│   │   │   ├── components/
│   │   │   ├── services/
│   │   │   └── utils/
│   │   └── __tests__/
│   └── api/
│       ├── pyproject.toml
│       ├── alembic.ini
│       ├── app/
│       │   ├── main.py
│       │   ├── api/
│       │   │   └── v1/
│       │   │       ├── auth.py
│       │   │       ├── users.py
│       │   │       ├── courses.py
│       │   │       ├── grading.py
│       │   │       ├── students.py
│       │   │       ├── messages.py
│       │   │       ├── notifications.py
│       │   │       ├── org_analytics.py
│       │   │       └── admin.py
│       │   ├── core/
│       │   │   ├── config.py
│       │   │   ├── security.py
│       │   │   ├── tenancy.py
│       │   │   └── logging.py
│       │   ├── domains/
│       │   │   ├── auth/
│       │   │   ├── users/
│       │   │   ├── courses/
│       │   │   ├── grading/
│       │   │   ├── analytics/
│       │   │   ├── messaging/
│       │   │   ├── notifications/
│       │   │   ├── org_analytics/
│       │   │   └── admin/
│       │   ├── db/
│       │   │   ├── base.py
│       │   │   ├── session.py
│       │   │   ├── models/
│       │   │   ├── repositories/
│       │   │   └── migrations/
│       │   ├── workers/
│       │   │   ├── grading_jobs.py
│       │   │   ├── notification_jobs.py
│       │   │   └── retry_policies.py
│       │   └── integrations/
│       │       ├── google_classroom/
│       │       └── connectors/
│       └── tests/
│           ├── unit/
│           ├── integration/
│           ├── contract/
│           └── security/
├── packages/
│   ├── contracts/
│   │   ├── openapi/
│   │   ├── schemas/
│   │   └── events/
│   ├── design-tokens/
│   ├── ui-mobile/
│   ├── ui-web/
│   ├── eslint-config/
│   ├── tsconfig/
│   └── testing/
├── infra/
│   ├── terraform/
│   │   ├── envs/
│   │   │   ├── dev/
│   │   │   ├── staging/
│   │   │   └── prod/
│   │   └── modules/
│   ├── docker/
│   └── scripts/
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── runbooks/
│   └── compliance/
└── _bmad-output/
    └── planning-artifacts/
```

### Architectural Boundaries

**API Boundaries:**
- External contract under `/v1/*`.
- Auth/RBAC/tenancy checks centralized in `app/core/*` and policy middleware.
- Domain endpoints map 1:1 with SRS FR groups: auth, courses, grading, analytics, messages, notifications, org analytics, admin.
- Workers only consume queued jobs; no direct client-facing logic.

**Component Boundaries:**
- Mobile and web apps consume only `packages/contracts` and shared token/UI packages.
- Feature modules in each app are role-scoped and cannot call DB or worker layers.
- Backend domain services do not import frontend packages.

**Service Boundaries:**
- Domain services call repositories, not raw SQL in handlers.
- Integrations isolated under `app/integrations/*` behind domain interfaces.
- Notification and grading orchestration occurs via workers with idempotent event handling.

**Data Boundaries:**
- DB access only through repository layer.
- Tenant boundary on all tables via `org_id`.
- Analytics aggregates expose privacy-safe views for org roles.
- S3 artifact access only through signed URL workflows.

### Requirements to Structure Mapping

**Feature/Epic Mapping:**
- Epic 1 (Identity/RBAC): `apps/api/app/domains/auth`, `users`, `core/security.py`, `tests/security`.
- Epic 2 (Course creation): `domains/courses`, mobile teacher feature `features/courses`.
- Epic 3 (AI grading): `domains/grading`, `workers/grading_jobs.py`, mobile `features/grading`.
- Epic 4 (Student/Parent analytics): `domains/analytics`, mobile `features/analytics`.
- Epic 5 (Messaging/notifications): `domains/messaging`, `domains/notifications`, worker notification jobs.
- Epic 6 (Org dashboard): admin-web `features/org-analytics`, API `domains/org_analytics`.

**Cross-Cutting Concerns:**
- Tenant safety: `core/tenancy.py` + security tests.
- Audit logging: `core/logging.py` + audit events in DB models.
- Accessibility: shared design tokens/UI packages + CI checks.
- Contracts consistency: `packages/contracts` (OpenAPI + schemas + events).

### Integration Points

**Internal Communication:**
- App clients -> API via OpenAPI contract clients.
- API -> worker queue for grading/notifications.
- Worker -> DB + notification providers.

**External Integrations:**
- Google Classroom connector in `app/integrations/google_classroom`.
- Email provider and push provider adapters under notifications domain.
- Object storage (S3) via signed URL service module.

**Data Flow:**
- Teacher upload -> signed URL -> S3 -> grading job -> teacher approval -> grade_version write -> parent/student dashboards + notification triggers.
- Parent message -> messaging domain -> thread persistence -> read-state updates -> digest pipeline.

### File Organization Patterns

**Configuration Files:**
- Root-level monorepo/tooling config.
- App-local runtime configs and env schema validation.
- Infra config separated by environment.

**Source Organization:**
- Domain-first modules in backend.
- Role/feature-first modules in clients.
- Shared contracts and tokens in packages.

**Test Organization:**
- Backend: `unit`, `integration`, `contract`, `security`.
- Frontend: co-located unit tests + targeted e2e flows.
- Compliance/RBAC gate tests mandatory in CI.

**Asset Organization:**
- Mobile assets in `apps/mobile/assets`.
- Web static assets in `apps/admin-web/public`.
- Generated API docs in `docs/api`.

### Development Workflow Integration

**Development Server Structure:**
- Turborepo runs `mobile`, `admin-web`, and `api` concurrently.
- Shared package changes propagate through workspace graph.

**Build Process Structure:**
- Lint/test/typecheck per workspace + contract diff checks.
- Python and Node pipelines executed with cache-aware tasks.

**Deployment Structure:**
- API/worker containers deployed from `apps/api`.
- Mobile/web deployment pipelines isolated but contract-synced.
- Infra environments managed from `infra/terraform/envs/*`.

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
All major decisions are compatible: Turborepo monorepo + Expo mobile + FastAPI backend + PostgreSQL + AWS queue/storage model. Security, tenancy, and approval-gate rules align with API and data-layer patterns. No contradictory technology choices were found.

**Pattern Consistency:**
Implementation patterns are internally consistent across naming, structure, formatting, events, and process handling. API/data naming conventions align with backend-first contract strategy, and shared contracts package supports client consistency.

**Structure Alignment:**
Project structure supports all declared architectural decisions, including domain separation, worker isolation, integration adapters, and shared packages for contracts/tokens. Boundaries are explicit enough to prevent cross-layer leakage.

### Requirements Coverage Validation ✅

**Epic/Feature Coverage:**
All 6 epics are mapped to explicit domains/modules:
- Epic 1: auth/users/security
- Epic 2: courses
- Epic 3: grading + workers
- Epic 4: analytics
- Epic 5: messaging/notifications
- Epic 6: org analytics/admin web

**Functional Requirements Coverage:**
SRS FR-001..FR-040 are architecturally covered through endpoint groups, domain modules, policy enforcement, audit-capable persistence patterns, and client feature boundaries.

**Non-Functional Requirements Coverage:**
- Performance: addressed via API boundaries, caching decisions, async offloading, and scaling patterns.
- Reliability: worker retries/DLQ/idempotency + staged deployment + observability.
- Security/Privacy: centralized policy checks, tenant-scoped data model, signed URL flows, audit trails.
- Compliance/Accessibility: COPPA/FERPA-aligned controls, privacy-safe aggregates, WCAG 2.x AA quality gates.

### Implementation Readiness Validation ✅

**Decision Completeness:**
Critical decisions are documented with practical versions/major lines and rationale. Deferred decisions are identified to avoid MVP ambiguity.

**Structure Completeness:**
Directory tree is concrete and implementation-oriented, with explicit modules, test layout, infra segregation, and documentation locations.

**Pattern Completeness:**
Primary conflict vectors for multi-agent implementation are addressed (naming, payload formats, event schema/versioning, policy reuse, error/loading behavior).

### Gap Analysis Results

**Critical Gaps:** None identified.

**Important Gaps:**
- Finalize exact backend task queue/runtime choices in implementation story (for example, Celery/RQ/native worker) while preserving defined patterns.
- Lock specific cache/session topology details (single Redis vs split logical DBs) during infra story.
- Confirm final admin-web framework/runtime selection in scaffold story if Next.js assumptions change.

**Nice-to-Have Gaps:**
- Add concrete sample payload fixtures for key endpoints/events in `packages/contracts`.
- Add architecture decision records (ADR files) for tenant model and approval-gate invariants.
- Define explicit policy test matrix mapping each role x endpoint group.

### Validation Issues Addressed

- Resolved prior ambiguity between medium/high complexity characterization by treating implementation complexity as high due to compliance + multi-role coupling.
- Ensured structure and pattern sections both enforce the same tenancy and naming standards.
- Confirmed approval-gate invariant appears in decisions, patterns, and data-flow sections.

### Architecture Completeness Checklist

**✅ Requirements Analysis**

- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**✅ Architectural Decisions**

- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed

**✅ Implementation Patterns**

- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**✅ Project Structure**

- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** High based on validation results

**Key Strengths:**
- Strong tenant/RBAC/compliance-first architecture
- Clear multi-agent consistency rules
- Concrete structure-to-requirement mapping
- Explicit async and approval-gate flow design

**Areas for Future Enhancement:**
- Deeper integration adapter contracts beyond Google Classroom
- Optional enterprise tenant-isolation evolution path
- Expanded event catalog and contract-test automation depth

### Implementation Handoff

**AI Agent Guidelines:**
- Follow all architectural decisions exactly as documented.
- Use implementation patterns consistently across all components.
- Respect project structure and boundaries.
- Refer to this document for all architectural questions.

**First Implementation Priority:**
Initialize monorepo foundation:
`npx create-turbo@latest`
Then scaffold `apps/api` (FastAPI), `apps/mobile` (Expo), and `apps/admin-web` with shared contracts package before feature work.
