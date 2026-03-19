# Story 4.2: Local Infrastructure with Docker Compose

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want local infrastructure running via Docker Compose with PostgreSQL, MinIO (S3-compatible), and the FastAPI backend containerized,
So that the team can develop, test, and demo the full platform on a single machine without cloud credentials.

## Acceptance Criteria

1. **Docker Compose starts all services successfully:**
   - Running `docker compose up` starts: PostgreSQL 16.x, MinIO (S3-compatible object storage), FastAPI API service, and FastAPI worker service
   - All services are healthy and connected within 30 seconds
   - Health checks are defined for every service

2. **API service starts with database connectivity:**
   - The API service starts and connects to the local PostgreSQL instance
   - Alembic migrations run automatically against the local PostgreSQL on startup
   - The API health endpoint (`GET /health`) returns 200 with database connectivity status
   - The existing 268 API tests continue to pass without regressions

3. **Dockerfiles for API and worker services:**
   - Both API and worker services build successfully from shared Dockerfile(s)
   - Hot-reload is supported for local development via volume mounts (source code mounted into container)
   - Worker service uses same image but different entrypoint/command
   - Python 3.12+ base image used

4. **MinIO provides S3-compatible object storage:**
   - Pre-signed URL service generates time-limited MinIO pre-signed upload URLs scoped to the user's organization path
   - URLs expire after 15 minutes and enforce org-scoped storage paths (`{org_id}/{class_id}/{student_id}/{assignment_id}/`)
   - The same S3 client code (boto3) works against both MinIO (local) and AWS S3 (future cloud) — only endpoint URL config changes
   - A default bucket (`ilm-assignments`) is auto-created on startup

5. **Email service is provider-agnostic:**
   - Email service logs to console for development visibility (no real SMTP needed locally)
   - The email service interface is provider-agnostic so swapping to SES later requires only config change
   - Supports transactional emails: invitations, password resets

6. **RBAC authorization middleware is operational:**
   - The API has centralized RBAC middleware that validates: JWT authenticity, user role, organization membership, and resource ownership on protected endpoints
   - Unauthorized requests are rejected with 403 and logged
   - No protected endpoint is accessible without passing through the middleware
   - Tenant isolation is enforced on all org-scoped queries via `org_id` filtering

7. **Push notification infrastructure is stubbed:**
   - Device token registration endpoint exists (stores token linked to user account)
   - Token refresh/rotation is handled
   - Local mode logs notifications to console instead of calling FCM/APNs
   - Interface is provider-agnostic for future FCM/APNs integration

8. **Async job processing is operational:**
   - Jobs (grading, notifications) are processed via FastAPI BackgroundTasks locally
   - The job interface is queue-agnostic so swapping to SQS later requires only config change
   - Job dispatch and completion are logged with correlation IDs

## Tasks / Subtasks

- [ ] Task 1: Create Docker Compose configuration (AC: #1)
  - [ ] Create `docker-compose.yml` at project root (or `infra/docker/docker-compose.yml` per architecture)
  - [ ] Define PostgreSQL 16.x service with persistent volume, health check, env vars
  - [ ] Define MinIO service with pre-created bucket, health check, console access
  - [ ] Define API service with Dockerfile reference, volume mount for hot-reload, env vars, depends_on
  - [ ] Define Worker service (same image, different entrypoint), depends_on
  - [ ] Create `.env.example` with all required environment variables documented

- [ ] Task 2: Create Dockerfile for API/Worker (AC: #3)
  - [ ] Create `infra/docker/api.Dockerfile` with Python 3.12+ base
  - [ ] Install dependencies from `pyproject.toml` via `uv` or `pip`
  - [ ] Configure for hot-reload in dev (uvicorn --reload with volume mount)
  - [ ] Worker uses same Dockerfile with CMD override in docker-compose

- [ ] Task 3: Add database layer with SQLAlchemy + Alembic (AC: #2)
  - [ ] Add SQLAlchemy 2.x, asyncpg (or psycopg[async]), and Alembic to `pyproject.toml` dependencies
  - [ ] Create `app/db/base.py` with SQLAlchemy async engine and session factory
  - [ ] Create `app/db/session.py` with async session dependency for FastAPI
  - [ ] Initialize Alembic configuration (`alembic.ini` + `app/db/migrations/`)
  - [ ] Create initial migration with empty schema (ready for Story 4.3 to add tables)
  - [ ] Add startup event to run Alembic migrations automatically on API boot
  - [ ] Add `/health` endpoint that checks database connectivity

- [ ] Task 4: Create S3/MinIO service abstraction (AC: #4)
  - [ ] Create `app/core/storage.py` with provider-agnostic S3 client (boto3)
  - [ ] Implement pre-signed URL generation (upload + download) with org-scoped paths
  - [ ] Configure to use MinIO endpoint locally, AWS S3 endpoint in production (env-driven)
  - [ ] Add `POST /v1/storage/presigned-url` endpoint for requesting upload URLs
  - [ ] Enforce 15-minute URL expiry and org-scoped path validation

- [ ] Task 5: Create email service abstraction (AC: #5)
  - [ ] Create `app/core/email.py` with provider-agnostic email interface
  - [ ] Implement `ConsoleEmailProvider` for local dev (logs email content)
  - [ ] Define interface for future `SESEmailProvider`
  - [ ] Support invitation and password reset email templates (basic text)

- [ ] Task 6: Implement RBAC authorization middleware (AC: #6)
  - [ ] Create `app/core/tenancy.py` — centralized tenant/org isolation policy module
  - [ ] Create authorization middleware that validates JWT + role + org membership + resource ownership
  - [ ] Apply middleware to all protected router groups
  - [ ] Ensure 403 response with logged details for unauthorized access
  - [ ] Write tests for authorization middleware (role-based, tenant-scoped)

- [ ] Task 7: Stub push notification infrastructure (AC: #7)
  - [ ] Create `app/core/notifications.py` with provider-agnostic notification interface
  - [ ] Implement `ConsoleNotificationProvider` for local dev
  - [ ] Add device token registration API endpoint (`POST /v1/notifications/device-token`)
  - [ ] Define interface for future FCM/APNs providers

- [ ] Task 8: Create async job processing abstraction (AC: #8)
  - [ ] Create `app/core/jobs.py` with queue-agnostic job interface
  - [ ] Implement `BackgroundTasksJobProvider` using FastAPI BackgroundTasks
  - [ ] Define interface for future SQS-based provider
  - [ ] Add job dispatch logging with correlation IDs
  - [ ] Wire into existing grading/notification workflows

- [ ] Task 9: Update configuration and settings (AC: #1, #2)
  - [ ] Extend `app/core/settings.py` with database URL, MinIO config, email config, job queue config
  - [ ] All settings driven by environment variables with sensible local defaults
  - [ ] Create `.env.example` documenting all variables
  - [ ] Update `app/core/config.py` if needed for centralized config loading

- [ ] Task 10: Integration testing and verification (AC: #1, #2)
  - [ ] Verify `docker compose up` brings all services healthy
  - [ ] Verify API health endpoint returns 200 with DB status
  - [ ] Verify existing 268 API tests still pass (zero regressions)
  - [ ] Verify MinIO pre-signed URL generation works
  - [ ] Verify email logging works in dev mode
  - [ ] Add basic smoke tests for new infrastructure

## Dev Notes

### Critical: Existing Code Preservation

The `apps/api/` directory contains a **fully functional FastAPI backend** from Epics 1-3 with:
- Complete auth system (email/password + Google OIDC) with JWT tokens
- Admin endpoints (org/user/role management, invitations)
- Course generation with revision history
- Grading pipeline with async AI jobs, recommendations
- Student/progress/notification endpoints
- Comprehensive test suite (13 test files, 268 tests)
- **All repositories currently use in-memory storage** — this is intentional, Story 4.3 will add real database tables

**DO NOT break existing API functionality.** The API must continue to run with `uvicorn app.main:app`. The database layer should be additive — existing in-memory repositories remain functional until Story 4.3 replaces them with SQLAlchemy-backed repositories.

### Current API Structure

```
apps/api/
├── app/
│   ├── main.py              # FastAPI app with all routers included
│   ├── core/
│   │   ├── security.py       # JWT token handling, password hashing
│   │   ├── settings.py       # Environment-driven config (JWT, Google OIDC)
│   │   ├── roles.py          # Role definitions
│   │   └── rate_limit.py     # Rate limiting
│   └── domains/
│       ├── auth/             # Auth (email/pwd + Google OIDC), dependencies
│       ├── admin/            # Org/user/role management
│       ├── courses/          # Course generation
│       ├── grading/          # AI grading pipeline
│       ├── students/         # Student management
│       ├── progress/         # Progress tracking
│       └── notifications/    # Notification management
├── tests/                    # 13 test files, 268 tests
├── pyproject.toml            # Dependencies (FastAPI, bcrypt, PyJWT, etc.)
└── uv.lock                   # Lock file (uses uv package manager)
```

**Key observations from Story 4.1:**
- Package manager is **uv** (not pip) — Dockerfile should use `uv` for dependency installation
- The API starts with `uvicorn app.main:app`
- Settings uses dataclass with `os.getenv()` — extend this pattern, don't replace it
- No database layer exists yet — `app/db/` directory needs to be created from scratch
- No Docker files exist yet
- The `turbo.json` has basic task orchestration configured
- Existing tests use `httpx` with pytest

### Architecture Patterns and Constraints

**Docker Compose Services (from Architecture doc):**
- `postgres`: PostgreSQL 16.x with persistent volume
- `minio`: MinIO with pre-created bucket for assignment images
- `api`: FastAPI application (hot-reload via volume mount)
- `worker`: FastAPI worker service (same image, different entrypoint)

**Provider-Agnostic Abstractions (CRITICAL):**
The architecture mandates provider-agnostic interfaces for all external services. This story must create abstraction layers that allow swapping local services for cloud services via config only:

| AWS Service (Future) | Local Replacement | Interface Pattern |
|---|---|---|
| RDS PostgreSQL | PostgreSQL 16.x in Docker | SQLAlchemy/Alembic (unchanged) |
| S3 (file storage) | MinIO (S3-compatible) | boto3 S3 client (same SDK, different endpoint) |
| SQS (queues) | FastAPI BackgroundTasks | Queue interface abstraction |
| SES (email) | Console logging | Email service interface |
| FCM/APNs (push) | Console logging | Notification provider interface |

**Database Configuration:**
- SQLAlchemy 2.x with async support
- asyncpg or psycopg[async] as PostgreSQL driver
- Alembic for migrations (forward-only, compensating migration rollback policy)
- Connection string: `postgresql+asyncpg://user:password@postgres:5432/ilm`
- All tables will include `org_id` for tenant isolation (implemented in Story 4.3)

**API Naming Conventions:**
- REST resources plural nouns: `/v1/storage/presigned-url`
- Path params: `{id}` style
- Error envelope: `{ "error": { "code": "STRING_CODE", "message": "...", "request_id": "..." } }`
- Success envelope: `{ "data": ..., "meta": { "request_id": "..." } }`

**Python Code Conventions:**
- Modules/functions/variables: `snake_case`
- Classes: `PascalCase`
- File naming: `snake_case.py`
- Backend per-domain layout: `api/`, `service/`, `repo/`, `schemas/`, `policies/`

**RBAC Middleware Requirements:**
- Central policy module in `app/core/tenancy.py` — never inline ad-hoc checks
- Validates: JWT authenticity → user role → org membership → resource ownership
- All protected endpoints must pass through this middleware
- 403 for unauthorized with safe generic message (no data leakage)
- Correlation/request IDs in all error responses and logs

**Environment Variables Pattern:**
- All config via env vars with sensible local defaults
- Database: `DATABASE_URL=postgresql+asyncpg://ilm:ilm@postgres:5432/ilm`
- MinIO: `S3_ENDPOINT_URL=http://minio:9000`, `S3_ACCESS_KEY=minioadmin`, `S3_SECRET_KEY=minioadmin`, `S3_BUCKET=ilm-assignments`
- Email: `EMAIL_PROVIDER=console` (future: `ses`)
- Jobs: `JOB_PROVIDER=background_tasks` (future: `sqs`)
- Push: `NOTIFICATION_PROVIDER=console` (future: `fcm_apns`)

### Previous Story Intelligence (Story 4.1)

**Key learnings from Story 4.1:**
- pnpm workspace is already configured with `apps/*` and `packages/*`
- Turborepo task orchestration works for TS workspaces
- The API is Python-based — Turborepo handles it via custom task definitions
- Package naming convention: `@ilm/<package-name>`
- Network issues were encountered with npm registry — may need mirror configuration
- All 268 API tests pass — this is the regression baseline
- uv is the Python package manager (not pip)

**Code review fixes applied in Story 4.1:**
- Replaced hardcoded hex colors with design token imports
- Added `*.tsbuildinfo` to `.gitignore`
- Wired up eslint-plugin-import ordering rules

### Git Intelligence

**Recent commits:**
- `93c0fd5` - 4.1 done (monorepo scaffold complete)
- `31ed0bf` - local demo epics and stories setup
- Prior commits: architecture update, PRD validation, epics 1-3 completion

**Patterns established:**
- uv for Python dependency management
- Existing tests use httpx + pytest
- Settings pattern: dataclass with `os.getenv()` calls
- In-memory repositories as placeholder pattern

### What This Story Does NOT Include

- **No database tables/models** — Story 4.3 creates the actual schema
- **No mobile app changes** — Mobile auth is Stories 4.5/4.6
- **No real AI grading integration** — Just the job processing abstraction
- **No real email sending** — Just the abstraction with console logging
- **No real push notifications** — Just the device token registration and console logging
- **No CI/CD changes** — Infrastructure stays local
- **No Terraform/AWS resources** — Everything runs in Docker locally

### Technology Version Guidance

- **PostgreSQL:** `postgres:16.6-alpine` Docker image. Health check: `pg_isready -U $USER -d $DB`
- **MinIO:** `minio/minio:latest` (or pin to dated release tag like `RELEASE.2025-04-22T...`). Ports: 9000 (S3 API) + 9001 (web console). Health check: `curl -f http://localhost:9000/minio/health/live`. Command: `server /data --console-address ":9001"`. Default creds: `MINIO_ROOT_USER=minioadmin`, `MINIO_ROOT_PASSWORD=minioadmin`
- **SQLAlchemy:** 2.0.38+ (async support fully stable). Use `create_async_engine` + `async_sessionmaker`. **Critical:** set `expire_on_commit=False` for async sessions — without it, attribute access after commit triggers lazy loads that fail outside async context. Use 2.0-style declarative: `DeclarativeBase`, `Mapped[]`, `mapped_column()`
- **Alembic:** 1.14.x. For async: use `connection.run_sync()` to bridge async engine to sync migration context in `env.py`. Import `Base.metadata` as `target_metadata` for autogenerate
- **asyncpg:** 0.30.x — de facto standard async PostgreSQL driver. Connection string prefix: `postgresql+asyncpg://`. Fastest pure-async driver with broadest ecosystem adoption
- **boto3:** Latest stable (S3 client — same SDK works for MinIO and AWS S3, only endpoint URL differs)
- **Python:** `python:3.12-slim` base image. Use `uv` for dependency installation (established in Story 4.1)
- **Docker Compose:** Modern format — **no `version:` key** (deprecated/ignored). Use `depends_on` with `condition: service_healthy` for startup ordering
- **Dockerfile pattern for uv:** `RUN pip install uv && uv sync --frozen --no-dev`. For dev hot-reload: volume mount source code + `uvicorn --reload --reload-dir /app`

### Project Structure Notes

New files/directories this story creates:
```
apps/api/
├── Dockerfile                    # (or infra/docker/api.Dockerfile)
├── alembic.ini                   # Alembic configuration
├── app/
│   ├── core/
│   │   ├── config.py             # Centralized config loading (extend settings.py)
│   │   ├── tenancy.py            # Tenant isolation policy module
│   │   ├── storage.py            # S3/MinIO provider-agnostic client
│   │   ├── email.py              # Email provider abstraction
│   │   ├── notifications.py      # Push notification provider abstraction (extend existing)
│   │   └── jobs.py               # Queue-agnostic job processing
│   └── db/
│       ├── base.py               # SQLAlchemy engine/session factory
│       ├── session.py            # FastAPI session dependency
│       └── migrations/
│           ├── env.py            # Alembic environment
│           └── versions/         # Migration scripts (empty for now)
├── docker-compose.yml            # (or at project root)
└── .env.example                  # Environment variable documentation
```

- Align with architecture doc: `app/core/*` for cross-cutting concerns, `app/db/*` for database layer
- Tests mirror source paths in `tests/` directory
- The `app/domains/notifications/` already exists — coordinate with the new `app/core/notifications.py` abstraction

### Testing Standards

- Backend: `tests/` mirror of source paths
- Existing 268 tests MUST continue to pass (zero regression tolerance)
- New tests for:
  - RBAC middleware (role-based access, tenant isolation)
  - S3 pre-signed URL generation (mock boto3)
  - Email service abstraction
  - Job processing abstraction
  - Health endpoint with DB check
- Use httpx + pytest (established pattern)
- Integration tests can use docker compose services

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Local Development & Demo Deployment (MVP)] — Docker Compose service topology and provider-agnostic abstractions
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture] — SQLAlchemy, Alembic, PostgreSQL patterns
- [Source: _bmad-output/planning-artifacts/architecture.md#Authentication & Security] — JWT auth, RBAC, tenant isolation
- [Source: _bmad-output/planning-artifacts/architecture.md#API & Communication Patterns] — REST conventions, error handling, async patterns
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns & Consistency Rules] — Naming, structure, process patterns
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries] — Complete directory structure
- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.2] — Story requirements and acceptance criteria
- [Source: _bmad-output/planning-artifacts/prd.md#Technical Architecture Considerations] — Deployment topology, provider-agnostic design
- [Source: _bmad-output/implementation-artifacts/4-1-initialize-turborepo-monorepo-and-project-scaffold.md] — Previous story learnings and established patterns

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

### Completion Notes List

### File List
