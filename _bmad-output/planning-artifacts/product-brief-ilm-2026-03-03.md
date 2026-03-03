---
stepsCompleted: [1, 2]
inputDocuments:
  - /home/kuper/ss/teacherOs/ilm/_bmad-output/brainstorming/brainstorming-session-2025-03-01.md
date: 2026-03-03
author: elephant
---

# Product Brief: ilm

<!-- Content will be appended sequentially through collaborative workflow steps -->

## Executive Summary

Teacher OS (`ilm`) is an AI-assisted K-12 platform designed to reduce teacher workload while improving student outcomes through transparent, actionable parent-teacher collaboration. It combines AI-supported curriculum creation, camera-based grading with teacher approval, student progress/risk analytics, and role-based communication into a single multi-tenant system for schools and education organizations.

The core value is simple: help every stakeholder answer and act on the right question at the right time.
- Teachers: "How do I plan and grade faster without losing instructional quality?"
- Parents: "Is my child improving, and what should we do next?"
- Students: "Where am I growing, and how do I level up?"
- Principals/Org leaders: "Where are cohorts struggling, and how should we allocate resources?"

By combining human-in-the-loop AI, privacy-safe data access, and clear role-specific workflows, Teacher OS aims to become the operational backbone for modern K-12 teaching and family engagement.

---

## Core Vision

### Problem Statement

K-12 stakeholders operate in fragmented systems where curriculum planning, grading, progress monitoring, and parent communication are disconnected. Teachers are overburdened with repetitive planning and grading tasks; parents receive delayed or low-context updates; students often lack clear growth feedback; and school leaders struggle to identify intervention needs from reliable aggregate data.

### Problem Impact

- Teachers lose instructional time to manual grading and reactive communication.
- Parents cannot consistently see whether their child is improving or why performance changed.
- Students receive feedback that is often late, shallow, or hard to act on.
- Principals and org managers make staffing/intervention decisions with incomplete signals.
- Fragmentation increases operational overhead and reduces trust across teacher-parent relationships.

### Why Existing Solutions Fall Short

Current tools usually solve only one slice of the problem (LMS, messaging apps, grading tools, analytics dashboards) without a unified flow:
- Poor linkage between grading evidence, feedback, messaging context, and trend analytics.
- Limited explainability behind scores and risk indicators.
- Weak support for configurable communication cadences (instant/daily/weekly) that avoid overload.
- Insufficient role-aware data boundaries and tenant-safe defaults for sensitive student information.
- Few systems combine AI assistance with mandatory teacher approval and auditability.

### Proposed Solution

Teacher OS delivers a unified, role-based platform with:
- AI-assisted course and lesson generation that teachers can edit, version, and publish.
- Mobile camera-based grading pipeline (photo upload -> AI-proposed score/rubric/confidence -> teacher review/approval).
- Student/parent analytics with trend and risk views plus human-readable explanations.
- Threaded teacher-parent messaging linked to student, assignment, and analytics context.
- Configurable notifications and weekly parent digest workflows.
- Org-level cohort analytics for principals/managers, with default aggregate privacy protections.
- Strong RBAC, tenant isolation, and audit trails aligned to school privacy expectations.

### Key Differentiators

- Human-in-the-loop AI by design: automation accelerates decisions, teachers retain final authority.
- "Explainability-first" parent experience: progress and risk are contextualized, not just reported.
- End-to-end context chain: curriculum -> grading evidence -> analytics -> communication in one system.
- Multi-role utility in one product: teacher, parent, student, principal/org manager, and admin workflows cohere.
- Privacy and governance as product features: tenant isolation, role-scoped access, and auditable critical actions.
- Clear MVP discipline with measurable NFRs (latency, reliability, usability, and accessibility) to support implementation readiness.
