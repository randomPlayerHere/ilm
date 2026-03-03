---
title: Manual Test Plan - Teacher OS
author: elephant
status: draft
---

# Manual Test Plan - Teacher OS

## Test Scope
- Roles: Teacher, Parent, Student, Principal/Org Manager, Admin
- Platforms: React Native mobile (teacher/parent), web admin dashboard, FastAPI backend APIs
- Environments: Local first, then AWS staging/prod smoke

## Entry Criteria
- Seed data loaded for all roles.
- Core services available (API, DB, storage, notifications).
- Test accounts and credentials validated.

## Exit Criteria
- All P0 and P1 tests pass.
- No open Sev-1/Sev-2 defects.
- Manual regression for changed modules completed.

## P0 Scenarios (Must Pass)
1. Authentication and RBAC
- Login/logout works for each role.
- Role cannot access unauthorized routes/data.

2. Teacher course creation/customization
- Teacher generates course draft.
- Teacher customizes with state-standard profile.
- Teacher publishes lesson.

3. Camera grading workflow
- Teacher captures and uploads assignment image.
- AI-assisted grade appears.
- Teacher edits/approves final grade.

4. Parent dashboard and alerts
- Parent sees child trend, risk, and projection.
- Parent receives configured alert/digest.

5. Teacher-parent messaging
- Teacher sends context-linked message.
- Parent replies; thread status updates.

6. Org dashboard
- Principal views weakest cohorts/subjects.
- Filters by grade/class/teacher work correctly.

## P1 Scenarios (Should Pass)
- Notification preference changes (instant/daily/weekly).
- Risk alert trigger timing and message clarity.
- Export analytics (if enabled) and verify data integrity.

## Negative and Security Tests
- Invalid login attempts and lockout behavior.
- Access attempts across org boundaries.
- Parent access to non-linked student blocked.
- Broken/expired image upload token handling.

## Data Validation Checks
- Grade changes produce audit entries.
- Trendline updates after approved grades.
- Communication metrics update after thread activity.

## AWS Deployment Smoke Checklist
- API health endpoints pass.
- RDS connectivity stable.
- S3 upload/download works via signed URLs.
- Notification pipeline functional.
- Core dashboards load within NFR latency targets.

## Defect Reporting Template
- ID, severity, environment, role, feature
- Repro steps
- Expected vs actual
- Screenshot/video evidence
- Suggested priority and owner

## Sign-off
- QA/Test lead sign-off
- Product owner sign-off
- Engineering lead sign-off
