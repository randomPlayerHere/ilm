# ilm API (`apps/api`)

FastAPI service for TeacherOS.

## Story Scope

Implements identity + admin lifecycle baseline with:
- `POST /auth/login`
- `POST /auth/google`
- `POST /admin/organizations`
- `POST /admin/users/invite`
- `POST /admin/users/{user_id}/role`
- `POST /admin/users/{user_id}/membership`
- `PUT /admin/organizations/{org_id}/safety-controls`
- `GET /admin/organizations/{org_id}/safety-controls`
- `POST /courses/drafts/generate`
- `GET /courses/drafts/{draft_id}`
- `GET /courses/drafts`
- `PUT /courses/drafts/{draft_id}`
- `GET /courses/drafts/{draft_id}/revisions`
- `POST /courses/drafts/{draft_id}/student-variants`
- `POST /grading/assignments`
- `POST /grading/assignments/{assignment_id}/artifacts`
- `GET /grading/assignments/{assignment_id}/artifacts/{artifact_id}`
- `GET /grading/assignments/{assignment_id}/artifacts`
- `POST /grading/assignments/{assignment_id}/grading-jobs`
- `GET /grading/assignments/{assignment_id}/grading-jobs/{job_id}`
- `POST /admin/users/{user_id}/activate`
- `POST /admin/users/{user_id}/deactivate`
- `POST /admin/invitations/accept`
- `GET /admin/protected/organizations/{org_id}/summary`
- Generic invalid-credentials responses (anti-enumeration)
- JWT access token containing `sub`, `org_id`, and `role`
- Role-based home path in response
- In-memory organization creation, invitation onboarding, and user lifecycle transitions (`invited`, `active`, `deactivated`)

## Environment Variables

- `JWT_SECRET` (recommended; if omitted, API uses an ephemeral process-local secret)
- `JWT_ALGORITHM` (default: `HS256`)
- `JWT_ACCESS_TOKEN_EXP_MINUTES` (default: `60`)
- `GOOGLE_OAUTH_CLIENT_ID` (required for real Google token verification)
- `GOOGLE_OIDC_JWKS_URL` (default: `https://www.googleapis.com/oauth2/v3/certs`)
- `GOOGLE_OIDC_ALGORITHM` (default: `RS256`)

Google callback/token-exchange integration should issue an ID token to the backend,
which is submitted to `POST /auth/google` as `id_token`.

Admin lifecycle endpoints require `Authorization: Bearer <token>` with a JWT role claim of `admin`.
Protected summary endpoint requires authenticated actor role of `admin` or `principal`, and actor org scope must match path org.
Safety controls mutation endpoint requires admin role and same-org scope; read endpoint requires same-org role of `admin`, `principal`, or `teacher` and returns latest versioned org defaults.
Course draft generation, edit, and variant endpoints require authenticated `teacher` role and same-org ownership checks. Unknown or cross-tenant draft/student references fail closed with `403` to avoid resource enumeration.
Draft edits are persisted with immutable revision history (in-memory) and remain in `draft` state. Student-specific variants are stored as distinct drafts linked back to `base_draft_id` with a required `student_id`.
Revision history is available via `GET /courses/drafts/{draft_id}/revisions` for the owning teacher/org scope.
Assignment creation requires `teacher` role and ownership of the target class (org+teacher checks). Artifact upload accepts multipart `file` + form field `student_id`; supported media types: `image/jpeg`, `image/png`, `image/gif`, `image/webp`, `application/pdf`. Unsupported types return `422`. Artifacts are stored in-memory with a stub `storage_key` (`s3://stub/{artifact_id}`). Student must be enrolled in the assignment's class (class-boundary enforcement). All grading endpoints enforce fail-closed `403` on unknown or cross-tenant references.
AI grading jobs are submitted via `POST /grading/assignments/{assignment_id}/grading-jobs` (body: `{"artifact_id": "..."}`) and return `202 Accepted` with a `job_id`. Jobs are processed asynchronously via FastAPI `BackgroundTasks` (in-memory stub). Poll status via `GET /grading/assignments/{assignment_id}/grading-jobs/{job_id}`: returns `status` (`pending`/`processing`/`completed`/`failed`) and, when completed, a `result` block with `proposed_score`, `rubric_mapping`, and `draft_feedback`. Submitting a grading job for an artifact that already has a job returns the existing job (idempotency gate).

## Local Run

```bash
cd apps/api
python -m uvicorn app.main:app --reload
```

## Test

```bash
cd apps/api
pytest
```
