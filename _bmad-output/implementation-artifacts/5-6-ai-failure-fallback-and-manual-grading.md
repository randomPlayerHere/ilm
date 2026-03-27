# Story 5.6: AI Failure Fallback and Manual Grading

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a teacher,
I want clear options when AI grading fails so I can continue grading without interruption,
So that AI failures never create dead ends in my workflow.

## Acceptance Criteria

1. **Given** the AI grading attempt fails on first try
   **When** the system detects the failure
   **Then** the system automatically retries once (up to 2 total attempts) — handled by backend, `attempt_count` increments
   **And** the teacher sees a "Still processing..." indicator during retry (i.e., while `status === 'processing'` and `attempt_count > 1`)

2. **Given** AI grading fails after 2 attempts
   **When** the final failure is reported
   **Then** the GradingCard displays: "Couldn't analyze this one" with a human-readable reason (e.g., "Handwriting unclear in bottom section") sourced from `job.failure_reason`
   **And** two action buttons appear: "Retake Photo" and "Grade Manually"

3. **Given** the teacher taps "Grade Manually"
   **When** the manual grading view opens
   **Then** the original photo is displayed alongside a score input (0–100), a feedback text area, and rubric criteria listed for reference
   **And** all workflow context is preserved (student, assignment, class) — no data is lost
   **And** a "Submit Grade" button is available; on success, shows "Grade submitted ✓"

4. **Given** the teacher taps "Retake Photo"
   **When** the camera reopens
   **Then** the student and assignment context is preserved (`classId`, `studentId`, `assignmentId`)
   **And** the new photo replaces the failed one and triggers a fresh AI grading attempt using the existing `assignment_id` (no new assignment created)

## Tasks / Subtasks

- [x] Task 1: Update contracts with failure/manual grading types (AC: 1, 2, 3)
  - [x] Add `failure_code: AIGradingErrorCode | null` and `failure_reason: string | null` to `GradingJobResponse` in `packages/contracts/src/grading.ts` — required fields (always present; null when not failed)
  - [x] Add `rubric_criteria: { criterion: string; description: string | null }[]` to `GradingJobResponse` — required field (always present; empty array if assignment has no rubric)
  - [x] Add `ManualGradeResponse { job_id: string; score: string; feedback: string; grader_user_id: string; graded_at: string }` type
  - [x] Add `ManualGradeRequest { score: string; feedback: string }` type
  - [x] Do NOT change any existing contract fields — only additions
  - [x] **IMPORTANT:** Because these are required (non-optional) fields, all existing test factory objects typed as `GradingJobResponse` / `GradingJobWithResultResponse` must be updated — see Task 8 subtasks

- [ ] Task 2: Add `submitManualGrade` function to `grading-service.ts` (AC: 3)
  - [ ] `export async function submitManualGrade(assignmentId: string, jobId: string, score: string, feedback: string, token: string): Promise<ManualGradeResponse>`
  - [ ] `POST /grading/assignments/${assignmentId}/grading-jobs/${jobId}/manual-grade` with `{ score, feedback }`
  - [ ] Import `ManualGradeResponse` and `ManualGradeRequest` from `@ilm/contracts`
  - [ ] Follow identical error-handling shape as other functions in file: `const body = await response.json().catch(() => ({})); throw new ApiError(...)` on non-2xx

- [x] Task 3: Update `useGradingJob` hook to expose retry state and failure reason (AC: 1, 2, 4)
  - [ ] Add `retrying: boolean` to `GradingJobState` interface (default `false`)
  - [ ] In poll handler, when `job.status` is not `completed`/`failed` AND `job.attempt_count > 1`: `setState(s => ({...s, retrying: true}))` before rescheduling
  - [ ] Reset `retrying: false` in initial state setup (`status: 'uploading'`)
  - [ ] When `job.status === 'failed'`: use `job.failure_reason ?? "AI grading did not complete — please try again."` as the error string
  - [ ] Accept optional `assignmentId?: string` as third parameter; when provided, skip the `createAssignment` call and use the passed value directly
  - [ ] TypeScript will pick up the new required fields from `@ilm/contracts` automatically — no source changes needed in `useGradingJob.ts` itself beyond adding the `retrying` field and `assignmentId` param; **however**, the test file `useGradingJob.test.ts` must be updated (see Task 8)

- [x] Task 4: Create `useManualGrading.ts` hook (AC: 3)
  - [ ] Create `apps/mobile/src/features/grading/hooks/useManualGrading.ts`
  - [ ] Signature: `useManualGrading(result: GradingJobWithResultResponse | null): ManualGradingControls | null`
  - [ ] Returns `null` when `result` is `null`
  - [ ] Export interface: `ManualGradingControls { scoreValue: number; scoreInputText: string; feedbackValue: string; submitState: 'idle' | 'loading' | 'submitted' | 'error'; submitError: string | null; isSubmitting: boolean; isSubmitted: boolean; rubricCriteria: { criterion: string; description: string | null }[]; setScore: (raw: string) => void; setFeedback: (text: string) => void; increment: () => void; decrement: () => void; submit: () => void }`
  - [ ] `submit()` flow:
    1. Guard: if `submitState === 'loading'` or `submitState === 'submitted'` → no-op
    2. `setSubmitState('loading')`
    3. `const authData = await getAuthData()` — if null: set `submitError = "Session expired — please sign in again"`, `submitState = 'error'`, return
    4. Call `submitManualGrade(result.assignment_id, result.job_id, String(scoreValue), feedbackValue, authData.token)`
    5. On success: `setSubmitState('submitted')`
    6. On thrown error: `submitState = 'error'`, `submitError = err.message ?? "Grade submission failed"`
  - [ ] `isMountedRef` pattern MUST be applied — guard every post-`await` state update
  - [ ] `scoreValue` initialized to `0`, `scoreInputText` to `"0"`, `feedbackValue` to `""`
  - [ ] `increment()`: `Math.min(100, scoreValue + 1)`; `decrement()`: `Math.max(0, scoreValue - 1)`
  - [ ] `setScore(raw)`: parse raw, clamp to `[0, 100]`, update both `scoreInputText` and `scoreValue`; ignore `NaN` (keep last valid `scoreValue`)
  - [ ] `rubricCriteria`: taken directly from `result.rubric_criteria` (the new field)

- [x] Task 5: Update `GradingCard.tsx` to handle fallback UI (AC: 1, 2, 3)
  - [ ] Add new optional props to `GradingCardProps`: `processingHint?: string | null`, `onRetakePhoto?: () => void`, `onGradeManually?: () => void`, `manualGradingControls?: ManualGradingControls | null`
  - [ ] Import `ManualGradingControls` from `../hooks/useManualGrading`
  - [ ] **Processing state update (AC1)**: when `status === 'uploading' || 'processing'`, if `processingHint` is set, render a `<Text style={styles.processingHint}>{processingHint}</Text>` below the skeleton block
  - [ ] **Failed state update (AC2)**: when `status === 'failed'` AND `manualGradingControls` is `null`:
    - Keep existing "Couldn't analyze this one" title + error detail
    - Render action row below error when at least one callback is provided:
      - "Retake Photo" `Pressable` (outline style, `borderWidth: 1`, `borderColor: colors.primary`, `colors.primary` label text) — only if `onRetakePhoto` provided
      - "Grade Manually" `Pressable` (filled, `backgroundColor: colors.primary`, `colors.textInverse` label) — only if `onGradeManually` provided
      - Both buttons: min height 44px, `hitSlop={8}`, `accessibilityRole="button"`, proper `accessibilityLabel`
  - [ ] **Manual grading form (AC3)**: when `status === 'failed'` AND `manualGradingControls != null`:
    - Add a **separate** `const [manualRubricExpanded, setManualRubricExpanded] = useState(false)` state variable — do NOT reuse the existing `rubricExpanded` state (which belongs to the completed-state rubric breakdown and is in a different render branch)
    - Show heading: "Grade Manually" (style: `styles.manualHeading`)
    - Show original photo thumbnail if `photoUri` available (same 80×80 `Image` style as completed state) with "Student work" `accessibilityLabel`
    - Score edit row: identical `+/-` buttons and `TextInput` as review controls in completed state; `+` button `accessibilityLabel="Increase manual score"`, `-` button `accessibilityLabel="Decrease manual score"`, TextInput `accessibilityLabel="Manual score"`
    - Feedback `TextInput`: multiline, same style as `feedbackInput`, `accessibilityLabel="Manual feedback"`, placeholder "Enter feedback..."
    - Rubric criteria section (when `rubricCriteria.length > 0`): collapsible using `manualRubricExpanded` / `setManualRubricExpanded`; each row shows `criterion` + `description` (if any); toggle label "Rubric criteria ▼/▲"
    - Submit button: `accessibilityRole="button"`, `accessibilityLabel="Submit manual grade"`, disabled + "Submitting..." when `isSubmitting`, `backgroundColor: colors.primary`, min height 44px
    - On `isSubmitted === true`: replace submit button with `<Text style={styles.submittedText}>Grade submitted ✓</Text>` (green, `colors.success`)
    - `submitError` renders as inline `<Text style={styles.approvalErrorText}>` when set (reuse existing error style)
  - [ ] **Do NOT touch** completed state rendering, approval block, rubric breakdown for completed state, or any existing 5.4/5.5 rendering paths

- [x] Task 6: Update `grading.tsx` to compose new hooks and handle navigation (AC: 1, 2, 3, 4)
  - [ ] Import `useManualGrading` and `ManualGradingControls` from hooks; import `useRouter` already present
  - [ ] Destructure `retrying` from `useGradingJob` return: `const { status: hookStatus, result, error: hookError, photoUri, retrying } = useGradingJob(classId ?? '', studentId ?? '', assignmentId)`
  - [ ] Add `assignmentId` to `useLocalSearchParams` destructure: `{ classId, studentId, batchIndex, batchTotal, assignmentId }` typed as `assignmentId?: string`
  - [ ] Compute `processingHint`: `const processingHint = status === 'processing' && retrying ? 'Still processing...' : null;`
  - [ ] Compose `useManualGrading`:
    ```typescript
    const manualGradingControls = useManualGrading(
      status === 'failed' && result != null ? result : null,
    );
    ```
  - [ ] Add `const [isManualGrading, setIsManualGrading] = useState(false)` at screen level (reset to false on result change — `useEffect([result?.job_id])`)
  - [ ] `handleGradeManually`: `() => setIsManualGrading(true)` — only enables when `status === 'failed'`
  - [ ] `handleRetakePhoto`: navigate to camera preserving context:
    ```typescript
    function handleRetakePhoto() {
      router.replace({
        pathname: '/(teacher)/camera',
        params: { classId: classId ?? '', studentId: studentId ?? '', assignmentId: result?.assignment_id ?? '' },
      });
    }
    ```
  - [ ] Pass to `GradingCard`:
    ```typescript
    <GradingCard
      status={status}
      result={result}
      photoUri={photoUri}
      error={error}
      reviewControls={reviewControls}
      approvalControls={approvalControls}
      processingHint={processingHint}
      onRetakePhoto={status === 'failed' && !isManualGrading ? handleRetakePhoto : undefined}
      onGradeManually={status === 'failed' && !isManualGrading ? handleGradeManually : undefined}
      manualGradingControls={isManualGrading ? manualGradingControls : null}
    />
    ```
  - [ ] Preserve ALL existing hook composition order and celebration/batch-complete logic unchanged

- [x] Task 7: Update `camera.tsx` to accept and forward `assignmentId` (AC: 4)
  - [ ] Add `assignmentId` to `useLocalSearchParams` destructure: `const { classId = 'cls_demo_math_1', studentId = 'stu_demo_1', assignmentId = '' } = useLocalSearchParams<{ classId?: string; studentId?: string; assignmentId?: string }>()`
  - [ ] Forward `assignmentId` in `handleCaptureAccepted`:
    ```typescript
    router.replace({
      pathname: '/(teacher)/grading',
      params: { classId, studentId, ...(assignmentId ? { assignmentId } : {}) },
    });
    ```
  - [ ] No other changes to camera.tsx

- [ ] Task 8: Tests (AC: 1, 2, 3, 4)
  - [ ] Create `apps/mobile/src/features/grading/hooks/__tests__/useManualGrading.test.ts`
    - Mock setup (exact paths, top of file):
      ```typescript
      jest.mock('../../../services/grading-service', () => ({ submitManualGrade: jest.fn() }));
      jest.mock('../../../services/token-storage', () => ({ getAuthData: jest.fn() }));
      ```
    - `makeResult(overrides?)` factory (failed job with assignment_id, job_id, rubric_criteria):
      ```typescript
      const makeResult = (overrides = {}) => ({
        job_id: 'job_1', assignment_id: 'asgn_1', artifact_id: 'art_1',
        status: 'failed', attempt_count: 2, submitted_at: '...', completed_at: '...',
        result: null, is_approved: false,
        failure_code: 'IMAGE_BLURRY', failure_reason: 'Handwriting unclear',
        rubric_criteria: [{ criterion: 'Clarity', description: 'Clear reasoning' }],
        ...overrides,
      });
      ```
    - Test: returns `null` when `result` is `null`
    - Test: initializes `scoreValue=0`, `feedbackValue=""`, `submitState='idle'`
    - Test: `rubricCriteria` comes from `result.rubric_criteria`
    - Test: `increment()` clamps to 100; `decrement()` clamps to 0
    - Test: `setScore('85')` sets `scoreValue=85` and `scoreInputText='85'`
    - Test: `setScore('')` keeps previous `scoreValue` unchanged (ignores NaN)
    - Test: `submit()` sets `isSubmitting=true` before API resolves
    - Test: calls `submitManualGrade` with `result.assignment_id`, `result.job_id`, `String(scoreValue)`, `feedbackValue`, token
    - Test: on success → `isSubmitted=true`, `submitState='submitted'`
    - Test: on API rejection → `submitState='error'`, `submitError` set to error message
    - Test: when `getAuthData()` returns null → `submitError = "Session expired — please sign in again"`, `submitManualGrade` NOT called
    - Test: `submit()` no-op when `submitState === 'submitted'`
    - Test: `submit()` no-op when `submitState === 'loading'`

  - [ ] Update `apps/mobile/src/features/grading/components/__tests__/GradingCard.test.tsx`
    - **Fix `COMPLETED_RESULT` factory:** add `failure_code: null, failure_reason: null, rubric_criteria: []` to satisfy the new required fields
    - Add `makeManualGradingControls(overrides?)` factory matching `ManualGradingControls` interface
    - **Processing hint tests:**
      - Test: "Still processing..." text renders when `status='processing'` and `processingHint='Still processing...'`
      - Test: no hint text when `processingHint` is null
    - **Failed state fallback buttons (no manualGradingControls):**
      - Test: "Retake Photo" button renders when `status='failed'` and `onRetakePhoto` provided
      - Test: "Grade Manually" button renders when `status='failed'` and `onGradeManually` provided
      - Test: neither button renders when callbacks are undefined
      - Test: tapping "Retake Photo" calls `onRetakePhoto`
      - Test: tapping "Grade Manually" calls `onGradeManually`
      - Test: failure reason `error` text still renders alongside buttons
    - **Manual grading form (manualGradingControls present):**
      - Test: "Grade Manually" heading renders
      - Test: score input renders with `scoreInputText` value
      - Test: `+` button (`accessibilityLabel="Increase manual score"`) calls `increment`; `-` button (`accessibilityLabel="Decrease manual score"`) calls `decrement`
      - Test: feedback input renders with `feedbackValue`
      - Test: feedback input change calls `setFeedback`
      - Test: rubric criteria section renders when `rubricCriteria.length > 0`; hidden when empty
      - Test: "Submit manual grade" button renders when `isSubmitted=false`
      - Test: "Submitting..." text and button disabled when `isSubmitting=true`
      - Test: "Grade submitted ✓" text renders when `isSubmitted=true`; submit button absent
      - Test: `submitError` text renders when set
      - Test: "Retake Photo" / "Grade Manually" buttons do NOT render when `manualGradingControls` is present
    - Test: no regression on all existing 5.4/5.5 GradingCard tests

  - [ ] Update `apps/mobile/src/features/grading/hooks/__tests__/useGradeApproval.test.ts`
    - **Fix `makeResult` factory:** add `failure_code: null, failure_reason: null, rubric_criteria: []` to satisfy the new required fields (no logic changes needed)

  - [ ] Update `apps/mobile/src/features/grading/hooks/__tests__/useGradingJob.test.ts`
    - **Fix test factory objects** to include new required `GradingJobResponse` fields — add to `FAKE_JOB_RESPONSE`, `FAKE_COMPLETED_JOB`, `FAKE_FAILED_JOB`:
      ```typescript
      failure_code: null,
      failure_reason: null,
      rubric_criteria: [],
      ```
      For `FAKE_FAILED_JOB` use `failure_code: 'MODEL_ERROR', failure_reason: 'AI grading did not complete — please try again.'` to be realistic
    - **Fix existing `retrying` tests:** `mockUseGradingJob` is called with 3 args after Task 3 adds `assignmentId`; all existing `toHaveBeenCalledWith(classId, studentId)` assertions must be updated to `toHaveBeenCalledWith(classId, studentId, undefined)` (or the specific `assignmentId` value where applicable)
    - **New retrying state tests:**
      - Test: `retrying=false` in initial state
      - Test: `retrying=true` when poll response has `status='processing'` and `attempt_count=2`
      - Test: `retrying=false` (stays false) when poll response has `status='processing'` and `attempt_count=1`
      - Test: when `assignmentId` is provided, `createAssignment` is NOT called and the provided value is used as `assignment_id`

  - [ ] Update `apps/mobile/app/(teacher)/__tests__/grading.test.tsx`
    - **Fix contract factory objects:** update `COMPLETED_RESULT` (line 56) to add `failure_code: null, failure_reason: null, rubric_criteria: []`; update the inline `completedResult` object inside the second test similarly
    - **Fix existing `useGradingJob` call assertion:** update `expect(mockUseGradingJob).toHaveBeenCalledWith("", "")` → `expect(mockUseGradingJob).toHaveBeenCalledWith("", "", undefined)` (assignmentId is undefined when not in URL params)
    - Add mock for `useManualGrading` at top (alongside existing mocks):
      ```typescript
      const mockUseManualGrading = jest.fn();
      jest.mock('../../../src/features/grading/hooks/useManualGrading', () => ({
        useManualGrading: (...args: unknown[]) => mockUseManualGrading(...args),
      }));
      ```
    - Add `mockUseManualGrading.mockReset(); mockUseManualGrading.mockReturnValue(null);` to `beforeEach`
    - Test: when `status='failed'` and `result` is not null → `useManualGrading` called with `result`
    - Test: when `status='processing'` → `useManualGrading` called with `null`
    - Test: `processingHint='Still processing...'` passed to `GradingCard` when `retrying=true`
    - Test: `processingHint=null` passed when `status='processing'` and not retrying
    - Test: `onRetakePhoto` is defined in GradingCard props when `status='failed'` and `!isManualGrading`
    - Test: `onGradeManually` is defined in GradingCard props when `status='failed'` and `!isManualGrading`
    - Test: after `onGradeManually()` is called (simulate press via mockGradingCard props), `manualGradingControls` becomes the hook's return value in next render
    - Test: after `onRetakePhoto()` is called, `router.replace` is called with camera pathname + `{ classId, studentId, assignmentId }`
    - Test: `assignmentId` URL param forwarded to `useGradingJob` as third arg
    - Test: all existing 5.3/5.4/5.5 behaviors unchanged

## Dev Notes

### Story Continuity and Context

- Stories 5.1–5.5 complete: contract defined, camera capture, async pipeline, review card, grade approval
- Story 5.6 closes the failure gap: after AI fails, the teacher has two escape hatches (Retake or Manual)
- The backend already handles 2x retry internally (`attempt_count` reflects this); this story adds client-side awareness + UI

### Current Failed State (Before This Story)

`GradingCard` at `status='failed'` currently renders:
```tsx
<Text style={styles.errorTitle}>Couldn't analyze this one</Text>
{error ? <Text style={styles.errorDetail}>{error}</Text> : null}
```

This story adds "Retake Photo" + "Grade Manually" buttons below, and conditionally replaces the card content with a manual grading form when `manualGradingControls` is supplied.

### Retry Indicator Implementation — CRITICAL DETAIL

The backend handles AI retries internally. `GradingJobResponse.attempt_count` tracks how many AI attempts have been made. During processing:
- `attempt_count: 1` → first attempt (show normal skeleton)
- `attempt_count: 2` → retry in progress (show "Still processing...")

The hook sets `retrying: true` when it polls a processing job and sees `attempt_count > 1`. `grading.tsx` converts this to `processingHint: "Still processing..."`.

**Critically:** the skeleton in GradingCard for uploading/processing is unchanged. `processingHint` is a new text element rendered BELOW the skeleton block, only when set. Do not alter the skeleton animation or layout.

### Auth Token Pattern — CRITICAL (same as all prior hooks)

`useManualGrading` MUST call `getAuthData()` internally, never accept a token as a param:
```typescript
import { getAuthData } from "../../../services/token-storage";
const authData = await getAuthData();
if (!authData) {
  if (!isMountedRef.current) return;
  setSubmitError("Session expired — please sign in again");
  setSubmitState("error");
  return;
}
```

### Unmount Safety — CRITICAL (same pattern as prior hooks)

```typescript
const isMountedRef = useRef(true);
useEffect(() => { return () => { isMountedRef.current = false; }; }, []);
// Guard every post-await state update:
await submitManualGrade(...);
if (!isMountedRef.current) return;
```

> **Known limitation (pre-existing in all hooks):** In React Strict Mode (development), the cleanup fires on the first synthetic unmount but `isMountedRef.current` is never reset to `true` on remount — async flows started in the second mount will always bail at the first `isMountedRef.current` check. This is acceptable because: (a) tests suppress Strict Mode behavior; (b) production builds don't use Strict Mode double-invocation. Do not attempt to fix this pattern in this story — it would require a different approach (AbortController) and is out of scope.

### Retake Photo Navigation — CRITICAL

Retake reuses the EXISTING `assignment_id` to avoid creating a duplicate assignment:

1. `grading.tsx` calls `router.replace({ pathname: '/(teacher)/camera', params: { classId, studentId, assignmentId: result?.assignment_id ?? '' } })`
2. `camera.tsx` receives `assignmentId` from params and forwards it to grading route on capture accept
3. `grading.tsx` passes `assignmentId` to `useGradingJob` as third parameter
4. `useGradingJob` skips `createAssignment()` when `assignmentId` is provided; starts directly at the upload step

**In `useGradingJob`:**
```typescript
export function useGradingJob(classId: string, studentId: string, assignmentId?: string): GradingJobState {
  // ...
  // Step 3 becomes:
  const assignment_id = assignmentId ?? (await createAssignment(classId, title, token)).assignment_id;
}
```

**In `grading.tsx`:**
```typescript
const { classId, studentId, batchIndex, batchTotal, assignmentId } = useLocalSearchParams<{
  classId?: string; studentId?: string; batchIndex?: string; batchTotal?: string; assignmentId?: string;
}>();
const { status: hookStatus, result, error: hookError, photoUri, retrying } = useGradingJob(
  classId ?? '',
  studentId ?? '',
  assignmentId,  // may be undefined for fresh grading sessions
);
```

### Backend Endpoint: Manual Grade Submission

The backend needs a new endpoint (NOT yet implemented — this story drives its contract):
```http
POST /v1/grading/assignments/{assignment_id}/grading-jobs/{job_id}/manual-grade
Authorization: Bearer <token>
Content-Type: application/json

{ "score": "85", "feedback": "Clear understanding demonstrated." }

→ 200 ManualGradeResponse { job_id, score, feedback, grader_user_id, graded_at }
→ 400 BAD REQUEST (score out of range or missing)
→ 403 FORBIDDEN (teacher role required)
→ 404 NOT FOUND (job not found)
→ 409 CONFLICT (already graded — treat as success; same pattern as 409 in approveGradingJob)
```

- This endpoint is NOT an extension of `/approve` — it handles failed jobs specifically
- Backend should set `is_approved: true` and populate `teacher_score`/`teacher_feedback` in the grades table
- `score` field format: string representation of 0–100 integer (e.g. `"85"`) — same as `approved_score` in approval endpoint
- Handle 409 in `submitManualGrade` service function the same way as `approveGradingJob`: drain body and return `{} as ManualGradeResponse`

### Backend Contract Extension: GradingJobResponse

Add these fields to `packages/contracts/src/grading.ts` → `GradingJobResponse`:
```typescript
failure_code: AIGradingErrorCode | null;   // set when status === 'failed'; null otherwise
failure_reason: string | null;              // user-facing reason, e.g. "Handwriting unclear in bottom section"
rubric_criteria: { criterion: string; description: string | null }[];  // always present, empty if no rubric
```

These are additions only — no existing fields removed or renamed. Backend already has error codes per 5.1 contract definition.

### Manual Grading Form — Rubric Display

`rubric_criteria` comes from `result.rubric_criteria` (the new field on `GradingJobResponse`). Even when AI fails, the backend always populates `rubric_criteria` from the assignment's standards profile. The manual grading form lists these for teacher reference during manual scoring.

When `rubric_criteria` is empty (array length 0), the rubric section is hidden entirely — do not render an empty toggle.

### Score Format Consistency

Same convention as 5.5 approval:
- `useManualGrading` stores `scoreValue: number` (0–100 integer)
- Service function receives `String(scoreValue)` → e.g. `"85"`
- `ManualGradeRequest.score` is `string` — same type as `ManualGradeResponse.score`

### isManualGrading State Scoping in grading.tsx

`isManualGrading` is screen-level state. Reset it to `false` when `result?.job_id` changes (new job loaded):
```typescript
useEffect(() => {
  setIsManualGrading(false);
}, [result?.job_id]);
```

This prevents the manual form from persisting across retake-and-new-job cycles.

> **Note:** Do NOT add an `isRetaking` state variable. The retake flow navigates away immediately via `router.replace` — no local retaking state is needed.

### GradingCard Prop Conditionals — Avoid Prop Drilling Confusion

The props `onRetakePhoto` and `onGradeManually` are passed as `undefined` (not `null`) when not applicable. Use existence check:
```tsx
{(onRetakePhoto || onGradeManually) ? (
  <View style={styles.failedActions}>
    {onRetakePhoto ? <Pressable ...>Retake Photo</Pressable> : null}
    {onGradeManually ? <Pressable ...>Grade Manually</Pressable> : null}
  </View>
) : null}
```

This preserves backward compatibility — existing failed state tests that don't pass these callbacks continue to pass unchanged.

### Existing Processing Skeleton — Do NOT Modify

The `SkeletonBox` shimmer animation and layout (skeletonRow, skeletonPhoto, skeletonTextColumn, etc.) are unchanged. `processingHint` is rendered as an additional element AFTER the skeleton block:
```tsx
if (status === "uploading" || status === "processing") {
  return (
    <View style={styles.card}>
      {/* ... existing skeleton blocks unchanged ... */}
      {processingHint ? (
        <Text style={styles.processingHint}>{processingHint}</Text>
      ) : null}
    </View>
  );
}
```

`processingHint` style: `fontSize: 13`, `fontFamily: fonts.body`, `color: colors.textSecondary`, `textAlign: 'center'`, `fontStyle: 'italic'`.

### Existing Failure Reason (Before vs. After)

**Before 5.6:**
- `useGradingJob` hardcodes: `error: "AI grading did not complete — please try again."`

**After 5.6:**
- `error: job.failure_reason ?? "AI grading did not complete — please try again."`
- Backend should populate `failure_reason` with human-readable text for each `AIGradingErrorCode`

### Not In Scope for Story 5.6

- **Offline queuing of manual grades**: queued photos are Epic 5.8
- **Push notifications on retry/failure**: Epic 8
- **Audit trail for manual grades**: Epic 11 (though the backend endpoint should log this internally)
- **Swipe-to-retake gesture**: deferred UX enhancement
- **Practice recommendations in manual grading**: Story 5.7 handles recommendations for successful AI grades; manual grades can skip recommendations for now

### Design Token Reference

```typescript
colors.primary          // "Grade Manually" button bg + "Retake Photo" border + score buttons
colors.textInverse      // "Grade Manually" button label
colors.textSecondary    // "Retake Photo" outline button label + processingHint text
colors.success          // "Grade submitted ✓" indicator
colors.error            // submitError inline text
colors.border           // feedback TextInput border
colors.borderFocus      // score TextInput bottom border
colors.surfaceSecondary // +/- score buttons bg (same as review controls in 5.4)
```

### File Structure Notes

**Create:**
- `apps/mobile/src/features/grading/hooks/useManualGrading.ts`
- `apps/mobile/src/features/grading/hooks/__tests__/useManualGrading.test.ts`

**Modify:**
- `packages/contracts/src/grading.ts` — add fields to `GradingJobResponse`, add `ManualGradeResponse`, `ManualGradeRequest`
- `apps/mobile/src/services/grading-service.ts` — add `submitManualGrade`
- `apps/mobile/src/features/grading/hooks/useGradingJob.ts` — add `retrying` state, `assignmentId` param, failure reason
- `apps/mobile/src/features/grading/components/GradingCard.tsx` — add fallback buttons, manual form, processing hint
- `apps/mobile/src/features/grading/components/__tests__/GradingCard.test.tsx` — new tests
- `apps/mobile/app/(teacher)/grading.tsx` — compose new hooks, handlers, pass new props
- `apps/mobile/app/(teacher)/__tests__/grading.test.tsx` — new tests
- `apps/mobile/app/(teacher)/camera.tsx` — accept + forward `assignmentId` param

**Do NOT touch:**
- `apps/mobile/src/features/grading/hooks/useGradingReview.ts`
- `apps/mobile/src/features/grading/hooks/useGradeApproval.ts`
- Camera capture components (`CameraCapture`, `useImageQuality.ts`, `pending-capture-store.ts`)
- `apps/api/` — backend implementation of `/manual-grade` is out of mobile scope (contract drives it)

### Testing Patterns — Carry Forward from 5.4/5.5

```typescript
// @testing-library/react-native v12 patterns:
getByRole('button', { name: 'Grade Manually' })  // prefer getByRole over getByText for buttons
getByRole('button', { name: 'Retake Photo' })
getByDisplayValue('0')                             // score input initial value
getByText('Grade submitted ✓')

// Wrap state updates in act():
import { act, renderHook } from "@testing-library/react-native";

// Animation suppression — all animations guarded by NODE_ENV !== 'test' already in existing code

// Import type in .tsx test files: use import type (not value import) for interfaces/types
// Run tests from apps/mobile/ directory: cd apps/mobile && npx jest
```

### Previous Story Intelligence (5.5)

- `useGradeApproval` hook composition pattern is the exact template for `useManualGrading` — copy isMountedRef, getAuthData(), optimistic/error state machine, return null when result is null
- `GradingCard` prop extension pattern: add optional props with `?` — existing tests that don't supply new props still pass without modification
- Score +/- UI: 44×44 style + `hitSlop={8}` for both review controls (5.4) and manual grading score (5.6)
- `accessibilityRole="button"` required on all Pressable elements; `accessibilityState={{ disabled }}` for loading states
- Animation guard pattern: `const shouldAnimate = process.env.NODE_ENV !== "test"` already in GradingCard — use same guard for any new animations
- `act(...)` wrapping required for all state updates in hook tests
- Jest mock paths must be relative from test file: `'../../../services/grading-service'` from hooks/__tests__/

### Git Intelligence Summary

- `da7426fb` — 5.4/5.5 shipped: three-hook orchestration established, GradingCard approval UI complete
- `5d86a6ad` — 5.1/5.2: AI grading contracts, AIGradingErrorCode type available in contracts
- `4c6da3e5` — 5.3: useGradingJob polling pipeline stable; this story modifies it — keep poll interval (2000ms) and 30-attempt timeout unchanged

### Definition of Done

- All 4 ACs implemented and test-covered
- `Still processing...` hint visible in GradingCard during processing when `retrying=true`
- Failed GradingCard shows "Couldn't analyze this one" + failure reason from backend + [Retake Photo] [Grade Manually]
- Manual grading form functional: photo, score ±, feedback, rubric criteria list, submit
- Manual grade submits to `POST .../manual-grade` endpoint; shows "Grade submitted ✓" on success
- Retake navigates to camera with `classId`, `studentId`, `assignmentId` preserved; camera forwards to grading; useGradingJob skips createAssignment
- 5.3/5.4/5.5 test suites pass unchanged
- No changes to `useGradingReview`, `useGradeApproval`, camera capture, or any non-5.6 hooks

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.6]
- [Source: _bmad-output/planning-artifacts/architecture.md#Error Handling Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Offline Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend Architecture]
- [Source: packages/contracts/src/grading.ts]
- [Source: apps/mobile/src/features/grading/hooks/useGradingJob.ts]
- [Source: apps/mobile/src/features/grading/hooks/useGradeApproval.ts — auth + isMountedRef template]
- [Source: apps/mobile/src/features/grading/hooks/useGradingReview.ts — score editing pattern]
- [Source: apps/mobile/src/services/grading-service.ts — service function pattern + 409 handling]
- [Source: apps/mobile/src/features/grading/components/GradingCard.tsx]
- [Source: apps/mobile/app/(teacher)/grading.tsx]
- [Source: apps/mobile/app/(teacher)/camera.tsx]
- [Source: _bmad-output/implementation-artifacts/5-5-grade-approval-and-visibility-control.md]
- [Source: _bmad-output/implementation-artifacts/5-5-grade-approval-and-visibility-control.md#Dev Notes]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- Story key: `5-6-ai-failure-fallback-and-manual-grading`
- `AIGradingErrorCode` confirmed in `packages/contracts/src/grading.ts` — not yet attached to `GradingJobResponse.failure_code`
- `attempt_count` confirmed on `GradingJobResponse` — poll sets `result: job` only on terminal states currently
- `camera.tsx` accepts `classId`/`studentId` params — `assignmentId` not yet forwarded
- `useGradingJob` hardcodes `createAssignment` — needs optional bypass for retake flow
- Manual grade endpoint `/manual-grade` does not yet exist in backend — contract defines it
- 5.5 409-handling pattern (`body?.cancel()`) applies to manual grade 409 as well

### Completion Notes List

- 2026-03-27: Pre-dev adversarial spec review completed (code-review workflow). 7 issues found and fixed directly in spec (2 HIGH, 3 MEDIUM, 2 LOW). No implementation exists yet — all tasks remain [ ]. Story ready for dev.
- 2026-03-27: Implementation cross-check completed against code and tests. Tasks 3–7 are implemented. Remaining open items: Task 2 import of `ManualGradeRequest` in `apps/mobile/src/services/grading-service.ts`, and Task 8 full regression confirmation (current failure in `GradingCard.test.tsx`: `toBeDisabled` matcher unavailable in this jest setup).

### File List
