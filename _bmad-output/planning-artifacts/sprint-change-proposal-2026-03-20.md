# Sprint Change Proposal — Local-First Infrastructure

**Date:** 2026-03-20
**Author:** Correct Course workflow (elephant)
**Status:** Approved
**Scope:** Minor — direct implementation by dev team

---

## Section 1: Issue Summary

**Problem statement:** Epic 4, Story 4.2 ("AWS Infrastructure, CI/CD, and Core Platform Services") specifies full AWS deployment — Terraform, ECS Fargate, RDS, S3, SQS, SES, CloudFront, ECR, Secrets Manager — but elephant does not have AWS credentials available. The demo will run locally on an Arch Linux system.

**Discovery context:** Identified during Epic 3 retrospective (2026-03-19) when reviewing Epic 4 readiness. elephant confirmed no AWS account is available for the project.

**Evidence:** Epic 3 retrospective documents the discovery explicitly with a local stack replacement table and recommends this correct-course workflow as a critical-path blocker before Epic 4.

---

## Section 2: Impact Analysis

### Epic Impact

- **Epic 4** (Platform Bootstrap, Mobile Auth & Onboarding): Only Story 4.2 affected. All other stories (4.1, 4.3–4.10) consume the infrastructure — they don't care whether PostgreSQL runs on RDS or Docker.
- **Epics 5–11:** No impact. These epics consume API endpoints, not infrastructure primitives. The backend API contract is identical regardless of hosting.
- **No epics added, removed, or resequenced.**

### Story Impact

- **Story 4.2:** Fully rewritten. Title changed from "AWS Infrastructure, CI/CD, and Core Platform Services" to "Local Infrastructure with Docker Compose." All AWS-specific acceptance criteria replaced with Docker Compose equivalents.
- **Story 4.3** (Database Schema): No change — Alembic migrations work identically against local PostgreSQL.
- **All other stories:** No changes.

### Artifact Conflicts

| Artifact | Impact | Changes Applied |
|---|---|---|
| **Epics** | Story 4.2 rewritten; Epic 4 description updated | Title, user story, all ACs replaced; FR coverage map minor clarification |
| **Architecture** | Stack decisions updated; local deployment section added; project structure updated | Added "Local Development & Demo Deployment" section with service mapping table; deferred `infra/terraform/` |
| **PRD** | Deployment topology sentence updated | One sentence in Technical Architecture Considerations |
| **UX Design** | No impact | — |
| **Sprint Status** | Story key renamed | `4-2-aws-infrastructure-cicd-and-core-platform-services` → `4-2-local-infrastructure-with-docker-compose` |

### Technical Impact

- **Simplifies** Epic 4 significantly — no Terraform, no cloud provisioning, no AWS account setup
- **Provider-agnostic interfaces** preserved throughout — cloud migration is a config change, not a rewrite
- **Same Dockerfiles** will work in both Docker Compose (local) and ECS Fargate (future cloud)
- **Same S3 SDK** (boto3) works against both MinIO and AWS S3

---

## Section 3: Recommended Approach

**Selected path:** Direct Adjustment — modify Story 4.2 and add notes to Architecture and PRD.

**Rationale:**
- Story 4.2 is in backlog (unstarted) — zero rollback cost
- Local-first actually simplifies and accelerates development
- Provider-agnostic service interfaces preserve the cloud migration path
- No MVP features, FRs, or NFRs are affected — the system does the same thing, just hosted differently

**Effort estimate:** Low
**Risk level:** Low (reduces risk by removing cloud dependency)
**Timeline impact:** Positive (faster to set up Docker Compose than provision AWS)

---

## Section 4: Detailed Change Proposals

### Epics Changes (3 edits)

1. **Story 4.2 full rewrite** — title, user story, and all acceptance criteria replaced for Docker Compose local infrastructure
2. **Epic 4 description** — updated to reference Docker Compose instead of "real infrastructure with CI/CD"
3. **FR Coverage Map** — FR7 clarified as "local infra + RBAC middleware"

### Architecture Changes (4 edits)

1. **Stack Decisions** — database and cloud entries updated to show local/future split
2. **New section: "Local Development & Demo Deployment (MVP)"** — full service mapping table, docker-compose services, and cloud migration path
3. **Project Structure** — `infra/terraform/` deferred with README; `docker-compose.yml` added under `infra/docker/`
4. **Delivery Environments** — local deployment section added before day-zero prerequisites

### PRD Changes (1 edit)

1. **Deployment topology** — one sentence updated to reflect local-first with provider-agnostic interfaces

### Sprint Status Changes (1 edit)

1. **Story key renamed** — reflects new story title

---

## Section 5: Implementation Handoff

**Scope classification:** Minor — direct implementation by development team.

**Handoff:** Dev agent implements Story 4.2 as rewritten when Epic 4 begins. No other role changes needed.

**Success criteria:**
- `docker compose up` starts all services (PostgreSQL, MinIO, API, worker) and they are healthy within 30 seconds
- Alembic migrations run automatically on API start
- Pre-signed URLs work against MinIO for image upload
- RBAC middleware passes all existing auth tests
- Email service logs to console in local mode
- All provider interfaces are swappable via config for future cloud deployment

**Next steps:**
1. Run `/bmad-bmm-sprint-planning` to regenerate sprint plan with revised stories
2. Run `/bmad-bmm-create-story` to start Story 4.1 (Turborepo monorepo scaffold)
