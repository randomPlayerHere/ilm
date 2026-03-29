# Story 5.8: Offline Photo Queue and Auto-Upload

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a teacher,
I want to capture assignment photos even without internet connectivity,
So that I can grade in classrooms with poor or no Wi-Fi without interrupting my workflow.

## Acceptance Criteria

1. **Given** the device has no internet connectivity
   **When** the teacher captures an assignment photo
   **Then** the photo is saved to a local persistent queue with a "Pending" badge on the assignment card
   **And** the teacher can continue capturing additional photos for other students

2. **Given** photos are queued locally
   **When** internet connectivity is restored
   **Then** queued photos auto-upload in the order they were captured
   **And** AI grading jobs are triggered automatically for each uploaded photo
   **And** the teacher receives push notifications as AI results arrive (via existing polling once job is running)

3. **Given** a teacher has offline-queued photos
   **When** they view their grading queue
   **Then** pending uploads show a "Waiting for connection" status
   **And** the queue count is visible (e.g., "3 photos pending upload")

4. **Given** an upload fails after connectivity is restored
   **When** the retry mechanism activates
   **Then** the system retries with exponential backoff
   **And** after 3 failed attempts, shows "Upload failed — Tap to retry" on the specific item

## Tasks / Subtasks

- [x] Task 1: Create persistent offline queue service (AC: 1, 3, 4)
  - [x] Create `apps/mobile/src/services/offline-queue.ts`
  - [x] Define `OfflineQueueItem` interface
  - [x] Use `@react-native-async-storage/async-storage` for queue persistence (key: `offline_photo_queue`)
  - [x] Implement `addToOfflineQueue`, `getOfflineQueue`, `updateQueueItem`, `removeFromOfflineQueue`, `clearOfflineQueue`
  - [x] Copy compressed photo from temp URI to `FileSystem.documentDirectory + 'offline-photos/' + id + '.jpg'` using `expo-file-system`

- [x] Task 2: Add connectivity detection hook (AC: 1, 2)
  - [x] Create `apps/mobile/src/hooks/useNetworkStatus.ts`
  - [x] Returns `{ isConnected: boolean | null }`, subscribes via `NetInfo.addEventListener`, unsubscribes on unmount

- [x] Task 3: Modify `useGradingJob` to support offline queuing (AC: 1, 3)
  - [x] Added `'queued-offline'` to `GradingJobStatus`
  - [x] Added `queueItemId: string | null` to `GradingJobState`
  - [x] Calls `NetInfo.fetch()` after reading `pendingCapture`; routes offline to `addToOfflineQueue` + early return

- [x] Task 4: Create `useOfflineQueueProcessor` hook for auto-upload on reconnect (AC: 2, 3, 4)
  - [x] Create `apps/mobile/src/features/grading/hooks/useOfflineQueueProcessor.ts`
  - [x] Subscribes to `NetInfo.addEventListener`, processes queue FIFO on reconnect
  - [x] Exponential backoff, max 3 attempts, exposes `pendingCount`, `processingItemId`, `queueItems`, `retryItem`

- [x] Task 5: Custom event emitter for queue item completion (AC: 2)
  - [x] Create `apps/mobile/src/services/queue-events.ts` with `onQueueJobComplete` / `emitQueueJobComplete`

- [x] Task 6: Update contracts with offline queue types (AC: 3)
  - [x] Added `OfflineQueueItemStatus` to `packages/contracts/src/grading.ts` and exported from index

- [x] Task 7: Update grading screen UI for offline states (AC: 3, 4)
  - [x] `grading.tsx`: imports `useOfflineQueueProcessor`, renders pending count banner, wires retry, registers `onQueueJobComplete`
  - [x] `GradingCard.tsx`: handles `'queued-offline'` status with "Waiting for connection" / retry UI

- [x] Task 8: Tests
  - [x] `apps/mobile/src/services/__tests__/offline-queue.test.ts` — 18 tests (all passing)
  - [x] `apps/mobile/src/hooks/__tests__/useNetworkStatus.test.ts` — 6 tests (all passing)
  - [x] `apps/mobile/src/features/grading/hooks/__tests__/useOfflineQueueProcessor.test.ts` — 11 tests (all passing)
  - [x] `apps/mobile/src/features/grading/hooks/__tests__/useGradingJob.test.ts` — updated with 8 offline tests (all passing)
  - [x] `apps/mobile/app/(teacher)/__tests__/grading.test.tsx` — updated with offline UI tests (all passing)

## Dev Notes

### Architecture Overview

This story implements the offline-first photo capture pattern described in the architecture. The key design principle is to intercept the existing grading flow at the earliest possible point (after photo capture and compression) and divert to persistent local storage when offline. The existing upload/poll flow is unchanged for the online case.

**Data flow (offline):**
```
Teacher captures photo (online check)
  → Offline detected
  → expo-file-system: copy compressed photo to DocumentDirectory/offline-photos/<id>.jpg
  → AsyncStorage: append item to offline_photo_queue
  → useGradingJob state: 'queued-offline'
  → GradingCard: shows "Waiting for connection"
```

**Auto-upload flow (on reconnect):**
```
NetInfo detects connectivity restored
  → useOfflineQueueProcessor processes queue (FIFO)
  → grading-service: createAssignment → uploadArtifact → submitGradingJob
  → On success: removeFromOfflineQueue, emitQueueJobComplete(assignmentId, jobId)
  → grading.tsx: receives event, navigates back (router.back())
  → Push notification (server-side) informs teacher when AI result is ready
  Note: in-app polling resume is a future enhancement — useGradingJob has no resume-by-jobId path yet
```

### Critical Architecture Constraints

1. **Temp URIs expire** — React Native camera gives a temp URI in the cache directory. You MUST copy the file to `FileSystem.documentDirectory` before storing the path, or the file will be gone after app restart. Use `FileSystem.copyAsync({ from: tempUri, to: persistentPath })`.

2. **AsyncStorage is module-level singleton** — Import as:
   ```typescript
   import AsyncStorage from '@react-native-async-storage/async-storage';
   ```
   Store the full queue as a JSON-serialized array. Always read-modify-write atomically to avoid race conditions (the app will not multi-thread this in MVP).

3. **NetInfo initial state** — `NetInfo.fetch()` gives a one-shot connectivity check. `NetInfo.addEventListener` gives real-time updates. Use `fetch()` in `useGradingJob` for the initial check (synchronous decision point), and `addEventListener` in `useOfflineQueueProcessor` for reactive reconnect handling.

4. **Existing patterns to follow** — The `isMountedRef` pattern is used in `useGradingJob`, `useManualGrading`, and `useGradeApproval`. Use the same pattern in `useOfflineQueueProcessor`.

5. **DO NOT modify the happy-path flow** — `useGradingJob`'s online path (upload → submit → poll) must remain unchanged. The offline check is a pre-condition added at the top of `run()`.

### Existing File Locations

| File | Path |
|---|---|
| Grading service | `apps/mobile/src/services/grading-service.ts` |
| Pending capture store | `apps/mobile/src/features/grading/pending-capture-store.ts` |
| `useGradingJob` hook | `apps/mobile/src/features/grading/hooks/useGradingJob.ts` |
| Grading screen | `apps/mobile/app/(teacher)/grading.tsx` |
| GradingCard component | `apps/mobile/src/features/grading/components/GradingCard.tsx` |
| Contracts grading types | `packages/contracts/src/grading.ts` |
| Contracts index | `packages/contracts/src/index.ts` |

### New Files to Create

| File | Purpose |
|---|---|
| `apps/mobile/src/services/offline-queue.ts` | Persistent queue (AsyncStorage + FileSystem) |
| `apps/mobile/src/services/queue-events.ts` | Simple event emitter for job-ready events |
| `apps/mobile/src/hooks/useNetworkStatus.ts` | React hook wrapping NetInfo |
| `apps/mobile/src/features/grading/hooks/useOfflineQueueProcessor.ts` | Auto-upload on reconnect |

### Key Packages (Already in Expo SDK — no new `package.json` additions needed)

- `@react-native-async-storage/async-storage` — persistent key-value storage
- `@react-native-community/netinfo` — network connectivity detection
- `expo-file-system` — file system access for persisting photos beyond temp cache

All three are standard Expo dependencies. Verify they're in `apps/mobile/package.json` before assuming — if not present, add them. Do NOT use `expo-network` (deprecated API for connectivity).

### `GradingJobStatus` Extension — CRITICAL

Current type in `useGradingJob.ts`:
```typescript
export type GradingJobStatus = "idle" | "uploading" | "processing" | "completed" | "failed";
```

Extended type:
```typescript
export type GradingJobStatus = "idle" | "uploading" | "processing" | "completed" | "failed" | "queued-offline";
```

**ALL consumers of `GradingJobStatus` must be updated to handle the new value.** Check `grading.tsx` — it has `status` comparisons that drive UI rendering. Add an `else if (status === 'queued-offline')` branch showing the offline-pending state.

### `GradingJobState` Extension

Add `queueItemId: string | null` to the interface. Initialize as `null`. Set to the queue item's id when `status === 'queued-offline'`. This allows the grading screen to look up the specific queue item for retry UI.

### Exponential Backoff Pattern

```typescript
const delay = Math.pow(2, attemptCount) * 1000; // 2s, 4s, 8s
await new Promise(resolve => setTimeout(resolve, delay));
```

Cap at 3 attempts. After 3 failures, require manual user retry (tap to retry resets `attemptCount` to 0 and status to `'pending'`).

### Previous Story Intelligence (5.7)

From Story 5.7 completion notes:
- `useGradingJob.ts` was modified in 5.6 to remove stale retry-count logic and add `retrying: false` to failed-state transitions
- The `isMountedRef` pattern is battle-tested across all async hooks — follow it exactly
- `clearPendingCapture()` is called after successful upload in the existing flow — call it after queuing as well (photo is now in DocumentDirectory)
- Tests use `jest.fn()` mocks for all service imports — follow the same mock pattern

### Git Intelligence (Recent Commits)

- `c7905df4` — Story 5.6: manual grading (modified `useGradingJob`, `useManualGrading`, `GradingCard`)
- `ffc1d7dc` — Story 5.5: grade approval and visibility (established `useGradeApproval` approval patterns)
- `da7426fb` — Story 5.4: grading review card (established `useGradingReview` hook patterns)
- Branching: Feature work comes from `harshit-05/dev/harshit` via PRs to `main`

### Project Structure Notes

- New `hooks/` directory: `apps/mobile/src/hooks/` (not inside `features/grading/`) — `useNetworkStatus` is a general utility, not grading-specific
- New `services/` files: `offline-queue.ts` and `queue-events.ts` join existing service files
- `useOfflineQueueProcessor` lives in `apps/mobile/src/features/grading/hooks/` — it is grading-specific
- Do NOT create new route files or screens — offline state is handled inline within existing grading screen

### Design Token Reference (Tamagui)

For offline-state UI in `GradingCard`:
```typescript
import { colors, fonts, fontWeights, radii } from "@ilm/design-tokens";
```
- "Waiting for connection" badge: `colors.confidenceMedium` (amber — same as medium confidence)
- "Upload failed" state: `colors.error` (if available) or a red-adjacent color
- Use existing badge styles from Story 5.3/5.4 confidence badge as a reference

### References

- Offline patterns specification: [_bmad-output/planning-artifacts/architecture.md](_bmad-output/planning-artifacts/architecture.md) — "Offline Patterns" section
- Architecture data flow: [_bmad-output/planning-artifacts/architecture.md](_bmad-output/planning-artifacts/architecture.md) — "Data Flow" section
- Epic 5 story spec: [_bmad-output/planning-artifacts/epics.md](_bmad-output/planning-artifacts/epics.md)
- Grading service: [apps/mobile/src/services/grading-service.ts](apps/mobile/src/services/grading-service.ts)
- Grading job hook: [apps/mobile/src/features/grading/hooks/useGradingJob.ts](apps/mobile/src/features/grading/hooks/useGradingJob.ts)
- Pending capture store: [apps/mobile/src/features/grading/pending-capture-store.ts](apps/mobile/src/features/grading/pending-capture-store.ts)
- GradingCard component: [apps/mobile/src/features/grading/components/GradingCard.tsx](apps/mobile/src/features/grading/components/GradingCard.tsx)
- Grading screen: [apps/mobile/app/(teacher)/grading.tsx](apps/mobile/app/(teacher)/grading.tsx)
- Contracts grading: [packages/contracts/src/grading.ts](packages/contracts/src/grading.ts)
- Previous story (5.7): [_bmad-output/implementation-artifacts/5-7-practice-recommendations.md](_bmad-output/implementation-artifacts/5-7-practice-recommendations.md)

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

N/A

### Pre-existing Uncommitted Changes (Not Part of Story 5.8)

The following files appear modified in git working tree but belong to earlier stories (5.4–5.7) and were never committed. They are carried forward in the working tree alongside story 5.8 changes:

- `apps/mobile/src/features/grading/hooks/useGradeApproval.ts` (Story 5.5)
- `apps/mobile/src/features/grading/hooks/useManualGrading.ts` (Story 5.6)
- `apps/mobile/src/services/grading-service.ts` (Story 5.3/5.6)
- `apps/mobile/src/features/grading/hooks/usePracticeRecommendations.ts` (Story 5.7)
- `apps/mobile/src/features/grading/components/__tests__/GradingCard.test.tsx` (Story 5.4/5.6)
- `apps/mobile/src/features/grading/hooks/__tests__/useGradeApproval.test.ts` (Story 5.5)
- `apps/mobile/src/features/grading/hooks/__tests__/useGradingReview.test.ts` (Story 5.4)
- `apps/mobile/src/features/grading/hooks/__tests__/useManualGrading.test.ts` (Story 5.6)
- `apps/mobile/src/features/grading/hooks/__tests__/usePracticeRecommendations.test.ts` (Story 5.7)

These should be committed as part of their respective stories before this story is merged.

### Completion Notes List

- Added `__esModule: true` to all Jest mock factories for ESM-interop packages (`@react-native-community/netinfo`, `@react-native-async-storage/async-storage`) — Babel's `_interopRequireDefault` double-wraps module exports without this flag, causing default imports to resolve to `undefined`.
- `updateQueueItem` returns early (no `setItem` call) when the target id is not found — test updated to assert `setItem` is not called in that case.
- `@react-native-async-storage/async-storage`, `@react-native-community/netinfo`, and `expo-file-system` were not present in `apps/mobile/package.json` and required explicit addition + `pnpm install`.
- `useOfflineQueueProcessor` exposes `queueItems` (full array) and `retryItem(id)` in addition to `pendingCount` and `processingItemId`, to allow the grading screen to drive per-item retry UI.

### File List

- `packages/contracts/src/grading.ts` — added `OfflineQueueItemStatus` type
- `packages/contracts/src/index.ts` — exported `OfflineQueueItemStatus`
- `apps/mobile/src/services/offline-queue.ts` — NEW: persistent queue with AsyncStorage + FileSystem
- `apps/mobile/src/services/queue-events.ts` — NEW: module-level event emitter for job-ready events
- `apps/mobile/src/hooks/useNetworkStatus.ts` — NEW: `useNetworkStatus` hook wrapping NetInfo
- `apps/mobile/src/features/grading/hooks/useGradingJob.ts` — offline path: NetInfo check + queue on offline
- `apps/mobile/src/features/grading/hooks/useOfflineQueueProcessor.ts` — NEW: auto-upload on reconnect
- `apps/mobile/src/features/grading/components/GradingCard.tsx` — `queued-offline` status UI
- `apps/mobile/app/(teacher)/grading.tsx` — pending count banner, retry wiring, queue job complete listener
- `apps/mobile/package.json` — added 3 dependencies + transformIgnorePatterns
- `pnpm-lock.yaml` — updated by pnpm install after package.json changes
- `apps/mobile/src/services/__tests__/offline-queue.test.ts` — NEW: 18 tests
- `apps/mobile/src/hooks/__tests__/useNetworkStatus.test.ts` — NEW: 6 tests
- `apps/mobile/src/features/grading/hooks/__tests__/useOfflineQueueProcessor.test.ts` — NEW: 11 tests
- `apps/mobile/src/features/grading/hooks/__tests__/useGradingJob.test.ts` — updated: 8 new offline tests
- `apps/mobile/app/(teacher)/__tests__/grading.test.tsx` — updated: offline UI tests
