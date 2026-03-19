---
title: Architecture - Teacher OS
author: elephant
status: complete
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
workflowType: architecture
lastStep: 8
completedAt: '2026-03-19'
previousVersion: '_bmad-output/implementation-artifacts/architecture.md (2026-03-03)'
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
  - _bmad-output/planning-artifacts/prd-validation-report-2026-03-19.md
  - _bmad-output/planning-artifacts/product-brief-ilm-2026-03-03.md
  - _bmad-output/planning-artifacts/product-brief-ilm-2025-03-01.md
---

# Architecture - Teacher OS

## Stack Decisions

- Backend: FastAPI (Python 3.12+)
- Database: PostgreSQL 16.x (AWS RDS)
- Connection pooling: RDS Proxy
- Migrations: Alembic (SQLAlchemy)
- Mobile UI: React Native (Expo) with Tamagui design system
- Companion Web: React SPA (Vite + Tamagui) — static deploy on S3 + CloudFront, no SSR
- Cloud: AWS (ECS Fargate, RDS, S3, SQS, CloudFront, Secrets Manager, ECR, Route 53, ACM)
- CI/CD: GitHub Actions
- Mobile builds: Expo EAS Build (TestFlight + Play Store internal testing)
- Push notifications: FCM (Android) + APNs (iOS) via backend dispatch service
- AI grading: Multimodal vision models (Claude / GPT-4 Vision) — no OCR pipeline
- Caching: Deferred — no Redis in MVP; add ElastiCache when load testing demands it

## High-Level Components

- **API Service (FastAPI)**
  - Auth (email/password + Google sign-in) and RBAC
  - Onboarding service (invite links, join codes, CSV roster import, guided setup)
  - Course generation orchestration
  - Grading workflow orchestration (multimodal AI, retry, manual fallback)
  - Messaging/notification APIs
  - Analytics endpoints
  - COPPA consent confirmation gate
  - Google Classroom one-time roster import connector
- **Worker Service (FastAPI/Celery or ARQ)**
  - AI grading jobs (multimodal vision model calls)
  - Notification dispatch (FCM/APNs via SQS)
  - Digest assembly (weekly/daily per cadence preferences)
  - Retry policies with dead-letter queues
- **Data Layer (PostgreSQL via RDS + RDS Proxy)**
  - Multi-tenant org/school model with strict `org_id` scoping
  - Users, roles, classes, enrollments, invite links, join codes
  - Courses, lessons, assignments, submissions
  - Grades, grade_versions (immutable approval ledger), rubric outcomes
  - Risk metrics, analytics aggregates
  - Message threads, notification events, cadence preferences
  - Audit events, consent status records
- **Client Apps**
  - React Native mobile app (Expo) — primary surface for teacher, parent, student
    - Tamagui components with shared design tokens
    - Role-scoped bottom tab navigation
    - Camera-native grading workflow
    - Offline photo queue (local storage + auto-upload on reconnect)
    - Cached dashboard views for offline reading
    - Client-side image compression (~2MP before upload)
    - Push notification handling (FCM/APNs)
  - React SPA companion web (Vite + Tamagui) — admin and principal dashboards
    - Static deploy: S3 + CloudFront (zero compute cost)
    - Sidebar navigation, data-dense tables and charts
- **AWS Platform**
  - ECS Fargate: API service + Worker service (separate ECS services, separate scaling)
  - RDS PostgreSQL + RDS Proxy (connection pooling)
  - S3 for assignment images (pre-signed URL upload)
  - SQS for async job queues (grading, notifications) with DLQ
  - CloudFront in front of everything (API + web) for edge TLS, DDoS baseline (Shield Standard), unified WAF
  - ECR for container images (lifecycle policy: keep last 10 tagged images)
  - Secrets Manager for all secrets (DB credentials, AI provider keys, signing keys) — no secrets in env vars or Docker images
  - Route 53 for DNS
  - ACM for TLS certificates
  - CloudWatch for logs, metrics, alarms

## Security and Compliance Baseline

- JWT auth with role-based access control.
- Tenant/org data isolation in queries and policy checks.
- Signed URL upload/download for student work images.
- Audit logs for grade edits, role changes, sensitive data access, and consent status changes.
- PII minimization and encrypted at-rest/in-transit defaults.
- COPPA consent confirmation gate: admin verifies consent before activating under-13 accounts.
- App store compliance: positioned as education-institution tool (not Kids category); all third-party SDKs reviewed for children's education app policies before each release. Privacy nutrition labels (Apple) and Data Safety sections (Google) maintained.

## Core Domain Model (MVP)

- users(id, org_id, role, email, password_hash, google_id, status, created_at)
- students(id, org_id, grade_level, profile, consent_status, consent_confirmed_by, consent_confirmed_at)
- guardians(id, user_id)
- guardian_student_links(guardian_id, student_id, linked_via)
- teachers(id, user_id)
- classes(id, org_id, teacher_id, subject, state_standard, join_code)
- enrollments(class_id, student_id)
- invite_links(id, org_id, type, target_student_id, token, expires_at, accepted_at)
- courses(id, class_id, metadata)
- assignments(id, class_id, rubric)
- submissions(id, assignment_id, student_id, image_url, compressed_image_url, offline_queued_at, uploaded_at)
- grades(id, submission_id, ai_score, ai_feedback, ai_confidence, teacher_score, teacher_feedback, approved_at, approved_by)
- grade_versions(id, grade_id, version, score, feedback, changed_by, changed_at)
- risk_signals(id, student_id, period, score, reason)
- messages(id, thread_id, sender_id, body, student_context_id, assignment_context_id)
- threads(id, org_id, participants, student_id, created_at)
- notifications(id, user_id, type, status, cadence, sent_at, deep_link)
- notification_preferences(user_id, event_type, cadence)
- device_tokens(id, user_id, platform, token, updated_at)
- audit_events(id, org_id, actor_id, action, entity_type, entity_id, metadata, created_at)
- organizations(id, name, settings, created_at)

## API Boundaries (MVP)

- /auth/* (sign-in, sign-up, token refresh, Google OAuth)
- /onboarding/* (invite links, join codes, guided setup state, CSV import)
- /courses/* (generate, customize, publish)
- /grading/* (upload via pre-signed URL, AI-assist trigger, review, approve, manual fallback)
- /students/* (analytics, projection, risk, growth timeline)
- /messages/* (threads, contextual messages, read status)
- /notifications/* (preferences, delivery status, device token registration)
- /org-analytics/* (cohort trends, filtered views, engagement indicators)
- /admin/* (user/role/org management, safety config, consent confirmation, standards profiles)
- /health (service health check)

## Delivery Environments

| Aspect | Dev | Staging | Prod |
|--------|-----|---------|------|
| Compute | ECS Fargate (single task) | ECS Fargate (2 tasks) | ECS Fargate (autoscaling) |
| Database | RDS db.t4g.medium, single-AZ | RDS db.t4g.medium, single-AZ | RDS db.r7g.large, Multi-AZ |
| RDS Proxy | Yes | Yes | Yes |
| Backups | Automated, 7-day retention | Automated, 7-day retention | Automated, 14-day retention, PITR |
| S3 | Standard | Standard | Standard + lifecycle policies |
| CloudFront | Optional | Yes | Yes + WAF |
| Mobile | Expo Dev Client | TestFlight / Play Store internal | App Store / Play Store |
| CI/CD | GitHub Actions, GitHub-hosted runners | Same | Same + manual deploy gate |
| Secrets | Secrets Manager | Secrets Manager | Secrets Manager |
| Observability | CloudWatch basic | CloudWatch + alarms | CloudWatch + alarms + dashboards |

**Day-zero operational prerequisites:**
- Apple Developer Program enrollment ($99/yr) — requires DUNS number, review time
- Provisioning profiles and signing certificates (iOS)
- Google Play Console registration ($25 one-time)
- TestFlight setup and internal testing tracks
- Privacy policy URL (required by both stores)
- Expo EAS Build configuration in CI pipeline from sprint 1

## Non-Functional Requirements (NFR Targets)

### Performance

- API p95 latency for core read endpoints: ≤ 500ms under expected school-hour load.
- API p95 latency for write endpoints: ≤ 800ms excluding async AI processing.
- Mobile screen loads p95: ≤ 2.0s (NFR1).
- Core interactive actions p95: ≤ 1.5s (NFR2).
- Camera open: < 500ms from tap (UX spec).
- AI grading acknowledgment: ≤ 3s (NFR4). 90% results within 60s (NFR5).
- Total per-assignment grading: < 2 minutes including review (UX spec).

### Reliability

- Service availability: 99.5% monthly uptime (NFR13).
- No loss of committed grade records (NFR14).
- 99% of failed critical async jobs retried within 5 minutes, idempotently (NFR15).
- 4-hour restore for high-severity incidents (NFR16).

### Scalability

- 10x growth from pilot without re-architecture (NFR17).
- Horizontal scaling of API and worker services (NFR18).
- Worker autoscaling on SQS queue depth (`ApproximateNumberOfMessagesVisible`).
- API autoscaling on CPU/request count.

### Security

- TLS 1.2+ for all traffic via CloudFront edge termination.
- Password hashing with Argon2id or bcrypt.
- JWT expiration ≤ 60 minutes, refresh tokens revocable per-device.
- Mandatory audit logging for grade approvals/edits, role changes, consent changes.
- All secrets in AWS Secrets Manager — never in env vars or Docker images.

### Observability

- Structured logs with correlation/request ID across API and workers.
- CloudWatch alarms for p95 latency breaches, 5xx rate, job failure rate, SQS dead-letter depth.
- 95%+ of requests include distributed traces (NFR26).
- Security event monitoring: failed auth spikes, permission-denied anomalies (NFR28).

## Architecture Risks and Mitigations

- **Risk: AI grading inaccuracies** — Mitigation: mandatory teacher approval gate; confidence scoring with amber/low badges; 2x retry before manual fallback (FR18a, FR18b).
- **Risk: AI provider outage or timeout** — Mitigation: manual grading fallback path is always available; grading workflow never blocked by AI failure.
- **Risk: Notification overload** — Mitigation: default to weekly digest; per-user cadence preferences; batch notifications.
- **Risk: Scaling media uploads** — Mitigation: client-side compression to ~2MP; direct S3 upload via pre-signed URLs; async processing.
- **Risk: Offline data loss** — Mitigation: local photo queue with auto-upload; cached dashboards; optimistic UI with rollback.
- **Risk: App store rejection** — Mitigation: education-institution positioning (not Kids category); SDK audit before each release; privacy nutrition labels maintained.
- **Risk: RDS connection exhaustion at scale** — Mitigation: RDS Proxy from day one; connection pooling handles Fargate task scaling.

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
Teacher OS specifies 48 functional requirements across 7 capability groups, representing a fully usable mobile application (not just an API backend).
- Identity, access, and onboarding (FR1–FR9e): secure auth, RBAC, guided onboarding per role, invite links, join codes, CSV roster import, COPPA consent gate.
- Course workflows (FR10–FR12): AI-assisted curriculum generation with draft/edit/publish states, generic and student-specific plans.
- Grading pipeline (FR13–FR18b): in-app photo capture, client-side compression (~2MP), multimodal AI scoring (no OCR), confidence handling, teacher override, immutable approval ledger, 2x retry before manual fallback, manual grading path preserving workflow context.
- Parent/student analytics (FR19–FR26): trend indicators, longitudinal views, strengths/weaknesses, growth framing, self-serve access.
- Messaging/notifications (FR27–FR30): context-linked threads (student + assignment), configurable cadence (instant/daily/weekly/off), push via FCM/APNs.
- Org analytics and admin (FR31–FR34): privacy-safe aggregation, role-scoped filtering, engagement indicators.
- Platform operations (FR35–FR48): audit logging, COPPA/FERPA controls, data minimization, offline photo queue, cached dashboards, image compression.

**Non-Functional Requirements:**
28 NFRs drive architecture and deployment:
- Performance: p95 screen loads ≤2s, interactions ≤1.5s, AI ack ≤3s, 90% AI results within 60s.
- Reliability: 99.5% uptime, no grade data loss, 99% job retry within 5min, 4hr restore.
- Scalability: 10x from pilot, horizontal API/worker scaling, tenant-safe under load.
- Security: TLS 1.2+, encrypted at rest, 100% tenant isolation, immutable audit events within 30s.
- Accessibility: WCAG 2.1 AA across mobile and web, platform-native accessibility.
- Integration: external failures don't block core workflows, structured logs, versioned contracts.
- Observability: structured logs + traces on 95%+ requests, 5min alerting.

**Scale & Complexity:**
- Primary domain: Mobile-centric full-stack EdTech SaaS
- Complexity level: High
- Estimated architectural components: 15-18

### Technical Constraints & Dependencies

- React Native mobile app is the primary delivery surface; companion web for admin/principal.
- Tamagui as cross-platform design system (optimized native + web from shared components).
- Mandatory tenant/org isolation on all protected reads/writes.
- No grade release before teacher approval.
- COPPA consent confirmation gate for under-13 accounts.
- App store compliance: education-institution positioning, SDK audit per release.
- Multimodal AI grading: vision models analyze images directly — no OCR.
- Client-side image compression to ~2MP before upload.
- Offline photo queue + cached dashboards.
- Push notifications via FCM/APNs, SQS-backed dispatch.
- Deployment: ECS Fargate (API + worker as separate services), RDS PostgreSQL + RDS Proxy, S3, SQS, CloudFront (unified edge for API + web), ECR, Secrets Manager, Route 53, ACM.
- CI/CD: GitHub Actions with GitHub-hosted runners.
- Mobile builds: Expo EAS Build → TestFlight / Play Store.
- Migrations: Alembic (SQLAlchemy) — not Prisma or Flyway.
- Google Classroom: one-time roster import + Google sign-in only. No real-time sync in MVP.
- Subscription: free pilot tier. No payment infrastructure in MVP.
- No Redis in MVP — defer caching layer until load testing validates need.

### Cross-Cutting Concerns Identified

- Tenant safety and authorization consistency across every service boundary.
- Privacy-by-default data modeling and response shaping.
- Auditability for sensitive changes (grades, roles, consent, disclosure).
- Explainable AI outputs with confidence signaling and teacher authority.
- Offline-first resilience: photo queue, cached reads, graceful degradation.
- Push notification governance: cadence preferences, digest batching, deep-linking, device token lifecycle.
- Image pipeline: client-side compression → pre-signed URL upload → S3 → async AI processing.
- Observability, incident detection, SLO conformance.
- Accessibility (WCAG 2.1 AA) via Tamagui design tokens and shared components.
- Data lifecycle governance: retention, deletion/export, legal alignment.
- App store compliance: SDK audit, privacy labels, data safety sections.
- Onboarding flow architecture: invite links, join codes, CSV import, role-specific wizards.

## Starter Template Evaluation

### Primary Technology Domain

Mobile-centric full-stack multi-platform (React Native mobile + React SPA web + FastAPI backend).

### Starter Options Considered

1) **Expo starter (`create-expo-app`)**
- Strong fit for teacher/parent/student mobile apps.
- Supports Expo Router, TypeScript, and EAS Build out of the box.
- Limitation: does not scaffold backend or web admin.

2) **FastAPI full-stack template (`fastapi/full-stack-fastapi-template`)**
- Backend security, DB patterns, tests, CI/CD conventions.
- Limitation: web-frontend oriented, not mobile-first.

3) **Turborepo starter (`create-turbo`)**
- Monorepo scaling, shared packages, workspace-aware caching.
- Neutral foundation for multi-app architecture.

### Selected Starter: Turborepo (`create-turbo`) as repo foundation

**Rationale:** Teacher OS spans mobile apps, backend services, and web admin. A monorepo-first starter best matches cross-surface code sharing, shared contracts, and long-term maintainability.

**Initialization Command:**

```bash
npx create-turbo@latest
```

**Architectural Decisions Provided by Starter:**

**Language & Runtime:** TypeScript-first workspace baseline for JS/TS apps/packages; Python backend workspace added as separate workspace.

**Styling Solution:** Tamagui (selected in UX spec) provides cross-platform styling with build-time optimization.

**Build Tooling:** Turborepo task orchestration, caching, and workspace pipeline structure.

**Testing Framework:** Per-workspace test commands; shared CI task graph.

**Code Organization:** Monorepo with app/package separation and shared library patterns.

**Development Experience:** Parallel app/service workflows, incremental builds, scalable CI.

**Note:** Project initialization using this command should be the first implementation story.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Multi-tenant data isolation: shared DB + strict `org_id` scoping + DB-level guards.
- AuthN/AuthZ: JWT with refresh token rotation + centralized policy enforcement.
- API contract model: REST-first with OpenAPI as source of truth.
- Async job architecture: SQS-driven worker service with idempotency keys, separate from API service.
- Grade publication rule: immutable approval ledger; no visibility pre-approval.
- AI grading model: multimodal vision (no OCR); 2x retry; manual fallback always available.
- Deployment topology: separate ECS services for API and workers; CloudFront unified edge.

**Important Decisions (Shape Architecture):**
- Offline architecture: local photo queue + cached dashboard reads.
- Push notification topology: FCM/APNs with SQS-backed dispatch and cadence preferences.
- Image pipeline: client-side compression (~2MP) → pre-signed URL → S3 → async processing.
- Onboarding architecture: invite links, join codes, CSV import, role-specific guided wizards.
- Design system: Tamagui with shared design tokens across mobile and web.
- Monorepo package boundaries and shared contract library.
- Observability baseline (structured logs, traces, metrics, SLO alerting).

**Deferred Decisions (Post-MVP):**
- Redis/ElastiCache caching layer — add when load testing validates need.
- GraphQL federation / BFF specialization.
- Multi-region active-active deployment.
- Schema-per-tenant or DB-per-tenant enterprise isolation.
- Real-time websocket fanout.
- Payment infrastructure (Stripe) for paid tiers.

### Data Architecture

- Primary DB: PostgreSQL 16.x on RDS, with RDS Proxy for connection pooling.
- Data modeling: relational core with append-only grade_versions and audit_events tables.
- Validation: Pydantic models at API boundary + DB constraints for invariants.
- Migrations: Alembic with forward-only migrations; rollback via compensating migration policy.
- Caching: Deferred. No Redis in MVP. If rate limiting needed early, use in-memory sliding window per ECS task (sufficient for pilot scale).

### Authentication & Security

- Authentication: email/password + Google sign-in (OIDC).
- Token model: short-lived JWT access tokens (≤60min), rotating refresh tokens, per-device/session revocation.
- Authorization: policy module enforcing role + tenant + relationship checks on every protected endpoint.
- API security: strict input validation, signed URL upload flow, anti-enumeration responses.
- Encryption: TLS 1.2+ via CloudFront edge; encrypted storage at rest; secrets in AWS Secrets Manager only.
- Compliance controls: COPPA consent gate, FERPA-aligned access/disclosure workflows, auditable actions.
- COPPA consent gate: admin confirms consent collected → system activates under-13 accounts. Status recorded and auditable.

### API & Communication Patterns

- API style: REST + OpenAPI 3.1 contracts, versioned under `/v1`.
- Error standard: normalized error envelope with machine code + correlation ID.
- Async communication: SQS queues for AI grading and notification fanout. Worker service consumes independently.
- Reliability patterns: idempotency keys, retry policies with exponential backoff, dead-letter queues.
- Integration boundary: Google Classroom connector (one-time roster import) isolated from domain core.
- Push notification dispatch: backend service → SQS → worker → FCM/APNs. Device token management per user/platform.

### Frontend Architecture

- Mobile: Expo/React Native with Tamagui design system and shared design tokens.
  - Role-scoped bottom tab navigation (Teacher: 5 tabs + camera FAB; Parent: 4 tabs; Student: 4 tabs).
  - Camera-native grading workflow (snap → AI suggest → review → approve).
  - Offline photo queue (AsyncStorage/SQLite) with auto-upload on reconnect.
  - Cached dashboard views for offline reading (last-fetched data with "Last updated" timestamp).
  - Client-side image compression (~2MP) before upload using expo-image-manipulator.
  - Push notification handling via expo-notifications (FCM/APNs).
  - Skeleton loading states for all data-dependent screens.
  - Optimistic UI for grade approval, message send, preference changes.
- Web admin: React SPA (Vite) with Tamagui — same design tokens, web-specific layout.
  - Static deploy: S3 + CloudFront. No SSR, no compute cost.
  - Sidebar navigation for principal/admin roles.
  - Data-dense tables, charts, and filter-heavy interfaces.
- Shared packages: `packages/contracts` (OpenAPI types), `packages/design-tokens`, `packages/ui` (shared Tamagui components).
- State management: TanStack Query for server state; minimal local state (Zustand or React context) for UI-only state.
- Routing: Expo Router (file-based) for mobile; React Router for web. Role-scoped route trees with permission-aware guards.
- Accessibility: WCAG 2.1 AA. All color tokens validated for contrast. 44px minimum touch targets. Screen reader labels on all custom components. Reduced motion support.

### Infrastructure & Deployment

- Repo foundation: Turborepo monorepo with app/package boundaries.
- Backend runtime: FastAPI on ECS Fargate (containerized). Two separate ECS services:
  - `api` service: handles HTTP requests. Autoscales on CPU/request count.
  - `worker` service: consumes SQS queues (grading, notifications). Autoscales on `ApproximateNumberOfMessagesVisible`.
- Database: RDS PostgreSQL 16.x + RDS Proxy. Multi-AZ for production.
- Object storage: S3 with pre-signed URL upload. ECR lifecycle policy: keep last 10 tagged images per repo.
- Async: SQS queues with DLQ for grading and notification jobs.
- Edge: CloudFront in front of ALB (API) and S3 (web). Unified WAF on CloudFront distribution. Shield Standard (free) for DDoS baseline.
- DNS: Route 53. TLS: ACM certificates.
- Secrets: AWS Secrets Manager. ECS task definitions reference Secrets Manager ARNs directly.
- CI/CD: GitHub Actions (GitHub-hosted runners). Pipeline: lint → test → build → push to ECR → deploy to ECS (staging → manual gate → prod).
- Mobile builds: Expo EAS Build. Automated iOS (TestFlight) and Android (Play Store internal) builds in CI.
- Observability: CloudWatch logs/metrics/alarms. Structured JSON logs with correlation IDs.

### Decision Impact Analysis

**Implementation Sequence:**
1. Monorepo scaffold + CI/CD pipeline + ECS/RDS/S3 infrastructure
2. Auth/RBAC/tenant policy core + onboarding flows
3. Data schema + Alembic migration baseline
4. Grading ingest + async pipeline + approval ledger + manual fallback
5. Parent/student analytics and dashboard views
6. Messaging/notifications + push dispatch + cadence controls
7. Org analytics + admin web
8. Observability hardening + compliance workflows

**Cross-Component Dependencies:**
- Tenant policy affects every endpoint, query, and analytics aggregation.
- Grade approval ledger gates analytics visibility and notification triggers.
- Async worker reliability directly impacts teacher throughput and parent trust.
- Tamagui design tokens and shared UI components enforce visual consistency across mobile and web.
- Offline architecture requires careful sync ordering (photo upload → AI processing → notification).

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:**
22 areas where AI agents could make different choices and break consistency across services and clients.

### Naming Patterns

**Database Naming Conventions:**
- Tables: `snake_case` plural (`users`, `grade_versions`, `risk_signals`, `invite_links`).
- Columns: `snake_case` (`org_id`, `created_at`, `approved_by`, `consent_confirmed_at`).
- PK/FK: primary `id`; foreign keys as `<entity>_id`.
- Indexes: `idx_<table>_<column_list>` (example: `idx_grades_submission_id`).
- Constraints: `ck_<table>_<rule>`, `uq_<table>_<column_list>`, `fk_<table>_<ref_table>`.

**API Naming Conventions:**
- REST resources are plural nouns (`/v1/users`, `/v1/messages`, `/v1/invite-links`).
- Path params use `{id}` style in OpenAPI.
- Query params are `snake_case` in backend contracts.
- Header names follow standard HTTP casing; custom headers prefixed with `X-TeacherOS-`.

**Code Naming Conventions:**
- Python modules/functions/variables: `snake_case`; classes: `PascalCase`.
- TypeScript vars/functions: `camelCase`; types/components: `PascalCase`.
- File naming:
  - Python: `snake_case.py`
  - TS/RN components: `PascalCase.tsx`
  - Non-component TS files: `kebab-case.ts`.
- Tamagui tokens: `$camelCase` (e.g., `$primary`, `$textPrimary`, `$radiusMd`).

### Structure Patterns

**Project Organization:**
- Organize by bounded feature domain first, then by layer.
- Backend per-domain layout: `api/`, `service/`, `repo/`, `schemas/`, `policies/`.
- Shared cross-app contracts in dedicated package (`packages/contracts`).
- Shared UI components in `packages/ui` (Tamagui-based).
- Shared design tokens in `packages/design-tokens`.
- Tenant policy checks live in reusable policy module, never inline ad-hoc checks.

**File Structure Patterns:**
- Tests:
  - Backend: `tests/` mirror of source paths.
  - Frontend: co-located `*.test.ts(x)` for components/hooks.
- Config:
  - Root-level for monorepo/global tooling.
  - App-local config inside each app directory.

### Format Patterns

**API Response Formats:**
- Success envelope:
  - Read: `{ "data": ..., "meta": ... }`
  - Mutations: `{ "data": ..., "meta": { "request_id": "..." } }`
- Error envelope:
  - `{ "error": { "code": "STRING_CODE", "message": "Human readable", "details": {...}, "request_id": "..." } }`
- Status code discipline: `2xx` success, `4xx` client/auth/validation, `5xx` server/unexpected only.

**Data Exchange Formats:**
- External API JSON fields: `snake_case` (matches backend contracts).
- UI mapping layer converts to frontend-native naming if needed.
- Timestamps: ISO-8601 UTC (`YYYY-MM-DDTHH:MM:SSZ`).
- Booleans as true/false only.
- Null policy explicit in schemas.

### Communication Patterns

**Event System Patterns:**
- Event names: `domain.entity.action.v1` (example: `grading.submission.approved.v1`).
- Payload baseline: `event_id`, `event_name`, `occurred_at`, `org_id`, `actor_id`, `entity_id`, `version`, `data`.
- Events are immutable and versioned; schema changes require new version suffix.
- Consumers must be idempotent using `event_id`.

**Push Notification Patterns:**
- Notification dispatch: API enqueues to SQS → worker dequeues → dispatches to FCM/APNs.
- Device token management: `device_tokens` table, updated on app launch and token refresh.
- Cadence enforcement: worker checks `notification_preferences` before dispatch. Digest jobs run on cron (daily 6am, weekly Monday 6am user-local or UTC).
- Deep-linking: every push notification includes a deep-link URL resolved by mobile client to the relevant screen.
- Silent push: used to trigger background dashboard data refresh.

**State Management Patterns:**
- Server state via TanStack Query; UI state local/store only when not server-derived.
- State updates are immutable.
- Action names are verb-first (`approveGrade`, `setNotificationCadence`).
- Offline queue state managed in AsyncStorage/SQLite with sync status tracking.

### Process Patterns

**Error Handling Patterns:**
- Validation errors are structured and field-addressable.
- AuthZ failures return safe generic messages without leakage.
- User-facing messages are non-technical; detailed diagnostics go to logs.
- Correlation/request IDs included in all errors and logs.
- AI grading failures: clear reason + "Retake Photo" / "Grade Manually" forward actions. Never a dead end.

**Loading State Patterns:**
- Use explicit async states: `idle | loading | success | error`.
- Skeletons for first-load (warm-toned shimmer, 1.5s cycle), subtle spinners for background refresh.
- Disable destructive/conflicting actions during in-flight mutations.
- Retry UX: inline retry + fallback support path.

**Offline Patterns:**
- Photo capture: saved to local queue with "Pending" badge. Auto-uploads on reconnect. Push notification when AI grade ready.
- Dashboard viewing: cached data shown with "Last updated: [timestamp]" banner. Background refresh on reconnect.
- Messaging: queued with "Sending..." status. Auto-sends on reconnect. Timestamp reflects send time.
- Grade approval: optimistic "Approved" state, rollback if server rejects.
- Sign-in: requires network — not available offline.

### Enforcement Guidelines

**All AI Agents MUST:**
- Reuse shared contracts/schemas; do not invent endpoint or payload variants.
- Apply tenant and authorization checks through central policy utilities.
- Follow naming/format conventions exactly.
- Use Tamagui design tokens for all colors, spacing, typography — never hardcode values.
- Implement offline patterns using the queue/cache/sync approach defined above.

**Pattern Enforcement:**
- CI checks: lint, format, schema validation, API contract diff checks, test suites, accessibility scans.
- PR template includes "pattern compliance" checklist.
- Pattern updates require architecture doc update before code divergence.

### Pattern Examples

**Good Examples:**
- Endpoint: `GET /v1/students/{student_id}/risk-signals?from=...&to=...`
- Error: `{ "error": { "code": "FORBIDDEN", "message": "Access denied", "request_id": "req_123" } }`
- Event: `notifications.digest.generated.v1` with immutable payload including `org_id`.
- Push: `{ "notification": { "title": "Weekly Summary", "body": "Ava improved in Math" }, "data": { "deep_link": "/students/123/progress" } }`
- Offline photo: saved to AsyncStorage queue → `{ id, image_uri, assignment_id, queued_at, sync_status: "pending" }`

**Anti-Patterns:**
- Mixed naming (`userId` in one API, `user_id` in another).
- Direct DB query in handler bypassing policy module.
- Unversioned event names (`GradeApproved`) with unstable payload shapes.
- Frontend assuming grade visibility before approval gate is satisfied.
- Hardcoded color hex values instead of Tamagui tokens.
- Secrets in environment variables or Docker image layers.
- Single ECS service handling both API requests and background jobs.

## Project Structure & Boundaries

### Complete Project Directory Structure

```text
ilm/
├── README.md
├── LICENSE
├── .gitignore
├── .editorconfig
├── .env.example
├── turbo.json
├── package.json
├── pnpm-workspace.yaml
├── pyproject.toml
├── Makefile
├── docker-compose.yml
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── deploy-staging.yml
│       ├── deploy-prod.yml
│       ├── mobile-build.yml
│       └── security.yml
├── apps/
│   ├── mobile/
│   │   ├── app.json
│   │   ├── package.json
│   │   ├── babel.config.js
│   │   ├── tsconfig.json
│   │   ├── eas.json
│   │   ├── app/
│   │   │   ├── (teacher)/
│   │   │   │   ├── _layout.tsx
│   │   │   │   ├── index.tsx (home)
│   │   │   │   ├── grade.tsx
│   │   │   │   ├── plan.tsx
│   │   │   │   ├── messages.tsx
│   │   │   │   └── settings.tsx
│   │   │   ├── (parent)/
│   │   │   │   ├── _layout.tsx
│   │   │   │   ├── index.tsx (dashboard)
│   │   │   │   ├── progress.tsx
│   │   │   │   ├── messages.tsx
│   │   │   │   └── settings.tsx
│   │   │   ├── (student)/
│   │   │   │   ├── _layout.tsx
│   │   │   │   ├── index.tsx (growth)
│   │   │   │   ├── progress.tsx
│   │   │   │   ├── tips.tsx
│   │   │   │   └── settings.tsx
│   │   │   ├── auth/
│   │   │   ├── onboarding/
│   │   │   └── _layout.tsx
│   │   ├── src/
│   │   │   ├── features/
│   │   │   │   ├── auth/
│   │   │   │   ├── onboarding/
│   │   │   │   ├── grading/
│   │   │   │   │   ├── components/ (GradingCard, CameraCapture, BatchProgress)
│   │   │   │   │   ├── hooks/
│   │   │   │   │   └── services/
│   │   │   │   ├── courses/
│   │   │   │   ├── analytics/
│   │   │   │   │   ├── components/ (TrendIndicator, GrowthTimeline)
│   │   │   │   │   ├── hooks/
│   │   │   │   │   └── services/
│   │   │   │   ├── messages/
│   │   │   │   │   ├── components/ (ContextualMessageComposer)
│   │   │   │   │   ├── hooks/
│   │   │   │   │   └── services/
│   │   │   │   └── notifications/
│   │   │   ├── services/
│   │   │   │   ├── api-client.ts
│   │   │   │   ├── offline-queue.ts
│   │   │   │   ├── image-compressor.ts
│   │   │   │   └── push-notifications.ts
│   │   │   ├── state/
│   │   │   │   ├── query-client.ts
│   │   │   │   └── offline-store.ts
│   │   │   ├── hooks/
│   │   │   └── utils/
│   │   └── __tests__/
│   ├── admin-web/
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── vite.config.ts
│   │   ├── index.html
│   │   ├── src/
│   │   │   ├── App.tsx
│   │   │   ├── main.tsx
│   │   │   ├── routes/
│   │   │   ├── features/
│   │   │   │   ├── org-analytics/
│   │   │   │   ├── users-roles/
│   │   │   │   ├── school-setup/
│   │   │   │   └── safety-config/
│   │   │   ├── components/
│   │   │   ├── services/
│   │   │   └── utils/
│   │   └── __tests__/
│   └── api/
│       ├── pyproject.toml
│       ├── alembic.ini
│       ├── Dockerfile
│       ├── app/
│       │   ├── main.py
│       │   ├── api/
│       │   │   └── v1/
│       │   │       ├── auth.py
│       │   │       ├── users.py
│       │   │       ├── onboarding.py
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
│       │   │   ├── logging.py
│       │   │   └── dependencies.py
│       │   ├── domains/
│       │   │   ├── auth/
│       │   │   ├── users/
│       │   │   ├── onboarding/
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
│       │   │   ├── digest_jobs.py
│       │   │   └── retry_policies.py
│       │   └── integrations/
│       │       └── google_classroom/
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
│   │   ├── colors.ts
│   │   ├── typography.ts
│   │   ├── spacing.ts
│   │   └── tamagui.config.ts
│   ├── ui/
│   │   ├── TrendIndicator.tsx
│   │   ├── GradingCard.tsx
│   │   ├── GrowthTimeline.tsx
│   │   ├── ContextualMessageComposer.tsx
│   │   ├── OnboardingWizard.tsx
│   │   ├── SkeletonLoader.tsx
│   │   └── index.ts
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
│   │       ├── ecs/
│   │       ├── rds/
│   │       ├── s3/
│   │       ├── sqs/
│   │       ├── cloudfront/
│   │       ├── ecr/
│   │       └── secrets/
│   ├── docker/
│   │   ├── api.Dockerfile
│   │   └── worker.Dockerfile
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
- Domain endpoints map 1:1 with PRD FR groups.
- Workers only consume queued jobs; no direct client-facing logic.

**Component Boundaries:**
- Mobile and web apps consume only `packages/contracts` and shared UI/token packages.
- Feature modules in each app are role-scoped and cannot call DB or worker layers.
- Backend domain services do not import frontend packages.

**Service Boundaries:**
- API service and worker service are separate ECS services with independent scaling.
- Domain services call repositories, not raw SQL in handlers.
- Integrations isolated under `app/integrations/*` behind domain interfaces.
- Notification and grading orchestration occurs via workers with idempotent event handling.

**Data Boundaries:**
- DB access only through repository layer.
- Tenant boundary on all tables via `org_id`.
- RDS Proxy for all connections (API and worker).
- Analytics aggregates expose privacy-safe views for org roles.
- S3 artifact access only through signed URL workflows.

### Requirements to Structure Mapping

**Feature/Epic Mapping:**
- Epic 1 (Identity/RBAC/Onboarding): `apps/api/app/domains/auth`, `users`, `onboarding`, `core/security.py`, `tests/security`. Mobile: `features/auth`, `features/onboarding`.
- Epic 2 (Course creation): `domains/courses`. Mobile: `features/courses`.
- Epic 3 (AI grading): `domains/grading`, `workers/grading_jobs.py`. Mobile: `features/grading` (GradingCard, CameraCapture, offline-queue).
- Epic 4 (Student/Parent analytics): `domains/analytics`. Mobile: `features/analytics` (TrendIndicator, GrowthTimeline).
- Epic 5 (Messaging/notifications): `domains/messaging`, `domains/notifications`, `workers/notification_jobs.py`, `workers/digest_jobs.py`. Mobile: `features/messages`, `features/notifications`, `services/push-notifications.ts`.
- Epic 6 (Org dashboard): `admin-web/features/org-analytics`, API `domains/org_analytics`.

**Cross-Cutting Concerns:**
- Tenant safety: `core/tenancy.py` + security tests.
- Audit logging: `core/logging.py` + audit events in DB models.
- Accessibility: shared design tokens/UI packages + CI accessibility scans.
- Contracts consistency: `packages/contracts` (OpenAPI + schemas + events).
- Offline support: `services/offline-queue.ts`, `state/offline-store.ts`.
- Image pipeline: `services/image-compressor.ts` (mobile), S3 pre-signed URL service (API).

### Integration Points

**Internal Communication:**
- App clients → API via OpenAPI contract clients (TanStack Query).
- API → SQS for grading/notification jobs.
- Worker → DB + AI providers + push notification services.

**External Integrations:**
- Google Classroom connector in `app/integrations/google_classroom` (one-time roster import + sign-in).
- AI vision model provider (Claude API / OpenAI API) called from grading worker.
- FCM/APNs for push notification delivery.
- S3 via pre-signed URL for image upload/download.

**Data Flow:**
- Teacher capture → client compress (~2MP) → pre-signed URL → S3 → SQS grading job → AI vision model → grade suggestion → teacher approval → grade_version write → parent/student dashboards + notification dispatch (per cadence).
- Parent message → messaging domain → thread persistence → read-state updates → digest pipeline.
- Offline: teacher capture → local queue → auto-upload on reconnect → normal flow resumes.

### Development Workflow Integration

**Development Server Structure:**
- Turborepo runs `mobile`, `admin-web`, and `api` concurrently.
- Shared package changes propagate through workspace graph.
- `docker-compose.yml` for local PostgreSQL + localstack (S3/SQS).

**Build Process Structure:**
- Lint/test/typecheck per workspace + contract diff checks + accessibility scans.
- Python and Node pipelines executed with cache-aware Turborepo tasks.

**Deployment Structure:**
- API + worker containers: GitHub Actions → build → push to ECR → deploy to ECS Fargate (staging → manual gate → prod).
- Admin web: GitHub Actions → build → sync to S3 → CloudFront invalidation.
- Mobile: GitHub Actions → trigger Expo EAS Build → TestFlight / Play Store.
- Infra: Terraform in `infra/terraform/envs/*`, applied via CI with plan → approve → apply.

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
All major decisions are compatible: Turborepo monorepo + Expo mobile + Tamagui design system + Vite SPA web + FastAPI backend + PostgreSQL/RDS + RDS Proxy + AWS queue/storage model. Security, tenancy, and approval-gate rules align with API and data-layer patterns. Separate ECS services for API and worker prevent resource contention. CloudFront unified edge simplifies WAF/TLS/DDoS. No Redis in MVP avoids unnecessary operational complexity.

**Pattern Consistency:**
Implementation patterns are internally consistent across naming, structure, formatting, events, offline handling, and push notification patterns. API/data naming conventions align with backend-first contract strategy. Tamagui token-driven styling prevents visual inconsistency across mobile and web.

**Structure Alignment:**
Project structure supports all declared decisions, including domain separation, worker isolation, offline services, push notification handling, image compression, integration adapters, and shared packages for contracts/tokens/UI.

### Requirements Coverage Validation ✅

**Epic/Feature Coverage:**
All 6 epics are mapped to explicit domains/modules with both backend and frontend locations specified.

**Functional Requirements Coverage:**
All 48 FRs (FR1–FR48) are architecturally covered:
- FR1–FR9e: auth, onboarding, invite links, join codes, CSV import, COPPA consent gate.
- FR10–FR18b: courses, grading pipeline with multimodal AI, retry, manual fallback.
- FR19–FR26: analytics, dashboards, longitudinal views, growth framing.
- FR27–FR30: messaging, notifications, cadence preferences, push dispatch.
- FR31–FR34: org analytics, privacy-safe aggregates.
- FR35–FR45: audit, compliance, admin, Google Classroom import.
- FR46–FR48: offline photo queue, cached dashboards, image compression.

**Non-Functional Requirements Coverage:**
All 28 NFRs addressed:
- Performance: separate ECS services, async offloading, client-side compression, CloudFront edge.
- Reliability: worker retries/DLQ/idempotency, RDS Multi-AZ, PITR backups.
- Security: centralized policy, Secrets Manager, CloudFront TLS, audit trails.
- Accessibility: Tamagui tokens, WCAG 2.1 AA, CI accessibility scans.
- Scalability: horizontal API/worker scaling, SQS-based autoscaling, RDS Proxy.
- Observability: structured logs, CloudWatch alarms, distributed traces.

### Implementation Readiness Validation ✅

**Decision Completeness:**
All critical and important decisions documented with rationale. Deferred decisions identified with clear triggers for when to revisit (Redis: load testing; payments: Growth phase).

**Structure Completeness:**
Directory tree is concrete with explicit modules, role-scoped routes, offline services, and infrastructure layout.

**Pattern Completeness:**
All conflict vectors addressed: naming, payload formats, event schema, policy reuse, error/loading/offline behavior, push notification patterns, Tamagui token usage.

### Gap Analysis Results

**Critical Gaps:** None identified.

**Important Gaps:**
- Finalize exact worker runtime (Celery vs ARQ vs native asyncio consumer) in implementation story.
- Confirm Expo SDK version and Tamagui version compatibility during scaffold story.
- Define exact AI provider contract (Claude vs OpenAI vs abstraction layer) in grading implementation story.

**Nice-to-Have Gaps:**
- Sample payload fixtures in `packages/contracts` for key endpoints/events.
- ADR files for tenant model and approval-gate invariants.
- Policy test matrix mapping each role × endpoint group.

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Project context thoroughly analyzed (48 FRs, 28 NFRs)
- [x] Scale and complexity assessed (High)
- [x] Technical constraints identified (mobile-first, offline, multimodal AI, compliance)
- [x] Cross-cutting concerns mapped (12 identified)

**✅ Architectural Decisions**
- [x] Critical decisions documented with versions
- [x] Technology stack fully specified (including Tamagui, Alembic, RDS Proxy, ECS topology)
- [x] Integration patterns defined (Google Classroom, AI providers, FCM/APNs)
- [x] Performance considerations addressed (separate services, compression, caching deferred)
- [x] Deployment topology fully specified (CloudFront → ALB → ECS; S3 for web)

**✅ Implementation Patterns**
- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified (REST, events, push notifications)
- [x] Process patterns documented (error, loading, offline)

**✅ Project Structure**
- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** High

**Key Strengths:**
- Strong tenant/RBAC/compliance-first architecture
- Clear multi-agent consistency rules
- Concrete structure-to-requirement mapping for all 48 FRs
- Explicit async and approval-gate flow design
- Comprehensive offline/connectivity architecture
- Specific deployment topology with cost-conscious decisions (no Redis MVP, SPA web, RDS Proxy)
- Full alignment with UX spec (Tamagui, role-scoped nav, component specs)

**Areas for Future Enhancement:**
- Redis/ElastiCache when load testing validates need
- Deeper integration contracts beyond Google Classroom
- Enterprise tenant-isolation evolution path
- Payment infrastructure for Growth phase
- Expanded event catalog and contract-test automation

### Implementation Handoff

**AI Agent Guidelines:**
- Follow all architectural decisions exactly as documented.
- Use implementation patterns consistently across all components.
- Respect project structure and boundaries.
- Use Tamagui design tokens for all visual properties — never hardcode.
- Implement offline patterns using the queue/cache/sync approach.
- All secrets via Secrets Manager — never env vars or Docker images.
- Refer to this document for all architectural questions.

**First Implementation Priority:**
1. Initialize monorepo: `npx create-turbo@latest`
2. Scaffold `apps/api` (FastAPI), `apps/mobile` (Expo), `apps/admin-web` (Vite + Tamagui)
3. Set up `packages/design-tokens`, `packages/contracts`, `packages/ui`
4. Provision AWS infrastructure (ECS, RDS + RDS Proxy, S3, SQS, ECR, CloudFront, Secrets Manager)
5. Set up CI/CD pipeline (GitHub Actions → ECR → ECS deploy + Expo EAS Build)
6. Establish app store submission pipeline (TestFlight + Play Store internal) from sprint 1
