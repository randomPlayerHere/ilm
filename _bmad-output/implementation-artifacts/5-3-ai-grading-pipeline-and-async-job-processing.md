# Story 5.3: AI Grading Pipeline and Async Job Processing

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a teacher,
I want my captured assignment photos to be automatically analyzed by AI and return grading suggestions,
So that I can review AI-suggested grades instead of grading from scratch.

## Acceptance Criteria

1. **Given** a photo is captured and accepted in the camera screen
   **When** the grading screen opens
   **Then** the mobile app uploads the photo as an artifact, submits an async grading job, and displays a skeleton loading state while waiting for the AI result (< 10 seconds in dev/mock mode)
   **And** the pending capture store is cleared after successful upload

2. **Given** the AI grading job completes successfully
   **When** the polling detects `status = "completed"`
   **Then** the GradingCard displays: photo thumbnail (80×80px), suggested score, AI-generated feedback text, collapsible rubric breakdown, and confidence indicator (high=green / medium=amber / low=red)
   **And** the teacher receives a push notification if they navigated away (push notification deferred to Epic 8 — just implement the card display here)

3. **Given** multiple photos are submitted in a batch session (teacher captures → grades → back → captures → grades)
   **When** AI processing completes for each photo individually
   **Then** each grading result is shown as the teacher reaches that grading screen (not blocked on others)
   **And** a batch progress counter (e.g. "2 of 5 graded") appears at the top of the grading screen when the calling screen passes a total count via route params

4. **Given** the AI processing job fails after internal retries (all 3 attempts exhausted)
   **When** the failure is reported
   **Then** the GradingCard displays an error state with a user-facing message ("Couldn't analyze this one")
   **And** the detailed fallback actions (Retake / Grade Manually) are deferred to Story 5.6

## Tasks / Subtasks

- [x] Task 1: Create mobile grading API service (AC: 1, 2)
  - [x] Create `apps/mobile/src/services/grading-service.ts`
  - [x] `createAssignment(classId: string, title: string, token: string): Promise<{ assignment_id: string }>` — callers pass title as `"Assignment ${new Date().toLocaleDateString()}"` (timestamp-based, no user input needed)
  - [x] `uploadArtifact(assignmentId: string, studentId: string, compressedUri: string, token: string): Promise<{ artifact_id: string }>` — must use `fetch()` with `FormData` (NOT `apiRequest`, which is JSON-only)
  - [x] `submitGradingJob(assignmentId: string, artifactId: string, token: string): Promise<GradingJobResponse>`
  - [x] `getGradingJob(assignmentId: string, jobId: string, token: string): Promise<GradingJobWithResultResponse>`
  - [x] Import types from `@ilm/contracts` (`GradingJobResponse`, `GradingJobWithResultResponse`)

- [x] Task 2: Create `useGradingJob` hook (AC: 1, 2, 4)
  - [x] Create `apps/mobile/src/features/grading/hooks/useGradingJob.ts`
  - [x] On mount: read token via `getAuthData()` — if null, set `status = 'failed'` and `error = "Session expired — please sign in again"` and return early (do not navigate; the `setUnauthorizedHandler` in `api-client.ts` handles the redirect automatically on 401 responses)
  - [x] Read pending capture from `getPendingCapture()` — `photoUri` in the return value is `pendingCapture.compressedUri` (the local compressed file URI set by `CameraCapture.acceptCapture()`)
  - [x] Sequential async flow: `createAssignment(classId, title, token)` → `uploadArtifact` → `submitGradingJob` → start polling → `clearPendingCapture()`
  - [x] Poll `getGradingJob()` using recursive `setTimeout` (NOT `setInterval`) every 2000ms — see polling pattern in Dev Notes to avoid concurrent overlapping requests on slow networks
  - [x] Max 30 poll attempts (~60s timeout) → set error state "Request timed out" on timeout
  - [x] Return `{ status: 'idle' | 'uploading' | 'processing' | 'completed' | 'failed', result: GradingJobWithResultResponse | null, error: string | null, photoUri: string | null }` where `photoUri` = `pendingCapture.compressedUri`
  - [x] Clean up with `useRef<ReturnType<typeof setTimeout> | null>` — call `clearTimeout` on unmount

- [x] Task 3: Create `GradingCard` component (AC: 2, 4)
  - [x] Create `apps/mobile/src/features/grading/components/GradingCard.tsx`
  - [x] Component props interface (define at top of file):

    ```typescript
    interface GradingCardProps {
      status: 'uploading' | 'processing' | 'completed' | 'failed';
      result: GradingJobWithResultResponse | null;
      photoUri: string | null; // compressedUri from pending capture
      error: string | null;
    }
    ```

  - [x] **Skeleton state** (status = uploading/processing): animated gray placeholder boxes (photo area, score area, text area) using `Animated.loop` + `Animated.timing` fade between 0.3 and 0.8 opacity
  - [x] **Loaded state** (status = completed):
    - Photo thumbnail 80×80px via `<Image source={{ uri: photoUri }} style={{ width: 80, height: 80 }} />`
    - Suggested score: large text from `result.result.proposed_score` (e.g. "85/100")
    - Confidence badge pill: text "High" / "Medium" / "Low" with background color (see confidence colors in Dev Notes)
    - AI feedback text from `result.result.draft_feedback`
    - Collapsible rubric section: tappable "Rubric breakdown ▼" toggle that expands to show criterion → rating pairs from `result.result.rubric_mapping`
  - [x] **Error state** (status = failed): "Couldn't analyze this one" message with secondary text from `error` prop
  - [x] Use `colors`, `fonts`, `fontWeights` from `@ilm/design-tokens`
  - [x] Confidence colors: used `colors.confidenceHigh`, `colors.confidenceMedium`, `colors.confidenceLow` — named tokens found in design-tokens (no fallback hex needed)

- [x] Task 4: Create grading screen (AC: 1, 2, 3)
  - [x] Create `apps/mobile/app/(teacher)/grading.tsx`
  - [x] Receive route params via `useLocalSearchParams<{ classId: string; studentId: string; batchIndex?: string; batchTotal?: string }>()`
  - [x] Use `useGradingJob` hook (passing `classId`, `studentId`)
  - [x] Render `GradingCard` connected to hook state
  - [x] Batch header: if `batchTotal` param is present, show `"${batchIndex} of ${batchTotal} graded"` — the calling screen passes these counters; this screen does NOT manage a queue itself (one photo per screen instance)
  - [x] "Done" button calls `router.back()` — since camera→grading used `router.replace`, back() returns to whatever was before the camera (the teacher tabs)
  - [x] SafeAreaView wrapper for proper inset handling
  - [x] **Also update `apps/mobile/app/(teacher)/_layout.tsx`**: add a `<Tabs.Screen name="grading" options={{ href: null }} />` entry (same pattern as `camera`) to hide the grading screen from the tab bar

- [x] Task 5: Update camera screen navigation (AC: 1)
  - [x] In `apps/mobile/app/(teacher)/camera.tsx`, add `useLocalSearchParams<{ classId?: string; studentId?: string }>()`
  - [x] Change `handleCaptureAccepted` to navigate to grading screen:

    ```typescript
    router.replace({ pathname: '/(teacher)/grading', params: { classId, studentId } });
    ```

  - [x] Pass through any `classId` / `studentId` params received from caller (CameraFab)

- [x] Task 6: Update CameraFab to pass context params (AC: 1)
  - [x] In `apps/mobile/src/components/CameraFab.tsx`, accept optional `classId?: string` and `studentId?: string` props
  - [x] Update `router.push` call: `router.push({ pathname: '/(teacher)/camera', params: { classId, studentId } })`
  - [x] For dev: default to `classId="cls_demo_math_1"` and `studentId="stu_demo_1"` when not provided (allows FAB to work without full assignment picker UI, which is a later story)
  - [x] Update callers in teacher layout to pass appropriate props (or leave as-is to use defaults)

- [x] Task 7: Tests (AC: 1, 2)
  - [x] `apps/mobile/src/services/__tests__/grading-service.test.ts`:
    - Mock `fetch` globally (jest `global.fetch = jest.fn()`)
    - Test `uploadArtifact` sends `FormData` with `student_id` field and `file` blob
    - Test `submitGradingJob` sends correct JSON body `{ artifact_id }`
    - Test `getGradingJob` hits correct GET URL
    - Test error propagation via `ApiError` on non-2xx responses
  - [x] `apps/mobile/src/features/grading/hooks/__tests__/useGradingJob.test.ts`:
    - Mock `grading-service` module functions
    - Mock `pending-capture-store` — pre-seed a fake `PendingCapture` with `compressedUri: 'file://test.jpg'`
    - Mock `token-storage` — return `{ token: 'fake-token', role: 'teacher', homePath: '/', email: 'test@test.com' }`
    - Use `jest.useFakeTimers()` to advance polling `setTimeout` calls
    - Assert: `photoUri` in returned state equals `pendingCapture.compressedUri`
    - Assert: state transitions `uploading` → `processing` → `completed`
    - Assert: on failed job, state becomes `failed` with error message
    - Assert: `clearTimeout` is called on unmount (spy on global `clearTimeout`)
    - Assert: when `getAuthData()` returns null, status = `'failed'` with session-expired message
  - [x] `apps/mobile/src/features/grading/components/__tests__/GradingCard.test.tsx`:
    - Render skeleton state → no score text visible
    - Render completed state → score visible, confidence badge matches color
    - Render failed state → error message visible
  - [x] Verify: all 9 existing mobile tests still pass (0 regressions) — 33/33 total pass
  - [x] Verify: no backend changes — backend untouched

### Review Follow-ups (AI)

- [x] [AI-Review][High] Story scope mismatch: backend grading files were modified while story claims mobile-only implementation — RESOLVED: 5.1/5.2 backend committed separately ("epic 5.1/5.2: AI grading service backend and contracts")
- [x] [AI-Review][High] "no backend changes — backend untouched" is misleading in git state — RESOLVED: commits now cleanly separated; 5.3 commit is mobile-only
- [x] [AI-Review][Medium] Batch header guarded for both params — FIXED: grading.tsx now requires `batchTotal && batchIndex` [apps/mobile/app/(teacher)/grading.tsx]
- [x] [AI-Review][Medium] Missing `classId`/`studentId` runtime guard — FIXED: params typed optional; missingParams overrides status/error display [apps/mobile/app/(teacher)/grading.tsx]
- [x] [AI-Review][Medium] Story file list incomplete — FIXED: added babel.config.js, app.config.ts, grading.ts contract, index.ts
- [ ] [AI-Review][Low] Animated skeleton tests emit repeated `act(...)` warnings; stabilize test harness for clean output [apps/mobile/src/features/grading/components/__tests__/GradingCard.test.tsx:1]
- [x] [AI-Review][High] Poll catch block did not increment attemptRef — infinite polling on network failure — FIXED [apps/mobile/src/features/grading/hooks/useGradingJob.ts]
- [x] [AI-Review][Medium] 4xx poll errors retried indefinitely — FIXED: ApiError with status 400-499 now sets failed state immediately [apps/mobile/src/features/grading/hooks/useGradingJob.ts]
- [x] [AI-Review][Medium] Rubric expansion untested (AC 2) — FIXED: 3 new tests covering hidden default, expand on press [apps/mobile/src/features/grading/components/__tests__/GradingCard.test.tsx]
- [x] [AI-Review][High] GradingCard null-result completed state untested — FIXED: test added [apps/mobile/src/features/grading/components/__tests__/GradingCard.test.tsx]
- [x] [AI-Review][Medium] Hardcoded "AI grading failed" error — FIXED: improved to "AI grading did not complete — please try again." [apps/mobile/src/features/grading/hooks/useGradingJob.ts]

## Dev Notes

### Architecture Overview

**This story is predominantly mobile-side work.** The entire backend grading pipeline is already fully implemented and tested from Stories 5.1 and 5.2. No backend changes are required.

**Backend endpoints available (already implemented):**

| Method | Path | Status |
| ------ | ---- | ------ |
| POST | `/grading/assignments` | ✅ Done — creates an assignment |
| POST | `/grading/assignments/{id}/artifacts` | ✅ Done — multipart file upload |
| POST | `/grading/assignments/{id}/grading-jobs` | ✅ Done — submits job, returns 202 |
| GET | `/grading/assignments/{id}/grading-jobs/{job_id}` | ✅ Done — returns status + result |

**Auth for API calls:** All grading endpoints require `Authorization: Bearer <token>`. Get token via `getAuthData()` from `apps/mobile/src/services/token-storage.ts`. Returns `AuthData | null`; show auth error if null.

### CRITICAL: BackgroundTasks vs SQS

The architecture document specifies SQS for async job processing. The current implementation uses **FastAPI `BackgroundTasks`** (in-process, synchronous execution after the 202 response). In local dev:

- The background task runs *immediately* after `POST /grading-jobs` returns 202
- With `MockAIGradingProvider` (AI_MOCK_MODE=true), the job completes **in milliseconds**
- The first poll at t=2s will almost certainly return `status = "completed"` already

**This is expected behavior in dev.** The polling implementation is still required for production correctness when real SQS + worker service is deployed. Do NOT remove the polling loop because it seems "instant" in dev.

### CRITICAL: Seed Data for Dev

The `InMemoryGradingRepository` is pre-seeded on startup with these IDs that must be used in dev:

| Entity | ID | Notes |
| ------ | -- | ----- |
| Class | `cls_demo_math_1` | org: org_demo_1, teacher: usr_teacher_1 |
| Student | `stu_demo_1` | class: cls_demo_math_1, teacher: usr_teacher_1 |
| Student | `usr_student_1` | class: cls_demo_math_1, teacher: usr_teacher_1 |

The authenticated teacher JWT **must** have `sub = "usr_teacher_1"` and `org_id = "org_demo_1"` for the grading endpoints to accept requests. This is the demo user seeded by the auth domain. If a different user is logged in, all grading operations will return 403.

**Implication for CameraFab defaults:** The `classId` and `studentId` defaults in CameraFab (`cls_demo_math_1` / `stu_demo_1`) only work when the teacher is logged in as the demo user. This is acceptable for the dev iteration of this story.

### Mobile: Multipart Artifact Upload

The `apiRequest<T>` helper in `api-client.ts` sends `Content-Type: application/json`. It **cannot** be used for file upload. Use `fetch()` directly:

```typescript
// In grading-service.ts — uploadArtifact implementation pattern
const formData = new FormData();
formData.append('student_id', studentId);
formData.append('file', {
  uri: compressedUri,
  type: 'image/jpeg',
  name: 'assignment.jpg',
} as any); // React Native FormData accepts {uri, type, name} objects

const response = await fetch(`${API_BASE_URL}/grading/assignments/${assignmentId}/artifacts`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    // IMPORTANT: Do NOT set Content-Type — let fetch set multipart boundary automatically
  },
  body: formData,
});
if (!response.ok) {
  const body = await response.json().catch(() => ({}));
  throw new ApiError(String(response.status), body.detail ?? 'Upload failed', response.status);
}
return response.json();
```

Import `API_BASE_URL` and `ApiError` from `./api-client`.

> **⚠️ `ApiError` naming conflict:** `packages/contracts/src/index.ts` also exports an *interface* named `ApiError` (with shape `{ error: { code, message } }`). This is different from the `ApiError` *class* in `api-client.ts`. Never import `ApiError` from `@ilm/contracts` in service files — always import the class from `./api-client`.

### Mobile: Polling Hook Pattern

Use **recursive `setTimeout`**, NOT `setInterval`. `setInterval` with an async callback fires the next tick regardless of whether the previous async request has resolved — on a slow network, requests pile up and setState is called in unpredictable order.

```typescript
// useGradingJob.ts — correct polling pattern
const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
const attemptRef = useRef(0);
const isMountedRef = useRef(true);

const scheduleNextPoll = useCallback((assignmentId: string, jobId: string, token: string) => {
  timerRef.current = setTimeout(async () => {
    if (!isMountedRef.current) return;
    attemptRef.current += 1;
    if (attemptRef.current > 30) {
      setState(s => ({ ...s, status: 'failed', error: 'Request timed out' }));
      return;
    }
    try {
      const job = await getGradingJob(assignmentId, jobId, token);
      if (!isMountedRef.current) return;
      if (job.status === 'completed' || job.status === 'failed') {
        setState(s => ({ ...s, status: job.status, result: job }));
      } else {
        scheduleNextPoll(assignmentId, jobId, token); // reschedule only after resolve
      }
    } catch {
      if (isMountedRef.current) scheduleNextPoll(assignmentId, jobId, token);
    }
  }, 2000);
}, []);

// Cleanup
useEffect(() => {
  isMountedRef.current = true;
  return () => {
    isMountedRef.current = false;
    if (timerRef.current !== null) clearTimeout(timerRef.current);
  };
}, []);
```

### Mobile: Grading Screen Route Typing (expo-router)

```typescript
// grading.tsx
import { useLocalSearchParams } from 'expo-router';

const { classId, studentId } = useLocalSearchParams<{
  classId: string;
  studentId: string;
}>();
```

```typescript
// Camera.tsx — navigate to grading after capture
const { classId = 'cls_demo_math_1', studentId = 'stu_demo_1' } =
  useLocalSearchParams<{ classId?: string; studentId?: string }>();

function handleCaptureAccepted(_result: CaptureResult) {
  router.replace({
    pathname: '/(teacher)/grading',
    params: { classId, studentId },
  });
}
```

### Mobile: GradingCard Skeleton Animation Pattern

```typescript
// Fade loop between dim (0.3) and bright (0.8) opacity
const fadeAnim = useRef(new Animated.Value(0.3)).current;

useEffect(() => {
  const loop = Animated.loop(
    Animated.sequence([
      Animated.timing(fadeAnim, { toValue: 0.8, duration: 800, useNativeDriver: true }),
      Animated.timing(fadeAnim, { toValue: 0.3, duration: 800, useNativeDriver: true }),
    ])
  );
  loop.start();
  return () => loop.stop();
}, [fadeAnim]);
```

### Mobile: Confidence Badge Colors

First check if `@ilm/design-tokens` exports warning/danger color tokens (inspect `packages/design-tokens/src/`). If named tokens exist (e.g. `colors.warning`, `colors.danger`), use those. If not, fall back to:

```typescript
const CONFIDENCE_COLORS: Record<string, string> = {
  high: colors.primary,   // green — always use the token, not a hard-coded hex
  medium: '#F59E0B',      // amber fallback — replace with token if available
  low: '#EF4444',         // red fallback — replace with token if available
};
```

**Do not hard-code the hex for `colors.primary`** — it's the same green used on the CameraFab and primary buttons. Always reference the token so theme changes propagate.

### Design Token Usage

Import from `@ilm/design-tokens` (as in all other mobile files):

```typescript
import { colors, fonts, fontWeights, radii } from '@ilm/design-tokens';
```

The `colors.primary` is the green used for FAB, primary buttons, and high-confidence badges.

### Project Structure Notes

**Files to CREATE:**

- `apps/mobile/src/services/grading-service.ts` — grading API service (upload, submit, poll)
- `apps/mobile/src/features/grading/hooks/useGradingJob.ts` — orchestration hook
- `apps/mobile/src/features/grading/components/GradingCard.tsx` — result display component
- `apps/mobile/app/(teacher)/grading.tsx` — grading screen
- `apps/mobile/src/services/__tests__/grading-service.test.ts` — service unit tests
- `apps/mobile/src/features/grading/hooks/__tests__/useGradingJob.test.ts` — hook unit tests
- `apps/mobile/src/features/grading/components/__tests__/GradingCard.test.tsx` — component tests

**Files to MODIFY:**

- `apps/mobile/app/(teacher)/camera.tsx` — change `handleCaptureAccepted` to navigate to grading screen; add `useLocalSearchParams` for `classId`/`studentId`
- `apps/mobile/src/components/CameraFab.tsx` — accept optional `classId`/`studentId` props, pass to camera route, add dev defaults
- `apps/mobile/app/(teacher)/_layout.tsx` — add `<Tabs.Screen name="grading" options={{ href: null }} />` to hide grading route from tab bar (same pattern as the existing `camera` entry)

**Files NOT to touch:**

- Backend grading domain (`apps/api/app/domains/grading/`) — fully complete
- `apps/mobile/src/services/api-client.ts` — use as-is, don't modify
- `apps/mobile/src/services/image-compressor.ts` — use as-is
- `apps/mobile/src/features/grading/pending-capture-store.ts` — use as-is (setPendingCapture/getPendingCapture/clearPendingCapture)

**Existing grading features folder:**

```text
apps/mobile/src/features/grading/
  pending-capture-store.ts              <- use as-is
  hooks/
    useImageQuality.ts                  <- use as-is
    useGradingJob.ts                    <- CREATE
    __tests__/useImageQuality.test.ts
    __tests__/useGradingJob.test.ts     <- CREATE
  components/
    CameraCapture.tsx                   <- use as-is
    GradingCard.tsx                     <- CREATE
    __tests__/GradingCard.test.tsx      <- CREATE
```

### Git Intelligence

Recent commits confirm: Epics 1-4 complete, Stories 5.1 and 5.2 done, codebase is Expo + TypeScript throughout. No mobile grading API service exists yet — this story creates it from scratch.

### Testing Standards

- Mobile: Jest + React Native Testing Library, configured via `babel-preset-expo` in `apps/mobile/babel.config.js`
- Test files: `__tests__/` folder co-located with source (see `useImageQuality.test.ts` for the hook test pattern to follow)
- Run mobile tests: `cd apps/mobile && pnpm test`
- Do NOT use `--coverage` during development (slow)
- Mock `global.fetch = jest.fn()` for all service tests (React Native test env has no fetch polyfill)
- Backend: pytest in `apps/api/tests/` — not affected by this story

### TypeScript Contracts Available

From `packages/contracts/src/grading.ts`:

```typescript
GradingJobResponse            // { job_id, artifact_id, assignment_id, status, attempt_count, submitted_at, completed_at }
GradingJobWithResultResponse  // extends GradingJobResponse + { result: AIGradingResultResponse | null, is_approved: boolean }
AIGradingResultResponse       // { proposed_score, rubric_mapping, draft_feedback, generated_at, confidence_level, confidence_score, confidence_reason, practice_recommendations }
AIConfidenceLevel             // "high" | "medium" | "low"
AIGradingErrorCode            // "IMAGE_BLURRY" | "IMAGE_UNREADABLE" | "MODEL_TIMEOUT" | "MODEL_ERROR" | "RATE_LIMITED"
```

Import in mobile via: `import type { GradingJobResponse, GradingJobWithResultResponse } from '@ilm/contracts';`

### References

<!-- References use escaped underscores in __tests__ paths to avoid markdown bold formatting -->

- [Source: apps/api/app/domains/grading/schemas.py] — exact request body field names: `AssignmentCreateRequest { class_id, title }`, artifact upload uses Form field `student_id` + `file` (UploadFile), `GradingJobSubmitRequest { artifact_id }`
- [Source: apps/api/app/domains/grading/router.py] — all grading API endpoints with their exact URL patterns and response schemas
- [Source: apps/api/app/domains/grading/service.py] — `process_grading_job()` with 3-attempt retry logic (2s, 4s backoff), job state machine (pending → processing → completed/failed)
- [Source: apps/api/app/domains/grading/ai_provider.py] — `MockAIGradingProvider`, `AI_ERROR_CODES`, `AIGradingResponse` shape
- [Source: apps/api/app/domains/grading/repository.py#L189] — Seed data: `cls_demo_math_1`, `stu_demo_1`, `usr_student_1` (org_demo_1, teacher: usr_teacher_1)
- [Source: apps/mobile/app/(teacher)/camera.tsx] — `handleCaptureAccepted` hook point; `CaptureResult` import from CameraCapture component
- [Source: apps/mobile/src/features/grading/pending-capture-store.ts] — `PendingCapture` interface, `getPendingCapture()`, `clearPendingCapture()`
- [Source: apps/mobile/src/services/api-client.ts] — `apiRequest<T>`, `API_BASE_URL`, `ApiError`, `NetworkError`
- [Source: apps/mobile/src/services/token-storage.ts] — `getAuthData()` returns `AuthData | null` with `.token` field
- [Source: apps/mobile/src/services/image-compressor.ts] — `compressImage()`, `CompressedImage` interface (already called in CameraCapture before capture accepted)
- [Source: apps/mobile/src/components/CameraFab.tsx] — `CameraFabProps`, current `router.push` to camera
- [Source: packages/contracts/src/grading.ts] — TypeScript contract types
- [Source: apps/mobile/src/features/grading/hooks/\_\_tests\_\_/useImageQuality.test.ts] — Jest hook test pattern for mobile

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- Fixed `moduleNameMapper` in `apps/mobile/package.json` from `../packages/$1/src` to `../../packages/$1/src` — the original path resolved to `apps/packages/` which doesn't exist; the correct path from `apps/mobile` is two levels up to reach `packages/`
- Used `jest.spyOn(FormData.prototype, 'append')` to inspect FormData fields in tests instead of `_parts` (React Native test env FormData doesn't expose `_parts`)
- Used `colors.confidenceHigh/Medium/Low` from design-tokens directly — no fallback hex needed

### Completion Notes List

All 7 tasks implemented and verified. Story is pure mobile-side work — backend endpoints from 5.1/5.2 consumed as-is with no modifications.

Key implementation decisions:

- `grading-service.ts`: Uses raw `fetch()` with `FormData` for artifact upload (multipart), and plain `fetch()` with JSON for all other endpoints. `ApiError` class imported from `api-client.ts` (not `@ilm/contracts` which has an interface of the same name).
- `useGradingJob.ts`: Recursive `setTimeout` polling pattern as specified — avoids concurrent requests on slow networks. `clearPendingCapture()` called after successful `submitGradingJob` (not after poll completes) so the store is cleared even if user navigates away mid-poll.
- `GradingCard.tsx`: Confidence badge uses `colors.confidenceHigh/Medium/Low` tokens found in design-tokens — no hex fallbacks needed. Collapsible rubric section uses local `useState`.
- Tests: 24 new tests across 3 files; all 33 mobile tests pass (0 regressions).

### File List

**Created:**

- `apps/mobile/src/services/grading-service.ts`
- `apps/mobile/src/features/grading/hooks/useGradingJob.ts`
- `apps/mobile/src/features/grading/components/GradingCard.tsx`
- `apps/mobile/app/(teacher)/grading.tsx`
- `apps/mobile/src/services/__tests__/grading-service.test.ts`
- `apps/mobile/src/features/grading/hooks/__tests__/useGradingJob.test.ts`
- `apps/mobile/src/features/grading/components/__tests__/GradingCard.test.tsx`
- `apps/mobile/babel.config.js` — babel-preset-expo config required for Jest to compile mobile tests
- `packages/contracts/src/grading.ts` — TypeScript grading contract types (created in 5.1, consumed here)

**Modified:**

- `apps/mobile/app/(teacher)/camera.tsx` — added `useLocalSearchParams`, changed `handleCaptureAccepted` to `router.replace` to grading screen
- `apps/mobile/src/components/CameraFab.tsx` — added optional `classId`/`studentId` props with dev defaults
- `apps/mobile/app/(teacher)/_layout.tsx` — added `<Tabs.Screen name="grading" options={{ href: null }} />`
- `apps/mobile/package.json` — fixed `moduleNameMapper` path (`../packages` → `../../packages`)
- `apps/mobile/app.config.ts` — added `apiBaseUrl` to `extra` config for test env resolution
- `packages/contracts/src/index.ts` — re-exports grading contract types
