# Story 5.7: Practice Recommendations

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a teacher,
I want AI-generated practice recommendations included with grading results,
So that I can share actionable next steps with students alongside their grades.

## Acceptance Criteria

1. **Given** AI grading completes successfully for an assignment
   **When** the GradingCard is displayed
   **Then** a "Recommended Practice" section appears below the rubric breakdown
   **And** it contains 1-3 specific, actionable practice suggestions based on the student's performance gaps

2. **Given** the teacher reviews practice recommendations
   **When** they want to modify a recommendation
   **Then** they can edit the recommendation text before approval
   **And** edited recommendations are marked as "Teacher modified" in the record

3. **Given** a grade is approved with practice recommendations
   **When** the approval is persisted
   **Then** the practice recommendations are stored alongside the grade record in the database
   **And** the recommendations are retrievable via the student progress API for downstream consumers (dashboards, tips views)

## Tasks / Subtasks

- [x] Task 1: Extend contracts with practice recommendation approval fields (AC: 2, 3)
  - [x]In `packages/contracts/src/grading.ts`:
    - Extend `GradeApprovalRequest` (if it exists there) OR verify it's only in backend schemas — the mobile contract does NOT currently define `GradeApprovalRequest`; check and add to frontend `grading-service.ts` as inline body object only if needed
    - Extend `GradeApprovalResponse` to add `practice_recommendations: string[]` — required field (always present; empty array if none)
    - Add comment: `// Added in Story 5.7`
  - [x]Export from `packages/contracts/src/index.ts` if any new types are added (no new types expected — just field additions)
  - [x]**CRITICAL:** Because `GradeApprovalResponse` gets a new required field, ALL test factory objects typed as `GradeApprovalResponse` must be updated — see Task 7 subtasks

- [x] Task 2: Backend — extend approval to store practice recommendations (AC: 3)
  - [x]In `apps/api/app/domains/grading/schemas.py`:
    - Add `practice_recommendations: list[str] = []` to `GradeApprovalRequest` (optional with default `[]` so existing callers that don't send it still work)
    - Add `practice_recommendations: list[str]` to `GradeApprovalResponse`
  - [x]In `apps/api/app/domains/grading/service.py`:
    - Update `GradeApproval` dataclass/model to include `practice_recommendations: list[str]`
    - Update `approve_grading_job(...)` method signature: add `practice_recommendations: list[str] = []` parameter
    - Store `practice_recommendations` with the approval record
    - Return it in the `GradeApproval` domain object
  - [x]In `apps/api/app/domains/grading/router.py`:
    - In `_to_grade_approval_response`: add `practice_recommendations=approval.practice_recommendations`
    - In `approve_grading_job` handler: pass `practice_recommendations=payload.practice_recommendations` to `service.approve_grading_job`

- [x] Task 3: Mobile service — update `approveGradingJob` to send practice recommendations (AC: 3)
  - [x]In `apps/mobile/src/services/grading-service.ts`:
    - Update `approveGradingJob(assignmentId, jobId, approvedScore, approvedFeedback, token, practiceRecommendations?: string[])` — add optional sixth parameter
    - Include `practice_recommendations: practiceRecommendations ?? []` in the JSON body
    - Return type `GradeApprovalResponse` already covers the response (after contracts update in Task 1)
  - [x]Preserve ALL existing error-handling shape (`409` idempotent return, non-2xx throw `ApiError`)

- [x] Task 4: Create `usePracticeRecommendations.ts` hook (AC: 1, 2)
  - [x]Create `apps/mobile/src/features/grading/hooks/usePracticeRecommendations.ts`
  - [x]Signature: `usePracticeRecommendations(result: GradingJobWithResultResponse | null): PracticeRecommendationsControls | null`
  - [x]Returns `null` when `result` is `null` OR `result.result` is `null` OR `result.result.practice_recommendations.length === 0`
  - [x]Export interface:
    ```typescript
    export interface PracticeRecommendationsControls {
      recommendations: string[];          // current values (possibly edited)
      originalRecommendations: string[];  // AI originals for comparison
      modifiedIndices: Set<number>;       // which items differ from original
      editRecommendation: (index: number, text: string) => void;
      resetRecommendation: (index: number) => void;  // revert to AI original
    }
    ```
  - [x]Initialize `recommendations` from `result.result.practice_recommendations` (slice to max 3 items)
  - [x]Re-initialize when a new result arrives: key on `result.job_id` + `result.result.generated_at`
    (use same `initializedRefKeyRef` pattern as `useGradingReview`)
  - [x]`editRecommendation(index, text)`: update `recommendations[index]`, update `modifiedIndices`:
    - if `text === originalRecommendations[index]` → remove from `modifiedIndices`
    - else → add to `modifiedIndices`
  - [x]`resetRecommendation(index)`: restore original text, remove from `modifiedIndices`
  - [x]Slice AI recommendations to max 3: `result.result.practice_recommendations.slice(0, 3)`
  - [x]Use `useRef` for initialization key (NOT `useEffect` dependency on `recommendations` to avoid re-init loops)
  - [x]Use `useState` for `recommendations` and `modifiedIndices` (as `Set<number>`, copied on update for immutability)
  - [x]**No async operations** — this hook is pure local state management; no auth or API calls

- [x] Task 5: Update `useGradeApproval.ts` to forward practice recommendations (AC: 3)
  - [x]Update `useGradeApproval(result, reviewControls, practiceRecommendationsControls?)` — add optional third parameter `practiceRecommendationsControls: PracticeRecommendationsControls | null = null`
  - [x]In `approve` callback: pass `practiceRecommendationsControls?.recommendations ?? []` as the `practiceRecommendations` arg to `approveGradingJob`
  - [x]Import `PracticeRecommendationsControls` from `./usePracticeRecommendations`
  - [x]No other changes — preserve all existing approval logic, optimistic state, error handling, unmount safety

- [x] Task 6: Update `GradingCard.tsx` to show recommendations section (AC: 1, 2)
  - [x]Add new optional prop: `practiceRecommendationsControls?: PracticeRecommendationsControls | null`
  - [x]Import `PracticeRecommendationsControls` from `../hooks/usePracticeRecommendations`
  - [x]In completed state, **after the rubric breakdown section** (after the `rubric_mapping` collapsible block, before the closing `</View>`):
    ```tsx
    {practiceRecommendationsControls != null && practiceRecommendationsControls.recommendations.length > 0 ? (
      <View style={styles.recommendationsSection}>
        <Text style={styles.recommendationsHeading}>Recommended Practice</Text>
        {practiceRecommendationsControls.recommendations.map((rec, index) => (
          <View key={index} style={styles.recommendationRow}>
            <TextInput
              style={styles.recommendationInput}
              value={rec}
              onChangeText={(text) => practiceRecommendationsControls.editRecommendation(index, text)}
              multiline
              accessibilityLabel={`Practice recommendation ${index + 1}`}
            />
            {practiceRecommendationsControls.modifiedIndices.has(index) ? (
              <View style={styles.modifiedBadgeRow}>
                <Text style={styles.modifiedBadgeText}>Teacher modified</Text>
                <Pressable
                  onPress={() => practiceRecommendationsControls.resetRecommendation(index)}
                  accessibilityRole="button"
                  accessibilityLabel={`Reset recommendation ${index + 1} to AI original`}
                  hitSlop={8}
                >
                  <Text style={styles.resetText}>Undo</Text>
                </Pressable>
              </View>
            ) : null}
          </View>
        ))}
      </View>
    ) : null}
    ```
  - [x]Add required styles to `StyleSheet.create`:
    - `recommendationsSection`: `{ gap: 8 }`
    - `recommendationsHeading`: same font weight as `rubricToggleText` — `{ fontWeight: fontWeights.semibold, color: colors.textPrimary }`
    - `recommendationRow`: `{ gap: 4 }`
    - `recommendationInput`: same style as existing `feedbackInput` style (multiline text area look)
    - `modifiedBadgeRow`: `{ flexDirection: 'row', alignItems: 'center', gap: 8 }`
    - `modifiedBadgeText`: `{ fontSize: 11, color: colors.confidenceMedium, fontStyle: 'italic' }` (amber/medium color for "modified" marker)
    - `resetText`: `{ fontSize: 11, color: colors.primary }` (tappable undo link)
  - [x]**Do NOT touch** failed state rendering, manual grading form, approval block, or any 5.4/5.5/5.6 rendering paths

- [x] Task 7: Update `grading.tsx` to compose `usePracticeRecommendations` (AC: 1, 2, 3)
  - [x]Import `usePracticeRecommendations` from hooks
  - [x]Add: `const practiceRecommendationsControls = usePracticeRecommendations(result);`
    (after `useGradingReview`, before `useGradeApproval`)
  - [x]Update `useGradeApproval` call to pass `practiceRecommendationsControls` as third arg:
    ```typescript
    const approvalControls = useGradeApproval(result, reviewControls, practiceRecommendationsControls);
    ```
  - [x]Pass to `GradingCard`:
    ```typescript
    <GradingCard
      ...existingProps...
      practiceRecommendationsControls={status === 'completed' ? practiceRecommendationsControls : null}
    />
    ```
  - [x]Preserve ALL existing hook composition order, celebration/batch-complete logic, manual grading wiring

- [x] Task 8: Tests
  - [x]Create `apps/mobile/src/features/grading/hooks/__tests__/usePracticeRecommendations.test.ts`
    - `makeResult(overrides?)` factory (completed job with `result.practice_recommendations`):
      ```typescript
      const makeResult = (recs = ['Practice A', 'Practice B']) => ({
        job_id: 'job_1', assignment_id: 'asgn_1', artifact_id: 'art_1',
        status: 'completed', attempt_count: 1, submitted_at: '...', completed_at: '...',
        is_approved: false, failure_code: null, failure_reason: null,
        rubric_criteria: [],
        result: {
          proposed_score: '85', rubric_mapping: {}, draft_feedback: 'Good work',
          generated_at: '2026-03-28T00:00:00Z', confidence_level: 'high',
          confidence_score: 0.9, confidence_reason: null,
          practice_recommendations: recs,
        },
      });
      ```
    - Test: returns `null` when `result` is `null`
    - Test: returns `null` when `result.result` is `null`
    - Test: returns `null` when `result.result.practice_recommendations` is empty array
    - Test: initializes `recommendations` from `result.result.practice_recommendations` (up to 3)
    - Test: limits to max 3 recommendations even if AI returns more
    - Test: `modifiedIndices` is empty `Set` on initialization
    - Test: `editRecommendation(0, 'new text')` updates `recommendations[0]` and adds `0` to `modifiedIndices`
    - Test: `editRecommendation(0, originalText)` removes `0` from `modifiedIndices` (reverts to unmodified state)
    - Test: `resetRecommendation(0)` restores original text and removes `0` from `modifiedIndices`
    - Test: modifying index 1 does not affect index 0's modification state
    - Test: re-initializes when a new `result.job_id` arrives (state is reset to AI originals)
    - Test: `originalRecommendations` never changes after initialization (unaffected by edits)

  - [x]Update `apps/mobile/src/features/grading/hooks/__tests__/useGradeApproval.test.ts`
    - **Fix `GradeApprovalResponse` factory:** add `practice_recommendations: []` to all factory objects typed as `GradeApprovalResponse`
    - **Fix mock `approveGradingJob`** call assertions: update all `toHaveBeenCalledWith` assertions to include the new sixth argument (empty array `[]` when no recs controls provided)
    - Add test: when `practiceRecommendationsControls` is provided with `recommendations: ['Practice A']`, `approveGradingJob` is called with `['Practice A']` as sixth argument
    - Add test: when `practiceRecommendationsControls` is `null`, `approveGradingJob` is called with `[]` as sixth argument

  - [x]Update `apps/mobile/src/features/grading/components/__tests__/GradingCard.test.tsx`
    - **Fix `GradeApprovalResponse` factories** if present: add `practice_recommendations: []`
    - Add `makePracticeRecommendationsControls(overrides?)` factory matching `PracticeRecommendationsControls` interface
    - **New recommendation section tests:**
      - Test: `practiceRecommendationsControls` with non-empty `recommendations` renders "Recommended Practice" heading in completed state
      - Test: renders each recommendation text in a `TextInput`
      - Test: changing a `TextInput` calls `editRecommendation(index, text)`
      - Test: renders "Teacher modified" text when `modifiedIndices.has(index)` is true
      - Test: "Teacher modified" text does NOT render when index is not in `modifiedIndices`
      - Test: tapping the "Undo" Pressable calls `resetRecommendation(index)`
      - Test: `practiceRecommendationsControls=null` → no "Recommended Practice" section
      - Test: `practiceRecommendationsControls` with empty `recommendations` → no "Recommended Practice" section
    - Test: no regression on all existing 5.4/5.5/5.6 GradingCard tests

  - [x]Update `apps/mobile/app/(teacher)/__tests__/grading.test.tsx`
    - Add mock for `usePracticeRecommendations` alongside existing mocks:
      ```typescript
      const mockUsePracticeRecommendations = jest.fn();
      jest.mock('../../../src/features/grading/hooks/usePracticeRecommendations', () => ({
        usePracticeRecommendations: (...args: unknown[]) => mockUsePracticeRecommendations(...args),
      }));
      ```
    - Add `mockUsePracticeRecommendations.mockReset(); mockUsePracticeRecommendations.mockReturnValue(null);` to `beforeEach`
    - Test: when `status='completed'` and `result != null` → `usePracticeRecommendations` called with `result`
    - Test: when `status='processing'` → `practiceRecommendationsControls=null` passed to GradingCard
    - Test: when `status='completed'` → `practiceRecommendationsControls` passed to GradingCard (hook return value)
    - Test: all existing 5.3/5.4/5.5/5.6 behaviors unchanged

  - [x]Update backend tests `apps/api/tests/` for approval:
    - Add `practice_recommendations` to `GradeApprovalRequest` payloads (optional field, use empty list in most tests)
    - Verify `practice_recommendations` is returned in `GradeApprovalResponse`
    - Verify stored recommendations match what was sent (for approval tests)

## Dev Notes

### Architecture Overview

This story bridges the AI grading result to downstream consumers by making practice recommendations editable and persistent. The inline `practice_recommendations: string[]` field already exists in `AIGradingResultResponse` (contracts and backend) — this story wires it through the approval flow and surfaces it in the UI.

**Data flow:**
```
AI grading completes
  → job.result.practice_recommendations: string[] (0-3 items, already in contract)
  → usePracticeRecommendations hook extracts + makes editable
  → GradingCard shows editable "Recommended Practice" section (completed state only)
  → Teacher optionally edits (tracked as "modified")
  → On Approve: approveGradingJob called with recommendations in body
  → Backend stores them with approval record
  → Student progress API returns them to parent/student dashboards (downstream — Epic 7)
```

### Existing Contract Fields — CRITICAL (do not re-implement)

`AIGradingResultResponse` already has `practice_recommendations: string[]`:
```typescript
// packages/contracts/src/grading.ts (line 12)
export interface AIGradingResultResponse {
  // ...
  practice_recommendations: string[];  // ← ALREADY EXISTS, do not rename
}
```

The `GradeApprovalResponse` currently does NOT have `practice_recommendations` — this story adds it. The `GradeApprovalRequest` is only used as an inline body object in `approveGradingJob()` in `grading-service.ts` (not exported as a TypeScript type from contracts) — extend the call-site directly.

### Backend Schema Location

All backend domain schemas are in `apps/api/app/domains/grading/schemas.py`. The domain service objects are in `apps/api/app/domains/grading/service.py`. The router is in `apps/api/app/domains/grading/router.py`.

- `GradeApprovalRequest` in `schemas.py` has `extra="forbid"` — when adding `practice_recommendations`, use `practice_recommendations: list[str] = []` (with default) so existing tests/callers pass without modification
- The `approve_grading_job` service method stores to `InMemoryGradingRepository` — update the `GradeApproval` dataclass and `InMemoryGradingRepository._approvals` storage
- **DO NOT** touch any other endpoints or service methods

### Existing Hook Patterns — CRITICAL (follow exactly)

**Initialization key pattern** (from `useGradingReview.ts`):
```typescript
const initializedRefKeyRef = useRef<string | null>(null);
// In useEffect:
const initKey = `${result.job_id}:${aiResult.generated_at}`;
if (initializedRefKeyRef.current === initKey) return;
initializedRefKeyRef.current = initKey;
// ... initialize state
```
Apply the same pattern in `usePracticeRecommendations` to avoid re-init on every render.

**Set immutability** — `Set` in React state requires creating a new Set on each update:
```typescript
const [modifiedIndices, setModifiedIndices] = useState<Set<number>>(new Set());
// On edit:
setModifiedIndices(prev => {
  const next = new Set(prev);
  if (text === originalRecommendations[index]) next.delete(index);
  else next.add(index);
  return next;
});
```

**No async / no isMountedRef needed** — `usePracticeRecommendations` is pure local state. No async operations, no token access, no unmount guard needed. Contrast with `useManualGrading` which does need `isMountedRef`.

### GradingCard Completed State — Insertion Point

Current completed state structure (after rubric breakdown):
```tsx
// Line ~373 in GradingCard.tsx:
{rubric_mapping && Object.keys(rubric_mapping).length > 0 ? (
  <View style={styles.rubricSection}>
    ...rubric toggle...
  </View>
) : null}
{/* ← INSERT recommendations section HERE, before closing </View> of card */}
</View>
```
This is INSIDE the completed-state return block. The card uses a single `<View style={styles.card}>` wrapping everything. Insert recommendations after the rubric section, inside that wrapper.

### useGradeApproval Signature Change — CRITICAL

The `useGradeApproval` hook signature changes from:
```typescript
export function useGradeApproval(
  result: GradingJobWithResultResponse | null,
  reviewControls: GradingReviewControls | null,
): GradeApprovalControls | null
```
To:
```typescript
export function useGradeApproval(
  result: GradingJobWithResultResponse | null,
  reviewControls: GradingReviewControls | null,
  practiceRecommendationsControls?: PracticeRecommendationsControls | null,
): GradeApprovalControls | null
```

In `grading.tsx`, all existing call sites pass only 2 args — the third arg is new and optional, so existing call sites compile without change (TypeScript optional parameter).

### grading-service.ts — `approveGradingJob` Change

Current call:
```typescript
export async function approveGradingJob(
  assignmentId: string, jobId: string,
  approvedScore: string, approvedFeedback: string, token: string,
): Promise<GradeApprovalResponse>
```

New call (add optional 6th parameter):
```typescript
export async function approveGradingJob(
  assignmentId: string, jobId: string,
  approvedScore: string, approvedFeedback: string, token: string,
  practiceRecommendations: string[] = [],
): Promise<GradeApprovalResponse>
```

Body becomes:
```typescript
body: JSON.stringify({ approved_score: approvedScore, approved_feedback: approvedFeedback, practice_recommendations: practiceRecommendations }),
```

The `409` idempotent pattern and `ApiError` throw must be preserved identically.

### Project Structure Notes

- New hook: `apps/mobile/src/features/grading/hooks/usePracticeRecommendations.ts`
- New hook test: `apps/mobile/src/features/grading/hooks/__tests__/usePracticeRecommendations.test.ts`
- All other changes are modifications to existing files
- No new screen files, no new route files

### Design Token Reference (Tamagui)

GradingCard uses `@ilm/design-tokens`:
```typescript
import { colors, fonts, fontWeights, radii } from "@ilm/design-tokens";
```
- Existing styles use `colors.surface`, `colors.border`, `colors.textPrimary`, `colors.primary`, `colors.textInverse`, `colors.confidenceMedium` (amber), `colors.success`
- For "Teacher modified" badge: use `colors.confidenceMedium` (amber — same as medium confidence badge)
- For undo link: use `colors.primary`
- Recommendation input: reuse `styles.feedbackInput` style (already defined in GradingCard)

### References

- Contracts grading types: [packages/contracts/src/grading.ts](packages/contracts/src/grading.ts)
- Contracts index: [packages/contracts/src/index.ts](packages/contracts/src/index.ts)
- Grading service: [apps/mobile/src/services/grading-service.ts](apps/mobile/src/services/grading-service.ts)
- Grade approval hook: [apps/mobile/src/features/grading/hooks/useGradeApproval.ts](apps/mobile/src/features/grading/hooks/useGradeApproval.ts)
- Review hook (initialization pattern): [apps/mobile/src/features/grading/hooks/useGradingReview.ts](apps/mobile/src/features/grading/hooks/useGradingReview.ts)
- GradingCard component: [apps/mobile/src/features/grading/components/GradingCard.tsx](apps/mobile/src/features/grading/components/GradingCard.tsx)
- Grading screen: [apps/mobile/app/(teacher)/grading.tsx](apps/mobile/app/(teacher)/grading.tsx)
- Backend schemas: [apps/api/app/domains/grading/schemas.py](apps/api/app/domains/grading/schemas.py)
- Backend service: [apps/api/app/domains/grading/service.py](apps/api/app/domains/grading/service.py)
- Backend router: [apps/api/app/domains/grading/router.py](apps/api/app/domains/grading/router.py)
- Previous story (5.6): [_bmad-output/implementation-artifacts/5-6-ai-failure-fallback-and-manual-grading.md](_bmad-output/implementation-artifacts/5-6-ai-failure-fallback-and-manual-grading.md)

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- All 8 tasks implemented + code review fixes applied. 169 mobile tests pass, 168 backend tests pass (no regressions).
- `usePracticeRecommendations` hook created with initialization key ref pattern (matches `useGradingReview`).
- `GradeApprovalResponse` extended with `practice_recommendations: string[]` in contracts and backend.
- Backend `GradeApprovalRequest` uses default `[]` for backward compatibility with existing callers.
- GradingCard completed-state UI renders editable recommendations with "Teacher modified" badge + Undo.
- **Post-review fixes (2026-03-28):**
  - ✅ Resolved review finding [HIGH]: `useGradeApproval` `approve` callback now includes `practiceRecommendationsControls` in `useCallback` deps — stale closure on recommendation edits eliminated.
  - ✅ Resolved review finding [HIGH]: `ApprovedGradeRecord` + `ApprovedGradeResponse` (progress) + `list_approved_grades_for_student` all extended with `practice_recommendations` — AC3 retrieval via progress API now satisfied.
  - ✅ Added stale-closure regression test in `useGradeApproval.test.ts` (rerenders with edited recs then approves — must send edited values).
  - ✅ Added backend regression test in `test_progress_api.py` (Test 32 — approves with recs, asserts grades endpoint returns them).

### File List

- `packages/contracts/src/grading.ts` — extend `GradeApprovalResponse` with `practice_recommendations: string[]`
- `packages/contracts/src/index.ts` — add `ManualGradeRequest`/`ManualGradeResponse` exports (carry-over from Story 5.6, landed in this diff)
- `apps/api/app/domains/grading/schemas.py` — add `practice_recommendations` to `GradeApprovalRequest` (with per-item max_length=500) and `GradeApprovalResponse`
- `apps/api/app/domains/grading/service.py` — update `GradeApproval` model and `approve_grading_job` method
- `apps/api/app/domains/grading/router.py` — pass `practice_recommendations` through in approval handler and response helper
- `apps/api/app/domains/grading/repository.py` — extend `ApprovedGradeRecord` with `practice_recommendations`; propagate in `list_approved_grades_for_student`
- `apps/api/app/domains/progress/schemas.py` — add `practice_recommendations: list[str]` to `ApprovedGradeResponse`
- `apps/api/app/domains/progress/router.py` — map `practice_recommendations` into `ApprovedGradeResponse`
- `apps/api/tests/test_progress_api.py` — Test 32: approved recs retrievable from student progress grades endpoint
- `apps/mobile/src/services/grading-service.ts` — add optional `practiceRecommendations` param to `approveGradingJob`; fix 409 return to include `practice_recommendations: []`
- `apps/mobile/src/features/grading/hooks/usePracticeRecommendations.ts` — new file
- `apps/mobile/src/features/grading/hooks/__tests__/usePracticeRecommendations.test.ts` — new file
- `apps/mobile/src/features/grading/hooks/useGradeApproval.ts` — add optional third param; add `practiceRecommendationsControls` to `useCallback` deps
- `apps/mobile/src/features/grading/hooks/__tests__/useGradeApproval.test.ts` — update factories + assertions; add stale-closure regression test
- `apps/mobile/src/features/grading/components/GradingCard.tsx` — add `practiceRecommendationsControls` prop + recommendations section; fix `key` on recommendation rows
- `apps/mobile/src/features/grading/components/__tests__/GradingCard.test.tsx` — add recommendation tests
- `apps/mobile/app/(teacher)/grading.tsx` — compose `usePracticeRecommendations`, wire to card + approval
- `apps/mobile/app/(teacher)/__tests__/grading.test.tsx` — add mock + tests for recommendations wiring
- `apps/mobile/src/features/grading/hooks/useGradingJob.ts` — carry-over from Story 5.6: removed stale retry-count logic; add `retrying: false` to failed-state transitions
- `apps/mobile/src/features/grading/hooks/useManualGrading.ts` — carry-over from Story 5.6: fix score input text to reflect clamped value; remove unused `ManualGradeResponse` import
- `apps/mobile/src/features/grading/hooks/__tests__/useGradingJob.test.ts` — carry-over from Story 5.6: add `flushRun` helper and act() warning suppression
- `apps/mobile/src/features/grading/hooks/__tests__/useGradingReview.test.ts` — carry-over from Story 5.6: updated test utilities
- `apps/mobile/src/features/grading/hooks/__tests__/useManualGrading.test.ts` — carry-over from Story 5.6: updated assertions for clamped score text
- `apps/mobile/src/features/grading/components/GradingCard.tsx` — add `practiceRecommendationsControls` prop + recommendations section
- `apps/mobile/src/features/grading/components/__tests__/GradingCard.test.tsx` — add recommendation tests
- `apps/mobile/app/(teacher)/grading.tsx` — compose `usePracticeRecommendations`, wire to card + approval
- `apps/mobile/app/(teacher)/__tests__/grading.test.tsx` — add mock + tests for recommendations wiring

## Senior Developer Review (AI)

**Reviewer:** GitHub Copilot (GPT-5.3-Codex)  
**Date:** 2026-03-28  
**Outcome:** Changes Requested

### Summary

- Mobile targeted tests pass (103/103) and mobile typecheck passes.
- Backend grading tests could not be executed in this environment due missing Python deps (`httpx` import error during collection).
- Two AC-impacting gaps remain in the implementation.

### Validation Run

- `cd apps/mobile && pnpm test -- useGradeApproval.test.ts usePracticeRecommendations.test.ts grading.test.tsx GradingCard.test.tsx` ✅
- `cd apps/mobile && pnpm typecheck` ✅
- `cd apps/api && pytest -q tests/test_grading_api.py tests/test_grading_service.py` ❌ (`ModuleNotFoundError: No module named 'httpx'`)

### Findings

#### HIGH

1. Approval can submit stale recommendations because `approve` captures `practiceRecommendationsControls` but does not include it in the `useCallback` dependency list. If the teacher edits recommendations after initial render, the payload may still send older values.
  Evidence: [apps/mobile/src/features/grading/hooks/useGradeApproval.ts](apps/mobile/src/features/grading/hooks/useGradeApproval.ts#L62), [apps/mobile/src/features/grading/hooks/useGradeApproval.ts](apps/mobile/src/features/grading/hooks/useGradeApproval.ts#L77)

2. AC3 retrieval requirement is not met for student progress APIs: approved practice recommendations are persisted in grading approval records but not exposed by progress grade models/handlers. Current progress response shape includes score/feedback/version only.
  Evidence: [apps/api/app/domains/progress/schemas.py](apps/api/app/domains/progress/schemas.py#L6-L16), [apps/api/app/domains/progress/router.py](apps/api/app/domains/progress/router.py#L64-L74), [apps/api/app/domains/grading/repository.py](apps/api/app/domains/grading/repository.py#L141-L151)

### Review Follow-ups (AI)

- [x] Fix `useGradeApproval` callback dependencies so recommendation edits are always reflected in approval payload.
- [x] Extend progress API grade response (and underlying record mapping) to include approved `practice_recommendations` for downstream consumers.
- [x] Add regression tests:
  - [x] Hook test proving edited recommendations are what `approveGradingJob` receives.
  - [x] Progress API test asserting approved recommendations are retrievable from student progress endpoints.
