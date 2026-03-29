# Story 5.9: Assignment Artifact Storage and Retrieval

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a teacher,
I want captured assignment photos and grading records stored reliably and retrievable,
So that I can reference past work and maintain records for the school year.

## Acceptance Criteria

1. **Given** the mobile app has a photo ready for upload
   **When** it requests an upload URL from the API
   **Then** the API returns a time-limited S3 pre-signed upload URL scoped to the org's storage path
   **And** the mobile app uploads the image directly to S3 via the pre-signed URL
   **And** the storage path follows the pattern: `orgs/{org_id}/{class_id}/{student_id}/{assignment_id}/{uuid}.jpg`

2. **Given** a teacher views a student's assignment history
   **When** they select a past assignment
   **Then** the original photo, final grade, feedback, rubric scores, and practice recommendations are displayed
   **And** the photo loads via a time-limited pre-signed download URL (CloudFront CDN in production)

3. **Given** stored artifacts
   **When** access is requested
   **Then** artifact download URLs are scoped to authorized users within the organization (org-scoped RBAC)
   **And** artifacts are never exposed via raw bucket paths in API responses — only via signed URL accessors

## Tasks / Subtasks

- [x] Task 1: Update API storage service to support scoped upload and download URLs (AC: 1, 3)
  - [x] Update `PresignedUrlRequest` schema in `apps/api/app/domains/storage/router.py` to accept `class_id`, `student_id`, `assignment_id` (all optional strings, validated with safe-filename regex)
  - [x] Update `generate_presigned_upload_url` in `apps/api/app/core/storage.py` to accept `class_id`, `student_id`, `assignment_id` and generate key as `orgs/{org_id}/{class_id}/{student_id}/{assignment_id}/{uuid}.jpg`
  - [x] Add `generate_presigned_download_url(storage_key: str) -> str` to `apps/api/app/core/storage.py` (generates pre-signed GET URL, 900s expiry)
  - [x] Add `POST /v1/storage/presigned-download-url` endpoint to `apps/api/app/domains/storage/router.py`: accepts `{"key": str}`, validates key starts with `orgs/{actor.org_id}/` (org-scope guard), returns `{"url": str}`

- [x] Task 2: Update API artifact upload endpoint to accept storage_key (AC: 1, 3)
  - [x] Add `ArtifactRegisterRequest` Pydantic model to `apps/api/app/domains/grading/schemas.py` with fields: `student_id: str`, `storage_key: str`, `file_name: str`, `media_type: str`
  - [x] Add `POST /grading/assignments/{assignment_id}/artifacts/register` endpoint to `apps/api/app/domains/grading/router.py` that accepts `ArtifactRegisterRequest` (JSON body) and calls `service.create_artifact(...)` with the provided `storage_key` instead of generating a stub
  - [x] Keep the existing multipart `POST /grading/assignments/{assignment_id}/artifacts` endpoint unchanged (backward compatibility with offline queue processor which already calls it)
  - [x] Update `service.create_artifact` in `apps/api/app/domains/grading/service.py` to accept an optional `storage_key: str | None` parameter; if provided, use it; if not, generate stub key (existing behavior preserved)
  - [x] Update `InMemoryGradingRepository.create_artifact` in `apps/api/app/domains/grading/repository.py` to accept `storage_key: str | None` similarly

- [x] Task 3: Add teacher assignment history API endpoint (AC: 2)
  - [x] Add `AssignmentSummaryResponse` schema to `apps/api/app/domains/grading/schemas.py` with fields: `assignment_id`, `class_id`, `title`, `created_at`, `artifact_count: int`
  - [x] Add `AssignmentListResponse` schema with `assignments: list[AssignmentSummaryResponse]`
  - [x] Add `list_assignments_for_class` method to `InMemoryGradingRepository` that filters by `class_id` and `org_id`
  - [x] Add `list_assignments_for_class` method to `GradingService` with org-scope check
  - [x] Add `GET /grading/assignments?class_id={class_id}` endpoint to `apps/api/app/domains/grading/router.py` (teacher role required, returns `AssignmentListResponse`)

- [x] Task 4: Add photo retrieval to artifact response (AC: 2, 3)
  - [x] Add `GET /grading/assignments/{assignment_id}/artifacts/{artifact_id}/download-url` endpoint to `apps/api/app/domains/grading/router.py`; calls `generate_presigned_download_url(artifact.storage_key)` after org-scope check; returns `{"url": str}`
  - [x] In stub environment (MinIO), the URL will be a MinIO pre-signed URL; in production it will be S3/CloudFront — no code change needed between envs, just config

- [x] Task 5: Update mobile grading service for pre-signed URL upload flow (AC: 1)
  - [x] Add `getPresignedUploadUrl(classId: string, studentId: string, assignmentId: string, filename: string, token: string): Promise<{url: string; key: string}>` to `apps/mobile/src/services/grading-service.ts` — calls `POST /v1/storage/presigned-url`
  - [x] Add `uploadToPresignedUrl(presignedUrl: string, localUri: string): Promise<void>` helper — PUTs the file binary directly to S3 (no auth header, Content-Type: image/jpeg)
  - [x] Add `registerArtifact(assignmentId: string, storageKey: string, studentId: string, fileName: string, mediaType: string, token: string): Promise<{artifact_id: string}>` — calls `POST /grading/assignments/{id}/artifacts/register`
  - [x] **Do NOT modify existing `uploadArtifact`** — it is called by `useOfflineQueueProcessor` (5.8) and must remain for backward compatibility of that path. The new pre-signed flow is used in `useGradingJob` only.
  - [x] Update `useGradingJob.ts` (`apps/mobile/src/features/grading/hooks/useGradingJob.ts`) to use the new 3-step upload flow: `getPresignedUploadUrl` → `uploadToPresignedUrl` → `registerArtifact` (replaces the `uploadArtifact` call in the online path)

- [x] Task 6: Add assignment history screen (mobile) (AC: 2)
  - [x] Add `listAssignments(classId: string, token: string): Promise<AssignmentListResponse>` to `grading-service.ts`
  - [x] Add `getArtifactDownloadUrl(assignmentId: string, artifactId: string, token: string): Promise<{url: string}>` to `grading-service.ts`
  - [x] Add `AssignmentHistoryScreen` component at `apps/mobile/app/(teacher)/assignment-history.tsx` — lists assignments for current class, shows title, date, artifact count; tapping navigates to detail
  - [x] Add `AssignmentDetailScreen` at `apps/mobile/app/(teacher)/assignment-detail.tsx` — shows photo (loaded from download URL via `<Image source={{uri: downloadUrl}}`), grade, feedback, rubric scores, practice recommendations for a selected artifact
  - [x] Wire history screen into teacher tab navigation (Grading tab header or separate History tab per UX spec)

- [x] Task 7: Update contracts (AC: 1, 2)
  - [x] Add to `packages/contracts/src/grading.ts`:
    - `ArtifactRegisterRequest` interface
    - `ArtifactDownloadUrlResponse` interface
    - `AssignmentSummaryResponse` interface
    - `AssignmentListResponse` interface
  - [x] Export new types from `packages/contracts/src/index.ts`

- [x] Task 8: Tests
  - [x] `apps/api/tests/test_storage_api.py` — test scoped pre-signed upload URL (path format), test download URL org-scope guard (wrong org → 403), test missing key format → 422
  - [x] `apps/api/tests/test_grading_api.py` — test `POST /grading/assignments/{id}/artifacts/register`, test `GET /grading/assignments?class_id=`, test `GET /grading/assignments/{id}/artifacts/{id}/download-url`
  - [x] `apps/mobile/src/services/__tests__/grading-service.test.ts` — test `getPresignedUploadUrl`, `uploadToPresignedUrl`, `registerArtifact`, `listAssignments`, `getArtifactDownloadUrl`
  - [x] `apps/mobile/app/(teacher)/__tests__/assignment-history.test.tsx` — smoke test: renders assignment list, tap navigates to detail

## Dev Notes

### Architecture Overview

Story 5.9 closes the loop on the image pipeline described in the architecture:

```
Teacher capture → client compress (~2MP) [Story 5.2]
  → getPresignedUploadUrl (API: /v1/storage/presigned-url)
  → PUT image directly to S3/MinIO via pre-signed URL  [Story 5.9]
  → registerArtifact (API: /grading/assignments/{id}/artifacts/register)
  → submitGradingJob [Stories 5.3–5.8]
  → (later) getArtifactDownloadUrl → load photo in history screen [Story 5.9]
```

The existing `uploadArtifact` (multipart) is kept for the offline queue processor path (Story 5.8). The online path in `useGradingJob` switches to the pre-signed URL flow.

### Critical Architecture Constraints

1. **Never expose raw S3 bucket paths** — The `ArtifactResponse.storage_key` currently leaks `s3://stub/artf_1`. The `ArtifactResponse` schema has a comment noting this (Story 2.4 deferred fix). Story 5.9 MUST NOT add any new endpoint that returns raw `storage_key` values. All photo access goes through the `/download-url` endpoint.

2. **Org-scope guard on download URL** — The `POST /v1/storage/presigned-download-url` endpoint must validate that the requested `key` starts with `orgs/{actor.org_id}/`. Reject with 403 otherwise. This prevents cross-org access via key guessing.

3. **Pre-signed URL expiry** — Both upload and download URLs use 900 seconds (15 minutes). This is already configured in `_PRESIGNED_URL_EXPIRY_SECONDS` in `apps/api/app/core/storage.py`. Do not change it.

4. **Direct PUT to S3** — When calling the pre-signed upload URL from mobile, use a raw `fetch` PUT request with `Content-Type: image/jpeg`. Do NOT include the `Authorization` header — pre-signed URLs are already authorized by AWS/MinIO. Including an auth header will cause a signature mismatch error.

5. **Storage key format change** — The current `generate_presigned_upload_url` creates keys as `orgs/{org_id}/assignments/{uuid}/{filename}`. Story 5.9 changes this to `orgs/{org_id}/{class_id}/{student_id}/{assignment_id}/{uuid}.jpg` to match the spec. The new endpoint signature adds `class_id`, `student_id`, `assignment_id` parameters. The old path format is only used by the existing `/v1/storage/presigned-url` calls, which in the live codebase are not yet wired to mobile (no existing mobile caller before this story). Safe to change.

6. **MinIO local compatibility** — `app/core/storage.py` already configures boto3 with path-style addressing and `s3_endpoint_url` for MinIO. No changes needed to the S3 client configuration. The pre-signed download URL will use MinIO's URL in local dev (e.g., `http://minio:9000/...`). In production, a CloudFront distribution sits in front of S3 — the URL returned by boto3 will be an S3 URL; CDN fronting is an infrastructure concern, not a code concern for this story.

7. **`useGradingJob` online path — upload flow change** — The current `run()` function in `useGradingJob.ts` calls `uploadArtifact(assignmentId, studentId, compressedUri, token)`. Replace this with the 3-step sequence: `getPresignedUploadUrl` → `uploadToPresignedUrl` → `registerArtifact`. The offline path (at the top of `run()`) still calls the existing `uploadArtifact` via `useOfflineQueueProcessor` — do NOT touch that.

8. **`isMountedRef` pattern** — All async operations in hooks must check `isMountedRef.current` before setting state. Follow the exact same pattern as `useGradingJob`, `useManualGrading`, and `useGradeApproval`. See those files for reference.

### Existing File Locations

| File | Path |
|---|---|
| Storage core module | `apps/api/app/core/storage.py` |
| Storage router | `apps/api/app/domains/storage/router.py` |
| Grading router | `apps/api/app/domains/grading/router.py` |
| Grading schemas | `apps/api/app/domains/grading/schemas.py` |
| Grading service | `apps/api/app/domains/grading/service.py` |
| Grading repository | `apps/api/app/domains/grading/repository.py` |
| Mobile grading service | `apps/mobile/src/services/grading-service.ts` |
| useGradingJob hook | `apps/mobile/src/features/grading/hooks/useGradingJob.ts` |
| Contracts grading types | `packages/contracts/src/grading.ts` |
| Contracts index | `packages/contracts/src/index.ts` |
| API client utility | `apps/mobile/src/services/api-client.ts` |

### New Files to Create

| File | Purpose |
|---|---|
| `apps/mobile/app/(teacher)/assignment-history.tsx` | Assignment history list screen |
| `apps/mobile/app/(teacher)/assignment-detail.tsx` | Assignment detail with photo + grade |
| `apps/mobile/src/services/__tests__/grading-service.test.ts` | Tests for new service functions |
| `apps/mobile/app/(teacher)/__tests__/assignment-history.test.tsx` | Smoke tests for history screen |

### Key API Changes Summary

**Updated endpoint — `POST /v1/storage/presigned-url`:**
```json
// Request (updated schema)
{
  "filename": "assignment.jpg",
  "class_id": "cls_abc",
  "student_id": "stu_xyz",
  "assignment_id": "asgn_123"
}
// Response (unchanged)
{ "url": "https://...", "key": "orgs/{org_id}/{class_id}/{student_id}/{assignment_id}/{uuid}.jpg" }
```

**New endpoint — `POST /v1/storage/presigned-download-url`:**
```json
// Request
{ "key": "orgs/{org_id}/{class_id}/{student_id}/{assignment_id}/{uuid}.jpg" }
// Response
{ "url": "https://... (time-limited GET URL)" }
```

**New endpoint — `POST /grading/assignments/{id}/artifacts/register`:**
```json
// Request
{ "student_id": "stu_xyz", "storage_key": "orgs/.../uuid.jpg", "file_name": "assignment.jpg", "media_type": "image/jpeg" }
// Response — same as existing ArtifactResponse
{ "artifact_id": "artf_1", "assignment_id": "...", ... }
```

**New endpoint — `GET /grading/assignments?class_id={class_id}`:**
```json
// Response
{ "assignments": [{ "assignment_id": "...", "class_id": "...", "title": "...", "created_at": "...", "artifact_count": 2 }] }
```

**New endpoint — `GET /grading/assignments/{id}/artifacts/{artifact_id}/download-url`:**
```json
// Response
{ "url": "https://... (time-limited GET URL)" }
```

### Backward Compatibility — Critical

- `POST /grading/assignments/{id}/artifacts` (multipart) — **do not change**. Used by `useOfflineQueueProcessor` in Story 5.8.
- `app/core/storage.py::generate_presigned_upload_url` — add `class_id`, `student_id`, `assignment_id` as keyword-only parameters with defaults of `""` to avoid breaking any direct callers (there are no mobile callers before this story, but keep Python signature backward-compatible).

### Mobile Upload Flow (Updated `useGradingJob.ts`)

Replace the `uploadArtifact` call in the online path with:

```typescript
// Step 1: Get pre-signed upload URL
const { url: presignedUrl, key: storageKey } = await getPresignedUploadUrl(
  classId, studentId, assignmentId, 'assignment.jpg', token
);
// Step 2: PUT directly to S3 — NO Authorization header
await uploadToPresignedUrl(presignedUrl, compressedUri);
// Step 3: Register artifact with API using storage key
const { artifact_id: artifactId } = await registerArtifact(
  assignmentId, storageKey, studentId, 'assignment.jpg', 'image/jpeg', token
);
```

### Grading Repository — Stub Behavior

`InMemoryGradingRepository.create_artifact` currently generates `storage_key = f"s3://stub/{artifact_id}"`. With this story, it should accept an optional `storage_key` parameter. If provided (from `registerArtifact` endpoint), use it. If not (from existing multipart endpoint), keep the stub behavior. This ensures both paths work during the transition.

### Previous Story Intelligence (5.8)

From Story 5.8:
- `useOfflineQueueProcessor` calls `uploadArtifact` (multipart) for offline-queued photos on reconnect — this path must remain untouched
- `useGradingJob.ts` has the `isMountedRef` pattern established — follow it exactly
- `clearPendingCapture()` is called after successful upload — ensure this is still called after `registerArtifact` succeeds in the updated online path
- Jest mock factories require `__esModule: true` for ESM-interop packages

### Git Intelligence (Recent Commits)

- `5a23f746` — Merge PR #3 (dev/harshit): Stories 5.7–5.8 offline queue
- `b66f7e12` — Merge PR #2 (temp): Stories 5.5–5.6
- `c7905df4` — Story 5.6: manual grading (modified `useGradingJob`, `useManualGrading`, `GradingCard`)
- `ffc1d7dc` — Story 5.5: grade approval (established `useGradeApproval` patterns)
- Feature work from `harshit-05/dev/harshit` branch via PRs to `main`

### Project Structure Notes

- New screens go in `apps/mobile/app/(teacher)/` following existing pattern (see `grading.tsx`)
- `grading-service.ts` is the single service file for grading domain — add all new service functions there, do not create a separate service file
- API Python tests live in `apps/api/tests/` — follow the existing pattern in `test_progress_api.py`
- The `packages/contracts` package is shared — any type added here must be backward-compatible

### Design Token Reference (Tamagui)

For assignment history and detail screens:
```typescript
import { colors, fonts, fontWeights, radii } from "@ilm/design-tokens";
```
- Follow the same card/list patterns established in `GradingCard.tsx` and the grading screen
- Photo loading: use React Native `<Image>` or Expo `<Image>` with the pre-signed download URL. Show a skeleton/placeholder while loading. Handle load errors gracefully.

### References

- Storage core: [apps/api/app/core/storage.py](apps/api/app/core/storage.py)
- Storage router: [apps/api/app/domains/storage/router.py](apps/api/app/domains/storage/router.py)
- Grading router: [apps/api/app/domains/grading/router.py](apps/api/app/domains/grading/router.py)
- Grading schemas: [apps/api/app/domains/grading/schemas.py](apps/api/app/domains/grading/schemas.py)
- Grading service: [apps/api/app/domains/grading/service.py](apps/api/app/domains/grading/service.py)
- Grading repository: [apps/api/app/domains/grading/repository.py](apps/api/app/domains/grading/repository.py)
- Mobile grading service: [apps/mobile/src/services/grading-service.ts](apps/mobile/src/services/grading-service.ts)
- Grading job hook: [apps/mobile/src/features/grading/hooks/useGradingJob.ts](apps/mobile/src/features/grading/hooks/useGradingJob.ts)
- Offline queue processor: [apps/mobile/src/features/grading/hooks/useOfflineQueueProcessor.ts](apps/mobile/src/features/grading/hooks/useOfflineQueueProcessor.ts)
- Contracts grading types: [packages/contracts/src/grading.ts](packages/contracts/src/grading.ts)
- Architecture — image pipeline, pre-signed URL: [_bmad-output/planning-artifacts/architecture.md](_bmad-output/planning-artifacts/architecture.md)
- Previous story (5.8): [_bmad-output/implementation-artifacts/5-8-offline-photo-queue-and-auto-upload.md](_bmad-output/implementation-artifacts/5-8-offline-photo-queue-and-auto-upload.md)
- Epic 5 story spec: [_bmad-output/planning-artifacts/epics.md](_bmad-output/planning-artifacts/epics.md) (Story 5.9 at line 818)

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- All 8 tasks implemented and tested. 86 API tests pass, 193 mobile tests pass (all grading suites).
- `grading.test.tsx` required a mock for `useNetworkStatus` (added in Story 5.8 but test mock was missing).
- `generate_presigned_upload_url` extended with keyword-only `class_id`, `student_id`, `assignment_id` params (defaulting to `""`) to preserve backward compatibility.
- Stub storage keys (`s3://stub/...`) returned as-is from download-url endpoint to support local dev/test without MinIO.
- Assignment history and detail screens registered as non-tab screens (`href: null`) in `_layout.tsx`.

### File List

- `apps/api/app/core/storage.py`
- `apps/api/app/domains/storage/router.py`
- `apps/api/app/domains/grading/schemas.py`
- `apps/api/app/domains/grading/repository.py`
- `apps/api/app/domains/grading/service.py`
- `apps/api/app/domains/grading/router.py`
- `apps/api/tests/test_storage_api.py`
- `apps/api/tests/test_grading_api.py`
- `apps/api/tests/test_progress_api.py`
- `packages/contracts/src/grading.ts`
- `packages/contracts/src/index.ts`
- `apps/mobile/src/services/grading-service.ts`
- `apps/mobile/src/services/__tests__/grading-service.test.ts`
- `apps/mobile/src/features/grading/hooks/useGradingJob.ts`
- `apps/mobile/src/features/grading/hooks/useGradeApproval.ts`
- `apps/mobile/src/features/grading/hooks/useManualGrading.ts`
- `apps/mobile/src/features/grading/hooks/__tests__/useGradingJob.test.ts`
- `apps/mobile/src/features/grading/hooks/__tests__/useGradeApproval.test.ts`
- `apps/mobile/src/features/grading/hooks/__tests__/useGradingReview.test.ts`
- `apps/mobile/src/features/grading/hooks/__tests__/useManualGrading.test.ts`
- `apps/mobile/src/features/grading/components/GradingCard.tsx`
- `apps/mobile/src/features/grading/components/__tests__/GradingCard.test.tsx`
- `apps/mobile/app/(teacher)/assignment-history.tsx` (new)
- `apps/mobile/app/(teacher)/assignment-detail.tsx` (new)
- `apps/mobile/app/(teacher)/__tests__/assignment-history.test.tsx` (new)
- `apps/mobile/app/(teacher)/__tests__/grading.test.tsx`
- `apps/mobile/app/(teacher)/_layout.tsx`
- `apps/mobile/app/(teacher)/grading.tsx`
- `apps/mobile/package.json`
- `pnpm-lock.yaml`
