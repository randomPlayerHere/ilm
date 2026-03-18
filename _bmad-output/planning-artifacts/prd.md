---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-02b-vision', 'step-02c-executive-summary', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-01b-continue', 'step-01b-continue', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish', 'step-11-complete', 'step-12-complete', 'step-e-01-discovery', 'step-e-02-review', 'step-e-03-edit']
date: '2025-03-01'
lastEdited: '2026-03-19'
editHistory:
  - date: '2026-03-19'
    changes: 'Reframed product as mobile-centric (React Native) with companion web interface. Updated Executive Summary, Product Scope, Technical Architecture, User Journeys, Functional Requirements preamble, Non-Functional Requirements, and Project Scoping to explicitly define a fully usable mobile application as the primary deliverable.'
inputDocuments: ['_bmad-output/planning-artifacts/product-brief-ilm-2025-03-01.md', '_bmad-output/brainstorming/brainstorming-session-2025-03-01.md']
workflowType: 'prd'
classification:
  projectType: saas_b2b
  domain: edtech
  complexity: medium
  projectContext: greenfield
---

# Product Requirements Document - Teacher OS

**Author:** elephant
**Date:** 2025-03-01

---

## Executive Summary

**Teacher OS** is a mobile-centric AI-driven K-12 education application built around one question: *"Is my child improving?"* It delivers a React Native mobile app as the primary interface for teachers (grading and planning), parents (transparency and benchmarks), and students (growth and "level up" experience), with a companion web interface for principals/org managers (cohort-level insight) and administrators. The product addresses overloaded teacher-parent communication, lack of clear progress answers, and tools that show grades and attendance but not *why* or *how* students are improving. Target users are K-12 schools, districts, tutoring centers, and families; the platform supports the full spectrum of learners, including special needs and gifted.

### What Makes This Special

The product is explicitly designed to answer *"Is my child improving?"* with transparency (scores + explanations + strengths/weaknesses + longitudinal view), not just grade display. Teachers use the app to photograph student work and get AI-assisted grading; parents and students get self-serve access so they're not blocked on teacher availability. Differentiators: AI-assisted grading from photos; self-serve parent and student dashboards; full-spectrum equity (accommodations and enrichment); and a portable student record/portfolio. Core insight: parent–teacher communication works when it delivers that answer via transparency and self-serve access—not only scores and notifications. The product is delivered as a mobile-first application (React Native) so teachers can grade from anywhere with their phone camera, parents check progress on the go, and students engage with growth views on their own devices. A companion web interface serves administrative and organizational oversight needs.

## Project Classification

| Field | Value |
|-------|--------|
| **Project type** | SaaS B2B platform |
| **Domain** | EdTech (K–12) |
| **Complexity** | Medium (student privacy COPPA/FERPA, accessibility, content moderation, curriculum alignment) |
| **Project context** | Greenfield |

---

## Success Criteria

### User Success

- **Parent:** Can answer "Is my child improving?" without contacting the teacher; configures and uses notifications (daily/weekly/monthly or dashboard-only) without overload.
- **Teacher:** Saves time on parent communication (fewer calls and "what's my grade?" emails); uses in-app messaging with acceptable response/resolution; parents are informed without teacher as sole bottleneck.
- **Student:** Engages with growth / "level up" view; can articulate where they need to improve; experiences product as "helping me win" rather than surveillance.
- **Principal / org:** Uses cohort-level data to inform hiring, PD, or curriculum; can spot school-wide or org-wide trends before they become crises.

### Business Success

- **Adoption:** Schools, districts, or tutoring centers onboard; teachers and parents actively use the product (e.g. % of parents viewing dashboard at least monthly).
- **Retention:** Sustained use of dashboards, messaging, and AI grading; reduced churn after initial rollout.
- **Satisfaction:** NPS or satisfaction scores by role (parent, teacher) indicate the product delivers on "Is my child improving?"
- **Efficiency:** Measurable reduction in parent–teacher contact volume for grade/progress questions (calls, emails, tickets) where the product is used.

### Technical Success

- **Reliability:** Platform available when schools need it (uptime targets appropriate for school hours and reporting).
- **Performance:** Dashboard and messaging responsive; AI grading completes within acceptable time so teacher workflow is viable.
- **Privacy & compliance:** Student data handled per COPPA/FERPA and stated privacy policy; access controls and data use documented.
- **Integrations:** Google Classroom (and any other MVP integrations) work reliably for sync and sign-in.

### Measurable Outcomes

- % of parents who view the parent dashboard at least once per month.
- Parent–teacher message volume and average response/resolution time.
- Teacher-reported or system-measured time saved on parent communication (e.g. before/after or survey).
- Student engagement with student-facing growth/level-up view (e.g. return visits, time in student dashboard).
- Principal/org manager use of cohort/school-wide views for at least one decision (hiring, PD, curriculum, or intervention).
- NPS or satisfaction by stakeholder (parent, teacher) within target range.

## Product Scope

### MVP – Minimum Viable Product

- **Parent–teacher communication core:** Score transparency (scores + why), in-app bidirectional messaging (1:1 and small groups), configurable notifications (and/or dashboard-only).
- **"Is my child improving?" basics:** Longitudinal view of key data (e.g. scores, assignments), simple benchmarking (e.g. class-level), strengths/weaknesses view, consistency (attendance, HW, exams) where feasible.
- **AI grading:** Teacher captures work in-app (e.g. photo); AI assists grading; teacher reviews/approves; optional auto-generated practice for weak areas.
- **Self-serve access:** Parent and student dashboards so they can see progress without going through the teacher every time.
- **Course/curriculum:** Dynamic curriculum and lesson/assessment planning; teacher chat to create generic and student-specific plans using student data.
- **Mobile application (primary):** React Native mobile app delivering all teacher, parent, and student workflows as usable mobile screens with native device capabilities (camera for assignment capture, push notifications).
- **Companion web interface:** Browser-based interface for principal/org manager dashboards and admin management workflows.
- **Platform baseline:** Auth (email/password + Google sign-in), role-based access; mobile app as primary delivery surface for teacher, parent, and student roles; companion web interface for admin and principal/org manager roles; global admin for users, roles, orgs, content, and safety controls.

### Growth (Post-MVP)

- Principal/org dashboard: cohort-level metrics, resource-allocation insights, special needs and gifted support.
- Student experience: avatar tutor, "level up" framing, safe AI mode (vetted prompts/responses).
- Ecosystem: Google Classroom integration, internal community for teachers/parents.
- Deeper differentiation: comparative benchmarking (class → state → country), portable student portfolio, richer notifications and digest options.

### Vision (Future)

- Real-time parent view of in-class work; AI feedback on every assignment; async comms (e.g. voice/video).
- Full-spectrum equity: accommodations, IEP alignment, enrichment paths.
- Risk mitigations: role-based access, configurable notification cadence, student visibility controls, offline/low-bandwidth options where valuable.

---

## User Journeys

### 1. Teacher — Maria (6th grade math)

**Opening:** Maria has 28 students. She spends hours grading and answering parent emails and calls ("What did my child get?" "Why that grade?"). She's behind on planning and feels like a bottleneck.

**Rising action:** She opens the Teacher OS app on her phone, links her class, and starts using the in-app camera to photograph homework and tests. The AI suggests scores and feedback; she adjusts and approves. She creates a generic lesson plan via teacher chat ("6th grade math, struggles with multiplication") and a student-specific plan for a struggling student, with his data pulled in. She sends a short in-app message to a parent, linked to that student and assignment.

**Climax:** A parent messages asking why their child got a B. Instead of writing a long email, Maria points them to the dashboard: scores, rubric, and AI explanation are already there. The parent replies: "I see it now. Thanks." Fewer calls and emails; grading and planning feel manageable.

**Resolution:** Maria uses the platform for grading, planning, and messaging. She feels in control; parent conversations focus on next steps, not "what happened."

### 2. Parent — James (father of a 6th grader)

**Opening:** James worries about his daughter but doesn't know how she's really doing. He doesn't want to bug the teacher; report cards feel too late and too vague.

**Rising action:** He signs in with Google on the mobile app and sees his daughter's recent scores with short explanations ("Struggled on multi-step word problems; strong on computation"). He turns on a weekly digest and gets a notification when a test grade is posted. He checks the longitudinal view and sees an upward trend in math. He sends the teacher one in-app message to ask about extra practice.

**Climax:** He realizes he can answer "Is she improving?" himself. He feels informed and less anxious; when he talks to his daughter, he can be specific ("Your teacher said to focus on word problems—want to try a few together?").

**Resolution:** He uses the dashboard and digest regularly. He only messages the teacher when he needs something the dashboard can't give. He feels like a partner, not a nag.

### 3. Student — Sam (6th grader)

**Opening:** Sam finds grades stressful and doesn't really know what to work on. It feels like the adults are talking about him, not with him.

**Rising action:** He opens the app and sees his progress in a "level up" style: growth over time, strengths, and one or two clear areas to improve. He gets "secret tips" (e.g. hints or practice suggestions) tied to his weak spots. He sees his own improvement trail and feels proud.

**Climax:** He uses a tip before the next quiz and does better. He tells his dad, "I knew what to practice." He feels the app is on his side.

**Resolution:** He checks his growth view and tips regularly. He can say what he's good at and what he's working on. He feels more ownership of his learning.

### 4. Principal / Org manager — Dr. Chen (K–8 principal)

**Opening:** Dr. Chen has to decide where to put limited PD and hiring. She gets anecdotes and spreadsheets, not a clear picture of where the school struggles.

**Rising action:** She opens the companion web interface and sees cohort metrics: e.g. "Most students weak in fractions in 5th–6th grade" and trends over time. She filters by grade and subject, sees which teachers have the heaviest parent-message load, and reviews summary engagement (e.g. parent dashboard use). She spots a pattern before it becomes a crisis.

**Climax:** She uses the data in a staffing meeting: "We need to strengthen math in 5th–6th. Here's the evidence." She approves a PD focus and a hire with confidence.

**Resolution:** She uses the dashboard for staffing, PD, and curriculum decisions. She feels data-informed instead of guess-driven.

### 5. Global admin — Alex (platform/org admin)

**Opening:** Alex needs to onboard schools, manage roles (teachers, parents, students, principals), keep content and safety settings correct, and fix access issues.

**Rising action:** Alex logs into the admin web interface, creates an org and invites users, assigns roles (teacher, parent, student, principal), and configures safety and content policies. When a parent can't see their child, Alex checks role and org membership and fixes the link. Alex audits who has access to what and adjusts as needed.

**Climax:** A new school goes live in a day: org created, users invited, roles set. A reported issue is resolved by correcting one permission.

**Resolution:** Alex uses the admin dashboard for user/org/role management, content, and safety. Onboarding and support are under control.

### Journey Requirements Summary

| Journey | Capabilities revealed |
|--------|------------------------|
| Teacher | In-app capture and AI-assisted grading; teacher chat (generic + student-specific plans); in-app messaging tied to student/assignment; score transparency so parents can self-serve. |
| Parent | Parent dashboard (scores, explanations, longitudinal view, strengths/weaknesses); configurable notifications/digest; in-app messaging; self-serve answer to "Is my child improving?" |
| Student | Student dashboard with growth/"level up" view; strengths/weaknesses and tips; improvement trail; sense of agency, not surveillance. |
| Principal/Org | Org-level dashboard; cohort metrics (grade, subject, trend); resource/PD/hiring insight; overview of engagement and messaging. |
| Global admin | User/org/role management; safety and content controls; audit and support (e.g. access and permissions). |

---

## Domain-Specific Requirements

### Compliance & Regulatory

- **Student privacy (COPPA/FERPA):** Collect, store, and share only what's necessary; obtain parent consent where required (e.g. under-13); document data access and sharing so schools can meet FERPA.
- **Accessibility:** Meet WCAG 2.x (Level AA as baseline) for dashboards and key flows so teachers, parents, and students with disabilities can use the product.
- **Content moderation:** Define rules for user-generated content (e.g. internal community, messages); review and moderation path for reported content; age-appropriate and safe AI use (e.g. safe AI mode).
- **Curriculum alignment:** Support alignment to learning/curriculum standards where needed (e.g. for plans and assessments); document how content maps to standards if claimed.

### Technical Constraints

- **Security:** Role-based access; least-privilege; encryption in transit and at rest for student/parent data; audit trail for sensitive actions (e.g. access to student data, admin changes).
- **Privacy:** Clear data handling and retention; parent/guardian controls where required; no use of student data for non-educational purposes without consent; portable/exportable student data.
- **Availability:** Uptime and support aligned to school hours and reporting periods; planned maintenance communicated to orgs.

### Integration Requirements

- **Google Classroom (MVP):** Reliable sync for classes, roster, and assignments where used; Google sign-in for users; clear scope of what is synced and how often.
- **Future:** Document interfaces for any other SIS/LMS or assessment systems so integrations stay consistent with privacy and security.

### Risk Mitigations

- **Privacy/data exposure:** Strict RBAC; no parent access to other students' data; secure, context-aware messaging.
- **Overload/misuse:** Configurable notification cadence; student visibility controls to reduce surveillance anxiety; documented data-use and safety policies.
- **Inequality/access:** Consider accessibility, device diversity, and optional offline/low-bandwidth patterns where they add meaningful access.

---

## Innovation & Novel Patterns

### Detected Innovation Areas

- **AI-assisted grading from photos:** Teacher captures work in-app; AI suggests scores and feedback; teacher reviews/approves. Reduces grading load and supports consistent, explainable feedback.
- **AI-driven lesson and plan creation:** Teacher chat produces generic plans (e.g. "6th grade math, struggles with multiplication") and student-specific plans using that student's data. Combines workflow automation with an AI-agent style interface.
- **"Is my child improving?" as product center:** Product and UX are built around answering that question (transparency, longitudinal view, self-serve) instead of only storing grades. Shifts parent–teacher communication from reactive to proactive and self-serve.
- **Self-serve parent and student access:** Parents and students get dashboards and explanations without the teacher as gatekeeper. Changes the usual "teacher as sole source of truth" pattern.

### Market Context & Competitive Landscape

- Many EdTech tools focus on gradebooks, LMS, or parent portals; few combine **photo-based AI grading**, **generative lesson/plan support**, and **explicit "improvement over time"** in one product.
- Differentiation: workflow automation (grading, notifications) + AI agents (grading, plans, explanations) in a single K–12 workflow, with design centered on one question.

### Validation Approach

- **Pilots:** Schools or teachers use AI grading and teacher chat; measure time saved, plan quality, and teacher/parent satisfaction.
- **Success metrics:** Adoption of AI grading and plans; parent dashboard usage and "can answer without contacting teacher"; NPS/satisfaction by role.
- **Fallback:** If AI grading or plan quality is weak, keep human-in-the-loop (teacher always reviews/edits) and improve prompts and models before scaling.

### Risk Mitigation (Innovation)

- **AI quality/trust:** Teacher always reviews and approves AI output; explainability (e.g. "why this score") to build trust.
- **Over-reliance on AI:** Design so core value still works if AI is reduced (e.g. manual grading + transparency + messaging).
- **Privacy:** No use of student data for non-educational AI training; clear data-use and consent.

---

## SaaS B2B Specific Requirements

### Project-Type Overview

Teacher OS is a multi-role B2B SaaS platform for educational organizations (schools, districts, tutoring centers) with strict tenant isolation, role-based access control, auditable sensitive actions, and compliance-first handling of student data. The architecture must support organization-scoped workflows across curriculum, grading, analytics, and messaging.

### Technical Architecture Considerations

The system delivers a **React Native mobile application** as the primary client for teachers, parents, and students, and a **companion web interface** for principals/org managers and administrators. Both clients communicate with a shared backend API layer. The backend uses AWS-hosted PostgreSQL (RDS) and must enforce tenant/org isolation on every protected query. Current requirements strongly imply a shared-database architecture with strict organization scoping at the application and query layers, while preserving the option to evolve to stronger physical isolation if enterprise requirements demand it.

Core architecture constraints:
- Every core record is tenant-owned (`org_id`) per SRS DR-001.
- Tenant isolation is mandatory for all protected access paths per SRS FR-004.
- Sensitive workloads (e.g., AI grading jobs) can run asynchronously but must preserve org-scoped data boundaries.
- Auditability is required for sensitive mutations and accesses.
- Mobile app (React Native) is the primary delivery surface; companion web interface serves admin and org-level oversight roles.
- Backend exposes a well-defined API consumed by both mobile and web clients.

### Tenant Model

- Baseline model: single PostgreSQL cluster with strict logical multi-tenancy using `org_id` on all core domain records.
- Enforcement model:
  - All protected queries must include organization scope checks.
  - Service-layer authorization must validate actor role + org membership before data access.
  - Cross-tenant data access is prohibited by default.
- Future-proofing requirement:
  - Architecture should allow migration path to higher-isolation enterprise patterns (e.g., schema-per-tenant or database-per-tenant) if contractual needs evolve.

### RBAC Matrix

Defined launch roles and permissions:

- Admin
  - Manage users, roles, org memberships.
  - Configure baseline safety/content controls.
  - Perform tenant-scoped administrative actions with audit logs.
- Principal / Org Manager
  - View cohort-level trends by grade/subject.
  - Use filters for organizational oversight.
  - Default views must not expose student-level PII.
- Teacher
  - Create/edit AI-assisted curriculum outputs.
  - Capture assignments and run AI-assisted grading workflows.
  - Final approval required before grades/feedback become visible.
  - View class/student analytics within authorized scope.
  - Message linked parents/guardians.
- Parent/Guardian
  - View growth/risk dashboards and alerts for linked students only.
  - Message relevant teachers.
- Student
  - View own progress and teacher-approved feedback only.

### Subscription Tiers

Current state: **not defined in source artifacts**.

Requirement:
- Product must define launch packaging for at least:
  - School plan
  - District plan
  - Tutoring-center plan
- Tier definition must specify:
  - Feature gates (org analytics depth, admin controls, integration availability, support level)
  - Usage/volume constraints (students, staff, org units)
  - Contract and onboarding model
- Until defined, pricing/packaging remains a delivery risk and go-to-market blocker.

### Integration List

MVP integration stance:
- Google Classroom: explicitly unresolved (SRS OI-002); decision required whether MVP or post-MVP.
- AWS platform dependencies (required infrastructure components):
  - RDS PostgreSQL (system of record)
  - S3 (image/object storage)
  - SQS/EventBridge (async processing/events)
- State standards profiles:
  - Must be available for teacher selection; implementation may start as seeded/internal data if live API integration is not required in MVP.

Non-MVP / not currently specified:
- Clever/ClassLink/SIS/LMS ecosystem integrations are not required by current documents and should be treated as later-phase candidates.

### Compliance Requirements

Day-1 compliance and governance requirements:
- COPPA/FERPA-aligned handling of student/guardian data.
- Data minimization in collection, storage, and exposure paths.
- Auditable logs for:
  - Grade changes
  - Role/permission changes
  - Sensitive data access events

Explicitly not yet required by current artifacts:
- SOC 2
- SSO/SAML
- Jurisdiction-specific data residency beyond current AWS hosting assumptions

### Implementation Considerations

- Treat subscription tier definition and Google Classroom MVP decision as top open decisions before implementation planning finalization.
- Implement tenant-isolation safeguards as non-optional acceptance criteria in all protected endpoints and queries.
- Validate principal/org dashboards for privacy-safe aggregation (no default student PII leakage).
- Ensure grade publication workflow enforces teacher final approval as a hard gate.

---

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:** Problem-solving + platform trust MVP
Focus on one undeniable outcome: parents and teachers can reliably answer "Is this student improving?" with teacher-approved, privacy-safe data.

**Resource Requirements:**
- Product/Delivery: 1 PM, 1 designer (fractional acceptable), 1 EM/tech lead
- Engineering: 2-3 React Native mobile engineers, 1-2 backend/API engineers, 1 ML engineer (or ML-capable backend), 1 QA/SDET
- Web: 1 frontend engineer for companion web interface (admin/principal)
- Platform/Security: shared ownership with tech lead + backend engineer
- Total lean team: ~6-9 contributors

### MVP Feature Set (Phase 1)

**Core User Journeys Supported:**
- Teacher captures assignment, AI suggests grading, teacher approves.
- Parent views linked-student progress + explanation and messages teacher.
- Student sees own progress + approved feedback.
- Principal/org manager views privacy-safe cohort trends (no default student PII).
- Admin manages users/roles/org memberships and safety baseline settings.

**Must-Have Capabilities:**
- Strict tenant isolation (`org_id` enforcement on protected queries).
- RBAC for Admin, Principal/Org Manager, Teacher, Parent/Guardian, Student.
- Teacher final-approval gate before grade/feedback visibility.
- Parent/student self-serve dashboards for progress transparency.
- In-app teacher-parent messaging tied to student context.
- Core progress trend view answering "Is my child improving?"
- Audit logging for grade changes, role changes, sensitive access.
- COPPA/FERPA-aligned data handling and minimization.
- AWS baseline platform (RDS, S3, async jobs).
- React Native mobile app delivering all teacher, parent, and student workflows as complete, usable screens.
- Companion web interface for admin management and principal/org-level dashboards.
- Shared backend API layer serving both mobile and web clients.

### Post-MVP Features

**Phase 2 (Growth):**
- Comparative benchmarking (class/district/state) where data quality supports it.
- Stronger diagnostics (strength/weakness decomposition, consistency signals).
- Improved notification controls and digest intelligence.
- Google Classroom integration (if deferred from MVP).
- Enhanced principal insights for staffing/PD decisions.
- Early subscription packaging rollout (school/district/tutoring-center tiers).

**Phase 3 (Expansion):**
- Portable student portfolio/shareable records.
- Rich student "level up" experiences and deeper AI coaching.
- Additional LMS/SIS integrations (e.g., Clever/ClassLink candidates).
- Enterprise isolation options (schema-per-tenant / db-per-tenant path).
- Advanced analytics and intervention recommendation engine.

### Risk Mitigation Strategy

**Technical Risks:**
- Risk: AI grading quality, tenant leaks, role-permission errors.
- Mitigation: teacher-in-the-loop approval, strict authz checks on every protected access path, audit trails, staged rollout by org.

**Market Risks:**
- Risk: product becomes "monitoring only" instead of improvement engine.
- Mitigation: define adoption + learning-outcome KPIs early; pilot with explicit before/after measures (teacher time saved, parent clarity, student improvement trend).

**Resource Risks:**
- Risk: team capacity spread too thin across AI + platform + compliance.
- Mitigation: cut MVP to must-haves, defer gamification/advanced benchmarks/nonessential integrations, launch with one strong workflow and expand.

---

## Functional Requirements

All functional requirements below describe user-facing capabilities delivered through the **React Native mobile application** (teacher, parent, student roles) or the **companion web interface** (principal/org manager, admin roles), backed by a shared API layer. Each FR represents a complete, usable feature — not just an API endpoint.

### Identity, Access, and Tenant Administration

- FR1: Users can sign in using email/password credentials.
- FR2: Users can sign in using Google sign-in.
- FR3: Admins can create and manage organizations.
- FR4: Admins can invite, activate, and deactivate users.
- FR5: Admins can assign and update user roles.
- FR6: Admins can manage user-to-organization memberships.
- FR7: The system can enforce organization-scoped access for protected data and actions.
- FR8: The system can prevent cross-tenant data access by default.
- FR9: Admins can configure baseline safety and content controls.

### Teacher Instruction and Assessment Workflow

- FR10: Teachers can generate draft lesson and curriculum content with AI assistance.
- FR11: Teachers can edit and refine AI-generated instructional content before use.
- FR12: Teachers can create student-specific instructional plans informed by student performance context.
- FR13: Teachers can capture student assignment artifacts in-platform (including image upload/capture).
- FR14: Teachers can receive AI-assisted grading suggestions for submitted/captured work.
- FR15: Teachers can review and modify AI-assisted grading outputs before finalization.
- FR16: Teachers can approve final grades and feedback for publication.
- FR17: The system can block grade/feedback visibility until teacher approval is completed.
- FR18: Teachers can generate follow-up practice recommendations based on identified weak areas.

### Parent and Student Progress Transparency

- FR19: Parents/guardians can view progress dashboards for linked students only.
- FR20: Students can view their own progress dashboards.
- FR21: Parents and students can view assessment outcomes with explanatory context (not just scores).
- FR22: Parents and students can view longitudinal progress trends over time.
- FR23: Parents and students can view strengths and weakness indicators by subject/topic.
- FR24: Parents can configure update preferences (including digest-style and event-driven updates).
- FR25: Parents can access progress information through self-serve workflows without teacher mediation.
- FR26: Students can view teacher-approved feedback and next-step guidance.

### Communication and Engagement

- FR27: Teachers and parents can exchange in-app messages.
- FR28: Teachers and parents can send in-app messages linked to a specific student and, when applicable, a specific assignment or class activity.
- FR29: Parents can receive platform updates/alerts related to linked-student progress events.
- FR30: Users can configure notification preferences by event type and cadence (instant, daily digest, weekly digest, off), and the system shall apply changes within 60 seconds.

### School and Organization Oversight

- FR31: Principals/org managers can view cohort-level performance trends by grade and subject.
- FR32: Principals/org managers can apply filters to analyze organizational performance segments.
- FR33: Principal/org-manager default analytics views can exclude student-level PII.
- FR34: Principals/org managers can access organizational engagement indicators for parent-teacher interaction health.

### Compliance, Governance, and Safety

- FR35: The system can maintain auditable logs for grade changes.
- FR36: The system can maintain auditable logs for role and permission changes.
- FR37: The system can maintain auditable logs for sensitive data access events.
- FR38: The system can support COPPA/FERPA-aligned access and disclosure controls.
- FR39: The system can enforce data minimization in collection and exposure workflows.
- FR40: The system can enforce role-based permissions for all protected capabilities.

### Integration and Platform Operations

- FR41: The system can store and retrieve assignment artifacts and related media assets.
- FR42: The system can process asynchronous grading/analytics-related jobs.
- FR43: Admins can configure organization-level standards-aligned instructional profiles, including profile name, standards framework, effective date, and active/inactive status, with all changes captured in audit logs.
- FR44: The system can integrate with Google Classroom when enabled by product scope decisions.
- FR45: The system can provide baseline operational administration capabilities for multi-organization deployment.

---

## Non-Functional Requirements

### Performance

- NFR1: 95% of authenticated screen loads in the mobile app (teacher, parent, student) and companion web interface (principal, admin) must complete within 2.0 seconds under normal operating load.
- NFR2: 95% of core interactive actions (open student profile, open class analytics, open message thread) must complete within 1.5 seconds under normal load.
- NFR3: 95% of teacher message send actions must complete within 1.0 second, excluding downstream notification delivery latency.
- NFR4: 95% of AI grading job submissions must acknowledge receipt within 3 seconds.
- NFR5: 90% of AI grading jobs for single assignment submissions must produce reviewable output within 60 seconds.

### Security and Privacy

- NFR6: 100% of protected data in transit must use TLS 1.2+ as verified by automated monthly TLS endpoint scans and zero allowed critical TLS findings.
- NFR7: 100% of protected data at rest must be encrypted with managed keys as verified by quarterly storage encryption audits across all production data stores.
- NFR8: 100% of protected data-access requests must enforce tenant isolation checks, and cross-tenant read/write attempts must fail closed in automated authorization tests and production monitoring.
- NFR9: 100% of protected server-side operations must perform role-based authorization checks, validated by automated integration tests in CI on every release.
- NFR10: The system must record immutable audit events for grade changes, role changes, and sensitive data-access events within 30 seconds of the triggering action.
- NFR11: The system must enforce data minimization so no non-required student/guardian fields are collected in MVP workflows, as verified by quarterly privacy data-inventory reviews.
- NFR12: The platform must provide COPPA/FERPA-aligned parental access, correction, and disclosure-request workflows with request completion within 30 calendar days and auditable request logs.

### Reliability and Availability

- NFR13: Monthly service availability for core teacher/parent/student workflows must be at least 99.5%, excluding scheduled maintenance windows.
- NFR14: No single infrastructure failure may cause loss of committed grade records or approved feedback.
- NFR15: At least 99% of failed critical asynchronous jobs (grading pipeline and notification dispatch) must be retried within 5 minutes and processed idempotently with zero duplicate side effects.
- NFR16: Backup and restore procedures must support restoration of core production data within 4 hours for high-severity incidents.

### Scalability

- NFR17: The architecture must support at least 10x growth from initial pilot volume without full re-architecture of core services.
- NFR18: The platform must horizontally scale stateless application services and async workers to sustain 10x pilot baseline throughput with no more than 20% p95 latency degradation during quarterly load tests.
- NFR19: Data-access patterns must remain tenant-safe under load, with zero confirmed cross-tenant data exposure incidents in stress tests and production monitoring.

### Accessibility

- NFR20: All MVP workflows across mobile app and companion web interface must conform to WCAG 2.1 Level AA, validated by automated accessibility scans and manual accessibility audit before each production release.
- NFR21: Core user journeys on the companion web interface (admin user management, principal dashboards) must be fully keyboard accessible. Mobile app journeys must follow platform accessibility guidelines (iOS/Android).
- NFR22: 100% of production UI screens across mobile app and companion web interface in MVP scope must pass WCAG 2.1 AA checks for color contrast, focus indicators, and semantic labeling in release-gate accessibility audits.

### Integration and Interoperability

- NFR23: External integration failures (e.g., Google Classroom when enabled) must not block core in-app grading, progress viewing, or messaging workflows.
- NFR24: Integration sync operations must emit structured logs (request_id, tenant_id, connector_id, status, error_code) and trigger failure alerts within 5 minutes of repeated sync failure conditions.
- NFR25: All integration contracts must be versioned, and connector updates must pass backward-compatibility contract tests for at least one prior supported version before release.

### Observability and Operations

- NFR26: 100% of production services must emit structured logs and core service metrics, and at least 95% of inbound requests must include distributed traces, sufficient to diagnose Sev-1/Sev-2 incidents within incident response SLAs.
- NFR27: Alerting must detect sustained increases in error rate, latency, and failed async jobs within 5 minutes.
- NFR28: Security-relevant events (failed auth spikes, permission-denied anomalies, unusual sensitive access patterns) must be monitored and alertable.
