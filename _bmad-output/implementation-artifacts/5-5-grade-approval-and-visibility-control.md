# Story 5.5: Grade Approval and Visibility Control

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a teacher,
I want to explicitly approve grades before they become visible to parents and students,
So that no AI-suggested grade is shared without my review and consent.

## Acceptance Criteria

1. **Given** a teacher has reviewed and optionally adjusted a grade
   **When** they tap the "Approve" button
   **Then** the grade status transitions to "Published" (optimistic UI: immediately shows "Approved ✓")
   **And** a success animation plays (checkmark fade-in + card slides to "approved" state, 400ms) with haptic feedback (`Haptics.notificationAsync(NotificationFeedbackType.Success)`)
   **And** the next pending assignment auto-loads for continuous grading flow

2. **Given** a grade has NOT been approved by the teacher
   **When** a parent or student views their dashboard
   **Then** the unapproved grade is NOT visible in any form
   **And** no notification about this grade is sent to parents or students
   *(Note: Enforced by existing backend approval gate — `is_approved: boolean` on `GradingJobWithResultResponse`. Story 5.5 drives the approval transition; backend already blocks visibility pre-approval.)*

3. **Given** all assignments in a grading batch are approved
   **When** the last approval is submitted
   **Then** an "All caught up!" celebration view appears inline (within `grading.tsx`) with a summary:
   - number of grades approved
   - average score
   - time spent (tracked from screen mount to last approval)

4. **Given** a teacher approves a grade
   **When** the approval is persisted
   **Then** the approval record includes teacher identity, timestamp, original AI suggestion, and final approved values
   **And** this record is available for audit (Epic 11)
   *(Note: Backend persists this via `GradeApprovalResponse { approver_user_id, approved_at, approved_score, approved_feedback, version }`. Story 5.5 ensures correct values are sent from review state.)*

## Tasks / Subtasks

- [x] Task 1: Add `approveGradingJob` function to `grading-service.ts` (AC: 1, 4)
  - [x] Add `export async function approveGradingJob(assignmentId: string, jobId: string, approvedScore: string, approvedFeedback: string, token: string): Promise<GradeApprovalResponse>` to `apps/mobile/src/services/grading-service.ts`
  - [x] `POST /grading/assignments/${assignmentId}/grading-jobs/${jobId}/approve` with `{ approved_score: approvedScore, approved_feedback: approvedFeedback }`
  - [x] Return `GradeApprovalResponse` (already in `packages/contracts/src/grading.ts`)
  - [x] Throw `ApiError` on non-2xx, **except** 409: on `response.status === 409` return without throwing (treat as already-approved success)
  - [x] Follow identical error-handling shape as existing functions in the file (`const body = await response.json().catch(() => ({})); throw new ApiError(...)`)

- [x] Task 2: Create `useGradeApproval.ts` hook (AC: 1, 4)
  - [x] Create `apps/mobile/src/features/grading/hooks/useGradeApproval.ts`
  - [x] Signature: `useGradeApproval(result: GradingJobWithResultResponse | null, reviewControls: GradingReviewControls | null)` — **NO token parameter**; hook fetches token internally
  - [x] Imports: `import { getAuthData } from "../../../services/token-storage"` and `import { approveGradingJob } from "../../../services/grading-service"`
  - [x] Add `isMountedRef = useRef(true)` with cleanup `return () => { isMountedRef.current = false }` — guard every post-`await` state update with `if (!isMountedRef.current) return`
  - [x] State: `approvalState: 'idle' | 'loading' | 'approved' | 'error'`, `approvalError: string | null`
  - [x] `isApproved: boolean` — initialize from `result?.is_approved ?? false`; set `true` on optimistic update
  - [x] `isApproving: boolean` — derived: `approvalState === 'loading'`
  - [x] `approve()` function flow:
    1. Guard: if `result` is null or `reviewControls` is null → no-op
    2. Optimistic: set `approvalState = 'approved'`, `isApproved = true` immediately
    3. `const authData = await getAuthData()` — if null: rollback, set `approvalError = "Session expired — please sign in again"`, return
    4. Call `approveGradingJob(result.assignment_id, result.job_id, String(reviewControls.scoreValue), reviewControls.feedbackValue, authData.token)`
    5. On success (including 409 handled in service layer): keep `approvalState = 'approved'`
    6. On thrown error: rollback → `approvalState = 'error'`, `isApproved = false`, `approvalError = err.message ?? "Approval failed"`
  - [x] Return `null` when `result` is `null` (matches hook convention — `useGradingReview` does same)
  - [x] Export interface: `GradeApprovalControls { approve: () => void; isApproving: boolean; isApproved: boolean; approvalError: string | null }`

- [x] Task 3: Update `GradingCard.tsx` to add approval action (AC: 1)
  - [x] Extend `GradingCardProps` with `approvalControls?: GradeApprovalControls | null`
  - [x] Import `GradeApprovalControls` from `../hooks/useGradeApproval`
  - [x] When `reviewControls` AND `approvalControls` are both present, render below the feedback block:
    - `!isApproved`: "Approve" `Pressable`, `backgroundColor: colors.primary`, `colors.textInverse` label, min height 44px, `hitSlop={8}`, disabled + label "Approving..." when `isApproving`
    - `isApproved`: "Approved ✓" `Text` in `colors.success`, no button (use `Animated.timing` fade-in, 400ms, `useNativeDriver: true`, suppress with `process.env.NODE_ENV !== 'test'` guard)
    - `approvalError`: inline `Text` in `colors.error` below button when set
  - [x] `accessibilityRole="button"`, `accessibilityLabel="Approve grade"`, `accessibilityState={{ disabled: isApproving }}` on Approve button
  - [x] Do NOT change any existing review control rendering from Story 5.4

- [x] Task 4: Update `grading.tsx` to compose approval hook, haptics, and batch completion (AC: 1, 3)
  - [x] Import `useGradeApproval` and `GradeApprovalControls`; import `* as Haptics from "expo-haptics"` and `Platform`
  - [x] Add `startedAtRef = useRef(Date.now())` at screen level (top of component, not inside hook) — used for time-spent calculation
  - [x] Compose: `const approvalControls = useGradeApproval(status === 'completed' && result?.result != null ? result : null, reviewControls)`
  - [x] Pass `approvalControls` to `GradingCard`
  - [x] Add `const [batchComplete, setBatchComplete] = useState(false)` and `const [approvedScores, setApprovedScores] = useState<number[]>([])`
  - [x] Use `useEffect` watching `approvalControls?.isApproved`:
    - When transitions to `true`:
      - Fire `if (Platform.OS !== "web") Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success)`
      - Append current score to `approvedScores`
      - Parse `batchIndex`/`batchTotal` as integers (`parseInt(batchIndex ?? '', 10)`)
      - If `batchTotal` present AND `!isNaN(parsedIndex)` AND `!isNaN(parsedTotal)` AND `parsedIndex >= parsedTotal`: set `batchComplete = true`
      - Otherwise (not last in batch, or no batch params): call `router.back()` after a 600ms delay (allows success animation to complete before navigating — the class/queue screen manages what's next)
  - [x] **Celebration view** (render when `batchComplete === true`, replaces card content):
    - Full-screen `SafeAreaView` content
    - "All caught up! 🎉" heading in `colors.gold`
    - Summary: `{approvedScores.length} grades approved`, `Average: {Math.round(sum/count)}/100`, `Time: {elapsedMinutes}m`
    - Elapsed = `Math.round((Date.now() - startedAtRef.current) / 60000)`
    - "Done" `Pressable` → `router.back()`
  - [x] Preserve existing `batchHeader` display for non-complete states

- [x] Task 5: Tests (AC: 1, 2, 3, 4)
  - [x] Create `apps/mobile/src/features/grading/hooks/__tests__/useGradeApproval.test.ts`
    - Top of file mocks (exact paths required):

      ```typescript
      jest.mock('../../../services/grading-service', () => ({ approveGradingJob: jest.fn() }));
      jest.mock('../../../services/token-storage', () => ({ getAuthData: jest.fn() }));
      ```

    - Use `makeResult()` factory (same shape as in `useGradingReview.test.ts`) and `makeReviewControls()` stub
    - Test: returns `null` when `result` is `null`
    - Test: initializes `isApproved=true` when `result.is_approved=true`
    - Test: initializes `isApproved=false` when `result.is_approved=false`
    - Test: `approve()` is a no-op when `result` is `null`
    - Test: `approve()` sets `isApproved=true` optimistically before API resolves
    - Test: calls `approveGradingJob` with `result.assignment_id`, `result.job_id`, `String(scoreValue)`, `feedbackValue`, and token from `getAuthData`
    - Test: on API rejection, rollback — `isApproved=false`, `approvalError` set to error message
    - Test: when `getAuthData()` returns `null`, sets `approvalError = "Session expired — please sign in again"` and does NOT call `approveGradingJob`
  - [x] Update `apps/mobile/src/features/grading/components/__tests__/GradingCard.test.tsx`
    - Add `makeApprovalControls(overrides?)` factory: `{ approve: jest.fn(), isApproving: false, isApproved: false, approvalError: null, ...overrides }`
    - Test: "Approve" button renders when `reviewControls` + `approvalControls` both present and `!isApproved`
    - Test: "Approve" button does not render when `approvalControls` is null
    - Test: button is disabled and shows "Approving..." when `isApproving=true`
    - Test: "Approved ✓" text shown when `isApproved=true`; button absent
    - Test: `approvalError` text renders when set
    - Test: tapping Approve calls `approvalControls.approve`
    - Test: no regression on all existing 5.4 review control tests
  - [x] Update `apps/mobile/app/(teacher)/__tests__/grading.test.tsx`
    - Add mock for new hook at top (alongside existing mocks):

      ```typescript
      const mockUseGradeApproval = jest.fn();
      jest.mock('../../../src/features/grading/hooks/useGradeApproval', () => ({
        useGradeApproval: (...args: unknown[]) => mockUseGradeApproval(...args),
      }));
      ```

    - Add `mockUseGradeApproval.mockReset()` to `beforeEach`
    - Test: `approvalControls` passed to `GradingCard` from `useGradeApproval` return value
    - Test: celebration view renders when `approvalControls.isApproved=true` AND `batchIndex === batchTotal`
    - Test: no celebration when `batchIndex < batchTotal` (calls `router.back()` instead)
    - Test: no celebration when `batchTotal` is absent
    - Test: "Done" button in celebration calls `router.back()`
    - Test: all existing 5.3/5.4 behaviors unchanged (missing-params, processing, completed states)

  ### Review Follow-ups (AI)

  - [x] [AI-Review][HIGH] Set loading state during approval request so `isApproving` becomes true and duplicate taps are blocked — fixed: `setApprovalState("loading")` before API call, `setApprovalState("approved")` on success.
  - [x] [AI-Review][HIGH] Gate post-approval side effects on a true transition (`false -> true`) to avoid auto haptic/navigation/celebration on initial render for already-approved jobs — fixed: added `prevIsApprovedRef` with job-scoped baseline reset.
  - [x] [AI-Review][HIGH] Make 409 handling resilient to empty/non-JSON bodies and still treat it as idempotent success — fixed: `response.body?.cancel()` + return `{} as GradeApprovalResponse` instead of `response.json()`.
  - [x] [AI-Review][MEDIUM] Align UI behavior with task claim for disabled `Approving...` by wiring reachable loading lifecycle from hook to button — resolved by H1 fix above.
  - [x] [AI-Review][MEDIUM] Add tests for approval loading transition coverage — fixed: extended optimistic test to assert `isApproving=true` in flight and `isApproving=false` after resolve.
  - [x] [AI-Review][LOW] Remove or justify effect dependency suppression — fixed: introduced `scoreValueRef` (updated every render) to eliminate the only real stale closure risk; remaining excluded deps (`batchIndex`, `batchTotal`, `router`) are documented as stable for screen lifetime; eslint-disable retained with explanation comment.

  ### Review Follow-ups (AI) — Round 2

  - [x] [AI-Review][MEDIUM] GradingCard `approvedFadeAnim` flashes for already-approved cards on mount — fixed: initialize `approvedFadeAnim` to `1` when `approvalControls?.isApproved` is true on mount; track transitions via `prevIsApprovedRef` in GradingCard, animate only on false→true.
  - [x] [AI-Review][MEDIUM] Celebration summary shows session-scoped count instead of batch count — fixed: `totalApproved` uses `parsedTotalForDisplay` from `batchTotal` URL param when valid; average still uses `approvedScores` (session data).
  - [x] [AI-Review][MEDIUM] No test for hook re-initialization when job_id changes — fixed: added test "resets isApproved, approvalState, and approvalError when result job_id changes" to `useGradeApproval.test.ts`.
  - [x] [AI-Review][LOW] Vacuous no-op test for approve() when result is null — fixed: renamed test to clarify intent ("returns null when result is null — approve() is not available to callers").
  - [x] [AI-Review][LOW] GradingCard disabled-state assertion missing — fixed: added `toBeDisabled()` assertion to "Approve button is disabled" test.
  - [x] [AI-Review][LOW] `batchTotal=0` edge case triggers celebration — fixed: added `parsedTotal > 0` guard to batch-complete condition.
  - [x] [AI-Review][LOW] Redundant `isMountedRef.current = true` in useEffect — fixed: removed setter; `useRef(true)` already initializes to true.
  - [x] [AI-Review][LOW] `response.body?.cancel()` portability risk — fixed: wrapped in try-catch to absorb environments where Streams API cancel() may throw.

## Dev Notes

### Story Continuity and Context

- Story 5.4 delivered: `useGradingReview`, score +/- editing, feedback undo, all in `GradingCard`.
- Story 5.5 adds the approval action — the teacher's explicit sign-off that publishes the grade.
- Three-hook orchestration in `grading.tsx`:
  - `useGradingJob` — pipeline fetch/poll state (do not modify)
  - `useGradingReview` — local score/feedback editing state (do not modify)
  - `useGradeApproval` (new) — approval mutation state
- `GradingCard` receives all three via props.

### Auth Token Pattern — CRITICAL

**Hooks in this codebase NEVER accept tokens as parameters.** They call `getAuthData()` internally:

```typescript
// Pattern established in useGradingJob.ts
import { getAuthData } from "../../../services/token-storage";

const authData = await getAuthData();
if (!authData) {
  // handle session expired
  return;
}
const token = authData.token;
```

`getAuthData()` reads from platform-native secure store (expo-secure-store on native, localStorage on web). Returns `AuthData { token, role, homePath, email }` or `null`. The hook must handle the `null` case with `approvalError = "Session expired — please sign in again"`.

### Unmount Safety — CRITICAL

Any hook with async operations MUST use `isMountedRef`:

```typescript
const isMountedRef = useRef(true);
useEffect(() => {
  return () => { isMountedRef.current = false; };
}, []);

// Inside approve():
await approveGradingJob(...);
if (!isMountedRef.current) return;  // guard before every setState after await
```

This pattern is present in `useGradingJob.ts` and must be replicated in `useGradeApproval`.

### Auto-Advance After Approval — Navigation Decision

`grading.tsx` receives one `studentId` at a time. It does **not** have a list of pending student IDs. After approval:

- **If last in batch** (`batchTotal` present AND `parsedBatchIndex >= parsedBatchTotal`): show celebration inline.
- **In all other cases** (mid-batch or no batch): `router.back()` after 600ms delay. The class/queue screen manages the batch sequence and re-pushes the next grading route. This is the correct split of responsibility — do not try to push to a "next" student route from within the grading screen.

**Do NOT** attempt to `router.push` to a next grading route. `grading.tsx` does not know the next `studentId`.

### Backend Endpoint (ALREADY EXISTS — no backend changes needed)

```http
POST /v1/grading/assignments/{assignment_id}/grading-jobs/{job_id}/approve
Authorization: Bearer <token>
Content-Type: application/json

{ "approved_score": "85", "approved_feedback": "Good work on..." }

→ 200 GradeApprovalResponse { job_id, approved_score, approved_feedback, approver_user_id, approved_at, version }
→ 409 CONFLICT  (already approved — service layer returns without throwing; hook keeps isApproved=true)
→ 403 FORBIDDEN (teacher role required)
```

- `GradeApprovalResponse` already exported from `packages/contracts/src/grading.ts`.
- `is_approved: boolean` already on `GradingJobWithResultResponse`.

### 409 Handling (Idempotent Approval)

409 means the grade was already approved (e.g., duplicate tap). The correct outcome:

- Service layer: detect `response.status === 409`, return without throwing.
- Hook: optimistic state (`isApproved=true`, `approvalState='approved'`) was already set — no change needed.
- **Never rollback on 409.** Treating it as an error would flash a confusing "Approval failed" to the teacher for a grade that is actually approved.

### Existing Contract Types (do not duplicate)

```typescript
// packages/contracts/src/grading.ts — already present
export interface GradeApprovalResponse {
  job_id: string;
  approved_score: string;
  approved_feedback: string;
  approver_user_id: string;
  approved_at: string;
  version: number;
}

export interface GradingJobWithResultResponse extends GradingJobResponse {
  result: AIGradingResultResponse | null;
  is_approved: boolean;
  // job_id, assignment_id inherited from GradingJobResponse
}
```

### Animation Spec (UX Design)

From `ux-design-specification.md`:

| Action         | Animation                                            | Duration |
|----------------|------------------------------------------------------|----------|
| Grade approve  | Checkmark fade-in + card slides to "approved" state  | 400ms    |
| Batch progress | Progress bar width transition                        | 300ms    |

Implementation:

```typescript
// Suppress in test environment — established pattern from SkeletonBox
const shouldAnimate = process.env.NODE_ENV !== "test";
if (shouldAnimate) {
  Animated.timing(fadeAnim, { toValue: 1, duration: 400, useNativeDriver: true }).start();
}
```

Haptic type confirmed by UX spec: `Success (medium)` → `NotificationFeedbackType.Success`.

### Haptics Pattern

```typescript
import * as Haptics from "expo-haptics";
import { Platform } from "react-native";

// In grading.tsx, on approval:
if (Platform.OS !== "web") {
  Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
}
```

`expo-haptics ~14.0.1` installed. Pattern from `apps/mobile/src/components/CameraFab.tsx`.

### Score Format for Approval

- `reviewControls.scoreValue` is integer `0..100`.
- `GradeApprovalRequest.approved_score` is `string` (max 50 chars).
- Send: `String(reviewControls.scoreValue)` → e.g. `"85"`.

### Optimistic UI (Architecture Requirement)

> "Grade approval: optimistic 'Approved' state, rollback if server rejects."
> [Source: architecture.md#Offline Patterns]

Set `isApproved = true` / `approvalState = 'approved'` **immediately** on `approve()` call, before the API resolves. Rollback only on error (not on 409).

### Not In Scope for Story 5.5

- **Swipe-right quick approve**: The UX spec mentions "Swipe right → Quick approve (if previously reviewed)" — this is a grading-queue screen interaction, deferred to a later story.
- Parent/student visibility UI — Epic 7.
- Notification dispatch after approval — Epic 8.
- Audit log UI — Epic 11.

### Design Token Reference

```typescript
colors.primary          // Approve button background + heading
colors.textInverse      // Approve button label
colors.success          // "Approved ✓" indicator (#2D6A4F, same as primary)
colors.gold             // Celebration "All caught up!" accent
colors.error            // approvalError inline text
colors.surfaceSecondary // Used by existing score buttons (do not change)
```

### File Structure Notes

**Create:**

- `apps/mobile/src/features/grading/hooks/useGradeApproval.ts`
- `apps/mobile/src/features/grading/hooks/__tests__/useGradeApproval.test.ts`

**Modify:**

- `apps/mobile/src/services/grading-service.ts`
- `apps/mobile/src/features/grading/components/GradingCard.tsx`
- `apps/mobile/src/features/grading/components/__tests__/GradingCard.test.tsx`
- `apps/mobile/app/(teacher)/grading.tsx`
- `apps/mobile/app/(teacher)/__tests__/grading.test.tsx`

**Do NOT touch:**

- `packages/contracts/src/grading.ts` — all types present
- `apps/api/` — backend endpoint complete
- `useGradingJob.ts` / `useGradingReview.ts`
- Camera capture flow (`camera.tsx`, `useImageQuality.ts`, `pending-capture-store.ts`)

### Testing Patterns

**Mock setup for `useGradeApproval.test.ts`:**

```typescript
import { act, renderHook } from "@testing-library/react-native";
jest.mock('../../../services/grading-service', () => ({ approveGradingJob: jest.fn() }));
jest.mock('../../../services/token-storage', () => ({ getAuthData: jest.fn() }));

// Factory helpers
const makeResult = (overrides = {}) => ({ job_id: 'job_1', assignment_id: 'asgn_1', is_approved: false, result: { ... }, ...overrides });
const makeReviewControls = () => ({ scoreValue: 85, feedbackValue: 'Good work.', ... });
```

**Mock additions for `grading.test.tsx`:**

```typescript
const mockUseGradeApproval = jest.fn();
jest.mock('../../../src/features/grading/hooks/useGradeApproval', () => ({
  useGradeApproval: (...args: unknown[]) => mockUseGradeApproval(...args),
}));
// Add mockUseGradeApproval.mockReset() to beforeEach
```

**`makeApprovalControls` factory for `GradingCard.test.tsx`:**

```typescript
const makeApprovalControls = (overrides = {}) => ({
  approve: jest.fn(),
  isApproving: false,
  isApproved: false,
  approvalError: null,
  ...overrides,
});
```

General testing rules:

- `@testing-library/react-native v12`: use `getByRole` / `getByText`, NOT `getByAccessibilityLabel`.
- Wrap state updates in `act(...)`.
- Suppress animations via `process.env.NODE_ENV !== 'test'` pattern (already in `SkeletonBox`).

### Previous Story Intelligence (5.4)

- `useGradingReview` uses `useEffect` + `initKey` ref for re-initialization — apply same `initKey` pattern if `is_approved` can change across result updates.
- Score buttons: 44×44 style + `hitSlop={8}` — use same sizing for Approve button.
- Invalid `accessibilityRole="none"` caused AC5 failure in 5.4 review — use `accessibilityState={{ disabled }}` instead.
- 5.4 explicitly deferred: "Do not add approval/publish actions in this story" — this story is the direct continuation.
- 5.4 review finding: `act(...)` animation warnings → use `process.env.NODE_ENV !== 'test'` guard on all animations.

### Git Intelligence Summary

- `da7426fb` — 5.4 shipped: `useGradingReview`, `GradingCard` edit controls baseline
- `5d86a6ad` — 5.1/5.2: `GradeApprovalResponse` contract in place
- `4c6da3e5` — 5.3: `useGradingJob` polling pipeline stable

Continue in same files — do not move or restructure grading feature.

### Definition of Done

- All 4 ACs implemented and test-covered.
- `useGradeApproval` hook: correct auth via `getAuthData()`, optimistic update, isMountedRef guard, session-expired handling.
- Approve button functional in grading screen for completed, un-approved grades.
- Haptic + 400ms success animation on approval.
- Batch celebration renders when `batchTotal` present and last approval submitted.
- `router.back()` (delayed 600ms) used for mid-batch auto-advance.
- 5.3 and 5.4 test suites pass unchanged.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.5]
- [Source: _bmad-output/planning-artifacts/architecture.md#Offline Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend Architecture]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Animation + Haptics]
- [Source: packages/contracts/src/grading.ts]
- [Source: apps/mobile/src/features/grading/hooks/useGradingJob.ts — auth + isMountedRef pattern]
- [Source: apps/mobile/src/features/grading/hooks/useGradingReview.ts — hook composition]
- [Source: apps/mobile/src/services/grading-service.ts — service function pattern]
- [Source: apps/mobile/src/features/grading/components/GradingCard.tsx]
- [Source: apps/mobile/app/(teacher)/grading.tsx]
- [Source: apps/mobile/src/components/CameraFab.tsx — haptics pattern]
- [Source: packages/design-tokens/src/colors.ts]
- [Source: apps/api/app/domains/grading/router.py#approve_grading_job]
- [Source: apps/api/app/domains/grading/schemas.py#GradeApprovalRequest]
- [Source: _bmad-output/implementation-artifacts/5-4-grading-review-card-and-score-adjustment.md]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- Create-story: explicit key `5-5-grade-approval-and-visibility-control`
- Backend endpoint confirmed: `POST /approve`, `GET /approval` in `apps/api/app/domains/grading/router.py`
- `GradeApprovalResponse` confirmed in `packages/contracts/src/grading.ts`
- `is_approved: boolean` confirmed on `GradingJobWithResultResponse`
- `expo-haptics ~14.0.1` confirmed; pattern from `CameraFab.tsx`
- Auth pattern confirmed: `getAuthData()` from `token-storage` in `useGradingJob.ts:80`
- `isMountedRef` pattern confirmed from `useGradingJob.ts`
- Validate: fixed hook signature (removed token param), added isMountedRef guidance, clarified auto-advance as `router.back()`, added grading screen test mock, added UX animation spec, added test mock paths, clarified 409 state, added swipe-right out-of-scope note

### Completion Notes List

- Implemented all 4 ACs across Tasks 1–5. All 90 tests pass (zero regressions).
- `approveGradingJob` added to `grading-service.ts` with 409 idempotent handling (body?.cancel() + empty return instead of response.json()).
- `useGradeApproval` hook: `setApprovalState("loading")` sets isApproving=true during API call; `setApprovalState("approved")` on success; optimistic isApproved=true; isMountedRef guard; session-expired handling; getAuthData() pattern.
- `GradingCard` updated: Approve button (44px min-height, hitSlop=8), "Approved ✓" fade-in (400ms, suppressed in test env), inline approvalError.
- `grading.tsx` updated: `prevIsApprovedRef` gates side effects to false→true transitions only (prevents auto-haptics/navigation on already-approved mounts); `scoreValueRef` eliminates scoreValue stale closure; `startedAtRef`, haptics, 600ms router.back() for mid-batch, batch celebration view.
- Note: `import type` in `.tsx` test files fails when Jest is run from monorepo root; run from `apps/mobile/` or via `cd apps/mobile && npx jest`.
- Code review round 1 addressed (2026-03-27): 3 HIGH + 2 MEDIUM + 1 LOW findings resolved.
- Code review round 2 addressed (2026-03-27): 3 MEDIUM + 5 LOW findings resolved. Story promoted to done.

### File List

**Created:**

- `apps/mobile/src/features/grading/hooks/useGradeApproval.ts`
- `apps/mobile/src/features/grading/hooks/__tests__/useGradeApproval.test.ts`

**Modified:**

- `apps/mobile/src/services/grading-service.ts`
- `apps/mobile/src/features/grading/components/GradingCard.tsx`
- `apps/mobile/src/features/grading/components/__tests__/GradingCard.test.tsx`
- `apps/mobile/app/(teacher)/grading.tsx`
- `apps/mobile/app/(teacher)/__tests__/grading.test.tsx`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `_bmad-output/implementation-artifacts/5-5-grade-approval-and-visibility-control.md`
