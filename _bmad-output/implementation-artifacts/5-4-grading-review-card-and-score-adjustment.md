# Story 5.4: Grading Review Card and Score Adjustment

Status: in-progress

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a teacher,
I want to review, modify, and refine AI-suggested grades with easy controls,
So that I maintain full control over final grades while benefiting from AI assistance.

## Acceptance Criteria

1. **Given** a GradingCard is displayed with AI suggestions
   **When** the teacher reviews the card
   **Then** they see the photo thumbnail, suggested score with +/- adjustment buttons, editable feedback text field, collapsible rubric breakdown by criterion, and confidence badge (green high / amber medium / red low)

2. **Given** the teacher wants to adjust the score
   **When** they tap +/- buttons or directly edit the score field
   **Then** the score updates immediately with no lag
  **And** score editing is normalized to an integer range `0..100`
  **And** the displayed score format is `NN/100`
  **And** rubric criterion labels/ratings remain unchanged while the card-level total reflects the edited score

3. **Given** the teacher wants to modify AI-generated feedback
   **When** they tap the feedback text area
   **Then** the text becomes editable with the keyboard appearing
   **And** the original AI suggestion is preserved (undo available)

4. **Given** the AI confidence is medium or low (amber/red badge)
   **When** the GradingCard is displayed
   **Then** a note appears: "AI is less certain about this one — please review carefully"
   **And** the review controls are identical (no reduced functionality)

5. **Given** the teacher uses review controls
   **When** they interact with score buttons, score input, feedback field, and undo action
   **Then** each control exposes accessibility role/label metadata
   **And** controls meet mobile touch-target expectations

6. **Given** Story 5.4 implementation is complete
   **When** existing Story 5.3 grading flows are exercised
   **Then** loading, processing, failure, and result-display behavior remains unchanged
   **And** no new routes or backend endpoints are required by this story

## Tasks / Subtasks

- [ ] Task 1: Refactor `GradingCard` for review-only editing controls (AC: 1, 2, 3, 4, 5)
  - [ ] Update `apps/mobile/src/features/grading/components/GradingCard.tsx` to support controlled score and feedback editing in completed state only
  - [ ] Add score controls: increment, decrement, direct edit input
  - [ ] Add feedback editing with undo-to-original AI feedback
  - [ ] Keep existing loading/failed/completed render states from Story 5.3 unchanged
  - [ ] Add medium/low confidence helper note under the badge with no control restrictions

- [ ] Task 2: Create local review-state hook (AC: 2, 3)
  - [ ] Create `apps/mobile/src/features/grading/hooks/useGradingReview.ts`
  - [ ] Initialize from `GradingJobWithResultResponse.result`
  - [ ] Normalize score to integer `0..100` and expose `displayScore` as `NN/100`
  - [ ] Keep rubric data immutable in this story; only card-level score display changes
  - [ ] Implement feedback edit + undo to original AI draft

- [ ] Task 3: Integrate review controls into grading screen (AC: 1, 2, 3, 4, 6)
  - [ ] Update `apps/mobile/app/(teacher)/grading.tsx` to compose `useGradingJob` + `useGradingReview`
  - [ ] Enable edit controls only when grading job status is `completed` and result is available
  - [ ] Preserve existing missing-param handling and `Done` navigation behavior
  - [ ] Do not add approval/publish actions in this story

- [ ] Task 4: Accessibility and UX hardening (AC: 5)
  - [ ] Ensure score +/- buttons, score input, feedback editor, and undo action have accessibility labels/roles
  - [ ] Ensure controls meet mobile touch-target requirements
  - [ ] Use only `@ilm/design-tokens` primitives

- [ ] Task 5: Automated tests and regression protection (AC: 1, 2, 3, 4, 5, 6)
  - [ ] Create `apps/mobile/src/features/grading/hooks/__tests__/useGradingReview.test.ts`
  - [ ] Update `apps/mobile/src/features/grading/components/__tests__/GradingCard.test.tsx` for edit mode behaviors
  - [ ] Update `apps/mobile/app/(teacher)/grading.tsx` tests if present, or add focused screen behavior tests
  - [ ] Run mobile tests and confirm no regressions in Story 5.3 loading/processing/failure/result behavior

## Hard Constraints

- Implement **only** grading review/edit behavior for the existing card.
- Do not add grade publication/visibility workflow logic in this story.
- Do not add new backend endpoints, routes, or screen-level workflow branches.
- Preserve existing 5.3 pipeline behavior and route contracts.
- Use existing design tokens only; do not hardcode new colors/fonts.

## Non-Goals

- Grade approval/publish state transitions.
- Parent/student visibility gating logic.
- Push notifications or digest behavior.
- Backend grading-domain behavior changes unless a blocker is proven.

## Dev Notes

### Story Continuity and Context

- Story 5.3 completed the async grading fetch/poll lifecycle and base result rendering.
- Story 5.4 should build directly on existing files, not re-implement pipeline logic.
- Keep the current orchestration split:
  - pipeline fetch/poll state in `useGradingJob`
  - review editing/approval state in a new `useGradingReview`

### Architecture Alignment

- Mobile stack remains Expo React Native + TypeScript + design tokens from `@ilm/design-tokens`.
- Keep strict teacher-in-the-loop behavior at the UI review/edit layer in this story.
- Do not introduce extra screens/flows; implement exactly inside the existing grading experience.

### Data Shape Rules (Review State)

- Source value: `result.proposed_score` (string from grading result).
- Local editable value: `scoreValue` as integer `0..100`.
- Display format: `displayScore = "${scoreValue}/100"`.
- Invalid manual input handling:
  - empty input -> temporary empty UI state allowed while typing
  - non-numeric input -> ignore and keep previous valid value
  - out-of-range input -> clamp to `0..100`
- Rubric behavior in this story:
  - criterion rows (`rubric_mapping`) remain read-only
  - only the card-level total score display reflects edits

### Implementation Guardrails

- Reuse existing `GradingCard` component and extend it; do not create a parallel card component.
- Keep the current confidence color mapping through design tokens:
  - `colors.confidenceHigh`
  - `colors.confidenceMedium`
  - `colors.confidenceLow`
- Avoid any new color constants in component files.
- Keep current error/loading states untouched to avoid regressions in 5.3 behavior.
- Preserve route and navigation patterns already used by teacher grading screen.
- No publish/approve API calls in Story 5.4 implementation.

### Data and State Rules

- Editable score should initialize from `result.proposed_score`.
- Preserve raw AI suggestion values in local state to support undo.
- Undo should restore only feedback to original AI draft (as required by AC); score undo is optional and out-of-scope.

### Testing Requirements Summary

- Hook tests must validate immediate score updates and feedback undo reliability.
- Component tests must validate controls render correctly only in completed state and confidence note behavior for medium/low.
- Existing tests from Story 5.3 should continue to pass unchanged.

### Do / Don't

Do:

- Extend existing `GradingCard` and grading screen flow.
- Keep edit logic local and deterministic.
- Maintain strict compatibility with 5.3 state transitions.

Don't:

- Add new endpoints, approval submit logic, or publish side effects.
- Add new screens/routes or alter camera->grading navigation contract.
- Introduce hardcoded style primitives outside design tokens.

### Previous Story Intelligence (5.3)

Useful learnings carried forward:

- Polling reliability was hardened in `useGradingJob` (timeouts, fatal 4xx handling).
- `ApiError` class source matters (`apps/mobile/src/services/api-client.ts`), avoid contract type name collision.
- Existing grading UI already supports result rendering and rubric expansion; 5.4 should layer editing behavior over this.

### Git Intelligence Summary

Recent commit context:

- `529ed520` — story 5.3 mobile grading pipeline shipped
- `4c6da3e5` — included backend + mobile related grading artifacts; indicates existing grading domain and contracts are available

Pattern implication:

- Continue in the same files for mobile grading flow; do not move grading UI out of current feature folder.

### Latest Tech Information

Dependency currency check from `apps/mobile` indicates major newer versions exist (Expo 55, React Native 0.84, Tamagui 2.0 RC), while project currently runs Expo 52 / RN 0.76 / Tamagui 1.144.

Guidance for this story:

- Do **not** perform dependency upgrades inside Story 5.4.
- Keep implementation compatible with current pinned versions to reduce regression risk in active grading flow.

### Definition of Done

- All ACs for review/edit behavior are implemented and test-covered.
- No backend changes required for Story 5.4.
- No new routes/screens introduced.
- Story 5.3 behaviors remain regression-free.
- Mobile test suite passes for touched grading files.

### Project Structure Notes

Create:

- `apps/mobile/src/features/grading/hooks/useGradingReview.ts`
- `apps/mobile/src/features/grading/hooks/__tests__/useGradingReview.test.ts`

Modify:

- `apps/mobile/src/features/grading/components/GradingCard.tsx`
- `apps/mobile/app/(teacher)/grading.tsx`
- `apps/mobile/src/features/grading/components/__tests__/GradingCard.test.tsx`

Do not modify for this story:

- backend grading domain behavior unless blocker discovered
- camera capture flow logic from 5.2/5.3

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.4: Grading Review Card and Score Adjustment]
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend Architecture]
- [Source: apps/mobile/src/features/grading/components/GradingCard.tsx]
- [Source: apps/mobile/app/(teacher)/grading.tsx]
- [Source: apps/mobile/src/features/grading/hooks/useGradingJob.ts]
- [Source: apps/mobile/src/services/grading-service.ts]
- [Source: apps/api/app/domains/grading/router.py]
- [Source: apps/api/app/domains/grading/schemas.py]
- [Source: packages/contracts/src/grading.ts]
- [Source: packages/design-tokens/src/colors.ts]

## Dev Agent Record

### Agent Model Used

GPT-5.3-Codex

### Debug Log References

- Create-story workflow executed with explicit story key input: `5-4-grading-review-card-and-score-adjustment`
- Source synthesis completed from epic, architecture, PRD, previous story artifact, and current codebase

### Completion Notes List

- Story file created with comprehensive implementation context and explicit guardrails.
- Story status is set to `ready-for-dev`.
- Sprint status tracking updated accordingly.

### File List

- _bmad-output/implementation-artifacts/5-4-grading-review-card-and-score-adjustment.md (created)
- _bmad-output/implementation-artifacts/sprint-status.yaml (updated)
