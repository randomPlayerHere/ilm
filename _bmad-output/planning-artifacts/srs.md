
# Software Requirements Specification (SRS) - Teacher OS

## 1. Introduction

### 1.1 Purpose
This document defines the software requirements for Teacher OS, an AI-assisted K-12 platform for teachers, parents, students, principals/org managers, and platform admins. It is intended to guide implementation, testing, and release readiness.

### 1.2 Scope
Teacher OS provides:
- AI-assisted course generation and customization for teachers.
- Camera-based AI-assisted grading with teacher approval.
- Student progress analytics with simple trend and risk views.
- Teacher-parent messaging and configurable notifications.
- Basic org-level dashboard for school leadership.
- Role-based access and tenant isolation for school organizations.

### 1.3 Definitions and Acronyms
- AI: Artificial Intelligence.
- RBAC: Role-Based Access Control.
- MVP: Minimum Viable Product.
- NFR: Non-Functional Requirement.
- PII: Personally Identifiable Information.
- COPPA/FERPA: US student privacy/legal frameworks.

### 1.4 References
- PRD: `_bmad-output/planning-artifacts/prd.md`
- Architecture: `_bmad-output/planning-artifacts/architecture.md`
- Epics and Stories: `_bmad-output/planning-artifacts/epics-and-stories.md`
- UX Design Spec: `_bmad-output/planning-artifacts/ux-design-specification.md`
- Manual Test Plan: `_bmad-output/planning-artifacts/manual-test-plan.md`

## 2. Overall Description

### 2.1 Product Perspective
Teacher OS is a multi-role SaaS product with:
- FastAPI backend services.
- PostgreSQL data store.
- React Native apps for teacher/parent/student experiences.
- Web admin dashboard for org and platform administration.
- AWS-hosted infrastructure with S3 for assignment images and async processing for grading/notifications.

### 2.2 User Classes
- Teacher: Generates curriculum, grades submissions, tracks class/student performance, communicates with parents.
- Parent/Guardian: Monitors student growth, receives alerts, and communicates with teachers.
- Student: Views own progress and teacher-provided feedback.
- Principal/Org Manager: Monitors high-level cohort trends.
- Admin: Manages users, roles, and org membership.

### 2.3 Operating Environment
- Mobile: React Native app on modern iOS/Android versions supported by current React Native baseline.
- Web: Modern Chromium/Firefox/Safari browsers for admin console.
- Backend: Python FastAPI services deployed to AWS managed compute.
- Database: PostgreSQL on AWS RDS.
- Storage/Async: AWS S3 and SQS/EventBridge-equivalent job infrastructure.

### 2.4 Constraints
- Student privacy and access controls must satisfy COPPA/FERPA-aligned handling.
- No final grade visibility to parent/student before explicit teacher approval.
- Tenant/org boundary enforcement is mandatory across all data queries.
- MVP must prioritize reliability and explainability over full automation.

### 2.5 Assumptions and Dependencies
- Schools provide roster/class data directly or via integration.
- AI grading quality is sufficient for assisted workflows with mandatory teacher review.
- Notification channels (in-app/email) are available and configured.
- Seed/demo data exists in non-production for QA and demos.

## 3. External Interface Requirements

### 3.1 User Interfaces
- Teacher mobile screens: Dashboard, Curriculum Builder, Grading Camera/Review, Student Detail, Inbox.
- Parent mobile screens: Child Overview, Trends, Alerts, Message Thread.
- Student mobile screens: Basic progress view and feedback history.
- Principal/admin web screens: Org Overview, Basic cohort trends, User/Role Management.

### 3.2 Software Interfaces
- Authentication: `/auth/*`
- Courses: `/courses/*`
- Grading: `/grading/*`
- Students analytics: `/students/*`
- Messaging: `/messages/*`
- Notifications: `/notifications/*`
- Org analytics: `/org-analytics/*`

### 3.3 Data Interfaces
- Relational tables for users, students, classes, enrollments, assignments, submissions, grades, risk signals, messages, notifications.
- Object storage for uploaded assignment images.
- Audit log stream for grade approvals/edits and role changes.

### 3.4 Communication Interfaces
- HTTPS/TLS 1.2+ for all client-server traffic.
- Signed URL workflow for direct secure image upload/download.
- Async messaging for grading and notification jobs.

## 4. System Features and Functional Requirements

### 4.1 Identity and Access
- FR-001: The system shall support email/password registration and login for all supported roles.
- FR-002: The system shall store password credentials only as secure hashes.
- FR-003: The system shall implement RBAC for teacher, parent, student, principal/org manager, and admin.
- FR-004: The system shall enforce tenant/org data isolation on every protected query and mutation.
- FR-005: The system shall return authorization failures without exposing sensitive data.

### 4.2 Course Creation and Customization
- FR-006: The system shall allow a teacher to request AI-generated lesson/unit drafts.
- FR-007: The system shall include objectives, activities, and assessment outline in generated drafts.
- FR-008: The system shall allow teacher edits for pacing/objectives/assessment criteria.
- FR-009: The system shall support state-standard profile selection and persist selection per class/course.
- FR-010: The system shall maintain version history for saved curriculum revisions.
- FR-011: The system shall allow teachers to publish/unpublish lesson plans with audit metadata.

### 4.3 Camera-Based AI Grading
- FR-012: The system shall allow teachers to capture and upload assignment images from mobile app.
- FR-013: The system shall upload artifacts through signed URLs with restricted object permissions.
- FR-014: The system shall generate AI-proposed score, rubric rationale, and confidence indicator.
- FR-015: The system shall flag low-confidence outputs for additional teacher review.
- FR-016: The system shall allow teachers to edit AI-proposed grades and feedback before approval.
- FR-017: The system shall not expose final grades to parent/student until teacher approval is completed.
- FR-018: The system shall store AI model/version metadata for grading traceability.
- FR-019: The system shall create immutable grade version entries on approval.

### 4.4 Student and Parent Analytics
- FR-020: The system shall provide student historical performance timeline with filters.
- FR-021: The system shall compute and expose simple trend metrics.
- FR-022: The system shall display risk level with human-readable explanation text.
- FR-023: The system shall provide parent dashboard cards for growth and risk.
- FR-024: The system shall restrict parent access to linked students only.
- FR-025: The system shall provide default valid responses for empty/new student states.

### 4.5 Messaging and Notifications
- FR-026: The system shall provide threaded teacher-parent messaging.
- FR-027: The system shall allow messages to link to assignment or analytics context.
- FR-028: The system shall track thread/message read state and timestamps.
- FR-029: The system shall allow users to configure notification cadence (instant/daily/weekly).
- FR-030: The system shall support in-app and email notification delivery channels.
- FR-031: The system shall generate parent weekly digest including highlights and flagged risks.
- FR-032: The system shall log notification delivery success/failure outcomes.

### 4.6 Org-Level Analytics
- FR-033: The system shall provide cohort summary analytics by grade and subject.
- FR-034: The system shall allow principal/org manager filtering by grade/class/teacher.
- FR-035: The system shall provide basic communication metrics including unread thread counts.
- FR-036: The system shall prevent exposure of student-level PII in default org aggregate views.
- FR-037: The system shall support CSV export as an optional post-MVP enhancement.

### 4.7 Administration
- FR-038: The system shall allow admins to manage users, roles, and org membership.
- FR-039: The system shall allow basic safety/content configuration.
- FR-040: The system shall log sensitive admin actions in an auditable format.

## 5. Data Requirements

### 5.1 Core Entities
- User, Student, Guardian, Teacher, Class, Enrollment, Course, Assignment, Submission, Grade, RiskSignal, Message, Notification.

### 5.2 Data Integrity Rules
- DR-001: Every student, teacher, and class record shall belong to one organization tenant.
- DR-002: Submission records shall reference valid assignment and student IDs.
- DR-003: Grade records shall reference one submission and preserve historical approved versions.
- DR-004: Message threads shall enforce participant membership and linked student context permissions.
- DR-005: Notification preferences shall resolve per user per channel and cadence.

### 5.3 Retention and Audit
- DR-006: Grade approvals/edits and role changes shall be audit logged with actor and timestamp.
- DR-007: Data export/deletion behavior shall be defined per legal and school policy.

## 6. Non-Functional Requirements

### 6.1 Performance
- NFR-001: API p95 latency for student and org read endpoints shall be <= 700 ms under expected school-hour load.
- NFR-002: API p95 latency for grading/messaging write endpoints shall be <= 1200 ms excluding async AI job duration.
- NFR-003: Dashboard initial load p95 shall be <= 3.0 seconds on broadband-equivalent conditions.

### 6.2 Reliability
- NFR-004: Monthly service availability target shall be >= 99.0% for MVP.
- NFR-005: Background grading/notification job success rate shall be >= 98.0%.
- NFR-006: Disaster recovery targets shall meet RPO <= 60 minutes and RTO <= 4 hours.

### 6.3 Scalability
- NFR-007: MVP baseline shall support at least 2,000 active students per organization.
- NFR-008: MVP baseline shall support at least 100 concurrent active users per organization.
- NFR-009: Upload pipeline shall support at least 15 assignment image uploads per minute per organization.

### 6.4 Security and Privacy
- NFR-010: All traffic shall use TLS 1.2+.
- NFR-011: JWT access token lifetime shall be <= 60 minutes, with revocable refresh tokens.
- NFR-012: Password hashing shall use Argon2id or bcrypt with environment-appropriate cost.
- NFR-013: Access control checks shall be enforced server-side for all protected endpoints.
- NFR-014: Student data handling shall align with COPPA/FERPA expectations and organizational policy.

### 6.5 Observability
- NFR-015: API and worker logs shall be structured and include request correlation IDs.
- NFR-016: Alerts shall exist for 5xx error rates and job failures.
- NFR-017: Weekly reliability review shall track incidents and key latency trends.

### 6.6 Usability and Accessibility
- NFR-018: UX shall remain role-focused and minimize navigation complexity per role.
- NFR-019: Parent risk status shall be discoverable from dashboard within 30 seconds in usability tests.
- NFR-020: Teacher shall complete grading review cycle in under 2 minutes per submission for typical submissions.
- NFR-021: Primary user flows shall meet WCAG 2.x AA accessibility baseline.

## 7. Compliance Requirements
- CR-001: Student privacy controls shall satisfy COPPA/FERPA-aligned requirements for access, disclosure, and parental control.
- CR-002: Auditability shall be available for grade changes, role changes, and sensitive access.
- CR-003: Data minimization principles shall apply to student and guardian PII collection and exposure.

## 8. Verification and Acceptance

### 8.1 Test Strategy
Verification shall include unit tests, integration tests, API contract tests, RBAC/security tests, and manual scenario validation for P0 and P1 workflows.

### 8.2 MVP Acceptance Conditions
- AC-001: All P0 manual test scenarios pass.
- AC-002: No open Sev-1/Sev-2 defects remain.
- AC-003: RBAC and tenant boundary tests pass for all roles.
- AC-004: Core NFR targets are met in staging benchmark runs.

## 9. Requirements Traceability (Summary)

| Requirement Area | Primary Epic Mapping |
|---|---|
| Identity and Access (FR-001..005) | Epic 1 |
| Course Creation (FR-006..011) | Epic 2 |
| AI Grading (FR-012..019) | Epic 3 |
| Student/Parent Analytics (FR-020..025) | Epic 4 |
| Messaging/Notifications (FR-026..032) | Epic 5 |
| Org Analytics (FR-033..037) | Epic 6 |
| Admin Controls (FR-038..040) | Epic 1, Epic 6 |
| Non-Functional Requirements (NFR-001..021) | Architecture + all epics |

## 10. Open Items
- OI-001: Final decision on deployment compute flavor (ECS/Fargate vs App Runner) for MVP.
- OI-002: Decide whether Google Classroom integration is included in MVP or deferred.
- OI-003: Final retention durations and legal review outcome for student artifacts and logs.
- OI-004: Final quality thresholds for AI grading confidence by assignment type.
