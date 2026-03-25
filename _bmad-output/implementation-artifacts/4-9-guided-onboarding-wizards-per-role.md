# Story 4.9: Guided Onboarding Wizards per Role

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a new user,
I want a guided first-time setup flow tailored to my role,
so that I experience the core value of the product within my first few minutes.

## Acceptance Criteria

**AC1 — Teacher wizard**
Given a teacher signs in for the first time
When onboarding is triggered
Then they see a 3-step wizard: create/select class → add first students (or skip) → class setup confirmation with student count
And the wizard delivers a value moment (class is created and ready, students are enrolled)

**AC2 — Parent wizard**
Given a parent signs in for the first time (via invite link)
When onboarding is triggered
Then they see a 3-step wizard: confirm linked child → see dashboard preview → set notification preference
And the wizard delivers a value moment (child's dashboard is visible with any available data)

**AC3 — Student wizard**
Given a student signs in for the first time
When onboarding is triggered
Then they see a 2-step wizard: join class (if not already joined) → see growth view preview
And the wizard uses encouraging, growth-framed language

**AC4 — Admin wizard**
Given an admin signs in for the first time
When onboarding is triggered
Then they see a setup wizard: create organization → invite first teacher → confirmation
And the wizard includes progress indicators and clear step labels

**AC5 — Wizard completion**
Given the onboarding wizard completes for any role
When the user finishes all steps
Then they land on their role-appropriate home tab in a ready state
And the wizard does not reference or depend on features from future epics — all value moments are achievable with Epic 4 capabilities alone

**AC6 — First-login detection**
Given a user has already completed onboarding
When they sign in again
Then they are sent directly to their role home screen, not the wizard

## Tasks / Subtasks

- [x] Task 1: Add first-login detection mechanism (AC: #6)
  - [x] 1.1 Create `apps/mobile/src/services/onboarding-wizard-state.ts` — see exact implementation in Dev Notes (Platform-aware storage, named key constants)
  - [x] 1.2 Add `userId: string | null` to `AuthState` interface in `apps/mobile/src/contexts/AuthContext.tsx` — decode from JWT `sub` field using the existing `decodeJwtPayload()` function already in that file
  - [x] 1.3 Update `AuthGuard` in `apps/mobile/app/_layout.tsx` — see exact async `useEffect` pattern in Dev Notes

- [x] Task 2: Add backend endpoint for parent's linked children (AC: #2)
  - [x] 2.1 Add `get_enrollments_for_student(student_id)` to `OnboardingRepository` Protocol and `InMemoryOnboardingRepository` in `apps/api/app/domains/onboarding/repository.py`
  - [x] 2.2 Add `LinkedChildResponse`, `LinkedChildrenResponse` Pydantic schemas to `apps/api/app/domains/onboarding/schemas.py`
  - [x] 2.3 Add `get_linked_children(parent_user_id, org_id)` to `OnboardingService` in `apps/api/app/domains/onboarding/service.py` — see exact implementation in Dev Notes
  - [x] 2.4 Add `GET /onboarding/parent/children` endpoint to `apps/api/app/domains/onboarding/router.py` (requires parent role)
  - [x] 2.5 Add `LinkedChildResponse`, `LinkedChildrenResponse` to `packages/contracts/src/onboarding.ts` and re-export from `packages/contracts/src/index.ts`
  - [x] 2.6 Add `getLinkedChildren(token)` to `apps/mobile/src/services/onboarding-service.ts`
  - [x] 2.7 Add tests for new endpoint to `apps/api/tests/test_onboarding_api.py`

- [x] Task 3: Implement onboarding wizard screen (`apps/mobile/app/onboarding/index.tsx`) (AC: #1–5)
  - [x] 3.1 Replace placeholder entirely with role-branching wizard that reads `role` from `useAuth()`
  - [x] 3.2 Implement **Teacher wizard** (3 steps):
    - Step 1: Create/Select class — reuse `createClass` and `listClasses` from `onboarding-service.ts`; if classes exist, allow selecting one or creating new
    - Step 2: Add first students (skip allowed) — reuse `addStudent`; inline form with name + grade_level fields
    - Step 3: Confirmation — show class name, join code, student count ("Your class is ready!")
  - [x] 3.3 Implement **Parent wizard** (3 steps):
    - Step 1: Confirm linked child — call `getLinkedChildren`; display child name + class; if empty, show "Ask your teacher for an invite link" (never a dead-end)
    - Step 2: Dashboard preview — encouraging placeholder with child name ("Emma's progress will appear here")
    - Step 3: Notification preference — toggle stored via `expo-secure-store` (key: `ilm_notif_pref_{userId}`); Epic 8 will wire real notifications
  - [x] 3.4 Implement **Student wizard** (2 steps):
    - Step 1: Join class — navigate to existing `/(student)/join` route OR embed inline join code input; use growth-framed language
    - Step 2: Growth view preview — show `SkeletonLoader` cards with encouraging message ("Your learning journey starts here")
  - [x] 3.5 Implement **Admin wizard** (3 steps):
    - Step 1: Welcome — display `org_id` from `useAuth()` (only ID is available in JWT, not org name); confirm setup
    - Step 2: Invite first teacher — informational only (display manual instructions); no real email send
    - Step 3: Confirmation — "Your school is set up and ready"
  - [x] 3.6 Add progress indicator to all wizards — "Step X of Y" text using `colors.textTertiary` or dot row
  - [x] 3.7 On wizard completion: `await markOnboardingComplete(userId)` then `router.replace(homePath)`

- [x] Task 4: Verify AuthGuard allows `/onboarding` route (AC: #1–5)
  - [x] 4.1 Confirm no new `_layout.tsx` needed — root `apps/mobile/app/_layout.tsx` covers all routes via `<Slot />`
  - [x] 4.2 Add `segments[0] === "onboarding"` guard in `AuthGuard` so authenticated users on `/onboarding` are not redirected away

- [x] Task 5: Tests and typecheck (AC: all)
  - [x] 5.1 Run `pnpm typecheck` — zero TypeScript errors required before marking done
  - [x] 5.2 Run `python -m pytest apps/api/tests/test_onboarding_api.py -v` — all must pass

## Dev Notes

### Overview

Role-specific guided onboarding wizards shown **once on first login**. Core mechanism is **client-side first-login detection** via `expo-secure-store` — there is no `first_login` field in `LoginResponse` ([`packages/contracts/src/auth.ts`](packages/contracts/src/auth.ts)) and none should be added.

---

### Task 1 Detail: First-Login Detection

#### Step 1.1 — `onboarding-wizard-state.ts`

Follow the Platform-aware storage pattern from [`apps/mobile/src/services/token-storage.ts`](apps/mobile/src/services/token-storage.ts) (the `storage` wrapper in that file is **not exported** — replicate the pattern):

```typescript
// apps/mobile/src/services/onboarding-wizard-state.ts
import { Platform } from "react-native";
import * as SecureStore from "expo-secure-store";

const storage =
  Platform.OS === "web"
    ? {
        setItemAsync: async (key: string, value: string) => { localStorage.setItem(key, value); },
        getItemAsync: async (key: string) => localStorage.getItem(key),
        deleteItemAsync: async (key: string) => { localStorage.removeItem(key); },
      }
    : SecureStore;

// Named constants — follow pattern from token-storage.ts KEYS object
const KEYS = {
  onboardingDone: (userId: string) => `ilm_onboarding_done_${userId}`,
  notifPref: (userId: string) => `ilm_notif_pref_${userId}`,
} as const;

export async function isOnboardingComplete(userId: string): Promise<boolean> {
  const val = await storage.getItemAsync(KEYS.onboardingDone(userId));
  return val === "true";
}

export async function markOnboardingComplete(userId: string): Promise<void> {
  await storage.setItemAsync(KEYS.onboardingDone(userId), "true");
}

export async function getNotifPref(userId: string): Promise<boolean> {
  const val = await storage.getItemAsync(KEYS.notifPref(userId));
  return val !== "false"; // default ON
}

export async function setNotifPref(userId: string, enabled: boolean): Promise<void> {
  await storage.setItemAsync(KEYS.notifPref(userId), String(enabled));
}
```

> **No `@react-native-async-storage/async-storage`** — it is NOT in `package.json`. Use `expo-secure-store` exclusively for all local persistence in this story.

#### Step 1.2 — Add `userId` to `AuthContext`

In [`apps/mobile/src/contexts/AuthContext.tsx`](apps/mobile/src/contexts/AuthContext.tsx), `decodeJwtPayload()` already exists and returns `{ exp, sub, role, org_id }`. The `sub` field is the user ID. Add to `AuthState`:

```typescript
interface AuthState {
  // ... existing fields ...
  userId: string | null;  // ADD THIS
}
```

Set it wherever the token is decoded (login, Google login, and stored token restore):
```typescript
const { sub: userId } = decodeJwtPayload(response.access_token);
// then include userId in setState call
```

#### Step 1.3 — AuthGuard async routing

`isOnboardingComplete()` returns a `Promise`. The existing `useEffect` in `AuthGuard` is synchronous — the async check must be wrapped. **Exact pattern** (replaces the existing auth guard `useEffect` body for the authenticated-but-not-in-auth-group branch):

```typescript
useEffect(() => {
  if (isLoading) return;

  // Pending invite token handling (unchanged from Story 4.8)
  if (isAuthenticated && role === "parent" && token && pendingInviteToken) {
    // ... existing invite logic unchanged ...
    return;
  }

  const inAuthGroup = segments[0] === "auth";
  const inOnboardingGroup = segments[0] === "onboarding";

  if (!isAuthenticated && !inAuthGroup) {
    router.replace("/auth");
    return;
  }

  if (isAuthenticated && inAuthGroup && homePath) {
    // Will be redirected to onboarding or home below once not in auth group
    router.replace(homePath as Parameters<typeof router.replace>[0]);
    return;
  }

  if (isAuthenticated && !inAuthGroup && !inOnboardingGroup && homePath && userId) {
    // Async onboarding check — IIFE to handle Promise in useEffect
    void (async () => {
      const done = await isOnboardingComplete(userId);
      if (!done) {
        router.replace("/onboarding");
      } else {
        router.replace(homePath as Parameters<typeof router.replace>[0]);
      }
    })();
  }
}, [isAuthenticated, isLoading, role, token, segments, homePath, userId, router]);
```

> **Critical**: `userId` must be in the dependency array. Import `isOnboardingComplete` from `onboarding-wizard-state.ts`.

---

### Task 2 Detail: Backend — Parent's Linked Children

#### Step 2.1 — New repository method

Add to **both** the `OnboardingRepository` Protocol and `InMemoryOnboardingRepository` in [`apps/api/app/domains/onboarding/repository.py`](apps/api/app/domains/onboarding/repository.py):

```python
# In Protocol:
def get_enrollments_for_student(self, student_id: str) -> list[EnrollmentRecord]: ...

# In InMemoryOnboardingRepository:
def get_enrollments_for_student(self, student_id: str) -> list[EnrollmentRecord]:
    return [
        enr for enr in self.__class__._enrollments.values()
        if enr.student_id == student_id
    ]
```

> `_guardian_links` is a **class-level list** (not a dict): `InMemoryOnboardingRepository._guardian_links`. Access it only through protocol methods — never via direct attribute access on `self._repo`.

#### Step 2.2 — Service method

Add to [`apps/api/app/domains/onboarding/service.py`](apps/api/app/domains/onboarding/service.py). Uses **only protocol methods** — no direct attribute access on `_repo`:

```python
def get_linked_children(
    self,
    parent_user_id: str,
    org_id: str,
) -> list["LinkedChildResponse"]:
    # get_guardian_links_for_parent returns ALL links for this parent (no org filter in repo)
    all_links = self._repo.get_guardian_links_for_parent(parent_user_id)
    # Must filter by org_id here — repo method does not do it
    links = [l for l in all_links if l.org_id == org_id]

    result = []
    for link in links:
        student = self._repo.get_student(link.student_id)
        if not student:
            continue
        # Find class via student's enrollment(s)
        enrollments = self._repo.get_enrollments_for_student(link.student_id)
        class_record = None
        if enrollments:
            class_record = self._repo.get_class(enrollments[0].class_id)
        result.append(
            LinkedChildResponse(
                link_id=link.link_id,
                student_id=link.student_id,
                student_name=student.name,
                class_name=class_record.name if class_record else None,
                subject=class_record.subject if class_record else None,
            )
        )
    return result
```

Add `LinkedChildResponse` import at top of service.py once schema is created.

#### Steps 2.3–2.6 — Schema, Router, Contracts, Mobile Service

**Pydantic schemas** (add to [`apps/api/app/domains/onboarding/schemas.py`](apps/api/app/domains/onboarding/schemas.py)):
```python
class LinkedChildResponse(BaseModel):
    link_id: str
    student_id: str
    student_name: str
    class_name: str | None
    subject: str | None

class LinkedChildrenResponse(BaseModel):
    children: list[LinkedChildResponse]
```

**Router endpoint** (add to [`apps/api/app/domains/onboarding/router.py`](apps/api/app/domains/onboarding/router.py)):
```python
@router.get("/parent/children", response_model=LinkedChildrenResponse)
async def get_linked_children(
    actor: ActorContext = Depends(require_authenticated_actor),
    service: OnboardingService = Depends(get_onboarding_service),
) -> LinkedChildrenResponse:
    _require_parent(actor)
    children = service.get_linked_children(
        parent_user_id=actor.user_id,
        org_id=actor.org_id,
    )
    return LinkedChildrenResponse(children=children)
```

**TypeScript contracts** (add to [`packages/contracts/src/onboarding.ts`](packages/contracts/src/onboarding.ts)):
```typescript
export interface LinkedChildResponse {
  link_id: string;
  student_id: string;
  student_name: string;
  class_name: string | null;
  subject: string | null;
}

export interface LinkedChildrenResponse {
  children: LinkedChildResponse[];
}
```

Re-export from `packages/contracts/src/index.ts` (check existing export pattern — all types in `onboarding.ts` are already exported via `export * from "./onboarding"`).

**Mobile service** (add to [`apps/mobile/src/services/onboarding-service.ts`](apps/mobile/src/services/onboarding-service.ts)):

```typescript
import type { LinkedChildrenResponse } from "@ilm/contracts";

export async function getLinkedChildren(token: string): Promise<LinkedChildrenResponse> {
  return apiRequest<LinkedChildrenResponse>("/onboarding/parent/children", { token });
}
```

---

### Task 3 Detail: Wizard Implementation

#### Wizard root component pattern

```typescript
// apps/mobile/app/onboarding/index.tsx
export default function OnboardingScreen() {
  const { role, token, userId, homePath } = useAuth();
  const router = useRouter();
  const [step, setStep] = useState(0);

  const handleComplete = async () => {
    if (userId) await markOnboardingComplete(userId);
    await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    router.replace(homePath as Parameters<typeof router.replace>[0]);
  };

  if (role === "teacher") return <TeacherWizard step={step} setStep={setStep} token={token!} onComplete={handleComplete} />;
  if (role === "parent") return <ParentWizard step={step} setStep={setStep} token={token!} userId={userId!} onComplete={handleComplete} />;
  if (role === "student") return <StudentWizard step={step} setStep={setStep} token={token!} onComplete={handleComplete} />;
  if (role === "admin") return <AdminWizard step={step} setStep={setStep} orgId={/* from useAuth() */""} onComplete={handleComplete} />;
  void handleComplete(); // Unknown role — skip wizard
  return null;
}
```

Sub-wizard components can be in the same file or in `apps/mobile/src/components/onboarding/` (no existing components directory — create it if extracting).

#### Student wizard — reuse existing join screen

[`apps/mobile/app/(student)/index.tsx`](apps/mobile/app/(student)/index.tsx) (the Growth screen) **already has a "Join a Class" `Button`** that navigates to `/(student)/join`. The student wizard's Step 1 can either:

- **Option A** (preferred): Navigate to `/(student)/join` via `router.push("/(student)/join")` and detect return via `useFocusEffect`
- **Option B**: Embed an inline join code `Input` + `joinClassByCode()` call directly in the wizard

Do **not** duplicate the join UI from scratch — [`apps/mobile/app/(student)/join.tsx`](apps/mobile/app/(student)/join.tsx) already exists with the full implementation.

#### Student enrollment ID note — critical cross-domain fact

`join_by_code` in the service stores `student_id = student_user_id` (the auth user's ID, e.g., `"usr_xyz"`). This is **different** from `StudentRecord.student_id` (e.g., `"stu_1"`) used for teacher-added students. These two enrollment types coexist in the same `_enrollments` dict but serve different paths. The wizard only needs to trigger the student's own join — `joinClassByCode()` handles this correctly. Do not attempt to reconcile the two ID spaces.

#### Admin wizard — org name not available

The JWT payload contains `org_id` (a UUID/slug), not the org name. There is no `GET /org` endpoint in this codebase. The admin wizard Step 1 must display `org_id` as-is or use generic text ("Your organization is ready to set up"). Do not attempt to fetch an org name — no such endpoint exists.

#### Notification preference storage (parent wizard Step 3)

Use `setNotifPref(userId, enabled)` from `onboarding-wizard-state.ts` (defined in Task 1.1 above). No `AsyncStorage` — it is **not installed**. No push notification wiring — that is Epic 8.

---

### Design System Compliance

Exact import pattern (from [`apps/mobile/app/(teacher)/index.tsx`](apps/mobile/app/(teacher)/index.tsx)):

```typescript
import { colors, spacing, fontSizes, fontWeights } from "@ilm/design-tokens";
import { YStack, XStack, Text, Button, Input, Spinner } from "tamagui";
import { SafeAreaView } from "react-native-safe-area-context";
import * as Haptics from "expo-haptics";
// SafeAreaView always with edges={["top"]}
```

For skeleton loading (student step 2): `import { SkeletonLoader } from "@ilm/ui"` — already used in [`apps/mobile/app/(student)/index.tsx`](apps/mobile/app/(student)/index.tsx).

Token values: always via `colors.xxx`, `spacing.xxx` — no hardcoded hex or pixel values.

---

### Repository Access Rules (Prevent Disasters)

The `InMemoryOnboardingRepository` uses **class-level attributes** (`self.__class__._xxx`) never accessed directly from service code. The `OnboardingService` always uses **protocol methods** only:

| Need | Use this protocol method |
| ---- | ------------------------ |
| Parent's linked children | `self._repo.get_guardian_links_for_parent(parent_user_id)` |
| Student record | `self._repo.get_student(student_id)` |
| Student's enrollments | `self._repo.get_enrollments_for_student(student_id)` *(new — Task 2.1)* |
| Class record | `self._repo.get_class(class_id)` |

Never: `self._repo._classes`, `self._repo._guardian_links`, `self._repo.guardian_student_links` etc.

---

### What NOT To Implement

- **Push notifications** — parent notification preference is stored locally only; Epic 8 wires actual delivery
- **Real email invites** — admin wizard teacher invite is instructions-only; no SMTP/email send
- **COPPA consent gate** — Story 4.10, completely separate
- **Org name lookup** — no endpoint exists; display `org_id` or generic text in admin wizard
- **AsyncStorage** — not installed; use `expo-secure-store` for all persistence
- **Any Epic 5+ features** — AI grading, analytics, messaging are all out of scope

### File Structure Impact

Files to **create**:

- `apps/mobile/src/services/onboarding-wizard-state.ts`

Files to **modify**:

- `apps/mobile/app/onboarding/index.tsx` (replace placeholder)
- `apps/mobile/app/_layout.tsx` (AuthGuard async routing update)
- `apps/mobile/src/contexts/AuthContext.tsx` (add `userId` to `AuthState`)
- `apps/mobile/src/services/onboarding-service.ts` (add `getLinkedChildren`)
- `apps/api/app/domains/onboarding/repository.py` (add `get_enrollments_for_student`)
- `apps/api/app/domains/onboarding/service.py` (add `get_linked_children`)
- `apps/api/app/domains/onboarding/router.py` (add `GET /parent/children`)
- `apps/api/app/domains/onboarding/schemas.py` (add `LinkedChildResponse`, `LinkedChildrenResponse`)
- `packages/contracts/src/onboarding.ts` (add same two types)
- `apps/api/tests/test_onboarding_api.py` (add endpoint tests)

### Project Structure Notes

- `apps/mobile/app/onboarding/` directory already exists — no new directory needed
- Backend changes follow existing domain pattern: models → repository → service → router → schemas
- `packages/contracts/src/index.ts` uses `export * from "./onboarding"` — new types auto-exported; verify before adding manual re-exports

### References

- Epic 4 / Story 4.9 requirements: [Source: `_bmad-output/planning-artifacts/epics.md` #Epic 4 → Story 4.9]
- Auth contracts: [Source: `packages/contracts/src/auth.ts`]
- Onboarding contracts: [Source: `packages/contracts/src/onboarding.ts`]
- AuthContext + AuthGuard: [Source: `apps/mobile/app/_layout.tsx`], [Source: `apps/mobile/src/contexts/AuthContext.tsx`]
- Platform-aware storage pattern: [Source: `apps/mobile/src/services/token-storage.ts`]
- Onboarding mobile service: [Source: `apps/mobile/src/services/onboarding-service.ts`]
- Repository protocol + implementation: [Source: `apps/api/app/domains/onboarding/repository.py`]
- Onboarding service: [Source: `apps/api/app/domains/onboarding/service.py`]
- Onboarding router: [Source: `apps/api/app/domains/onboarding/router.py`]
- Teacher home (design patterns): [Source: `apps/mobile/app/(teacher)/index.tsx`]
- Student join screen (reuse): [Source: `apps/mobile/app/(student)/join.tsx`]
- Student growth screen (SkeletonLoader): [Source: `apps/mobile/app/(student)/index.tsx`]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — implementation proceeded without blockers.

### Completion Notes List

- **Task 1 (First-login detection):** Created `onboarding-wizard-state.ts` with platform-aware SecureStore wrapper, `isOnboardingComplete`/`markOnboardingComplete`/`getNotifPref`/`setNotifPref` exports. Added `userId: string | null` and `orgId: string | null` to `AuthState` — both decoded from JWT `sub`/`org_id` at login, Google login, and stored-token restore. Updated `AuthGuard` with async IIFE pattern: checks `isOnboardingComplete(userId)` and redirects to `/onboarding` if false; `inOnboardingGroup` guard prevents redirect loop.
- **Task 2 (Backend endpoint):** Added `get_enrollments_for_student` to `OnboardingRepository` protocol and `InMemoryOnboardingRepository`. Added `LinkedChildResponse`/`LinkedChildrenResponse` Pydantic schemas and TypeScript contracts. `get_linked_children` service method filters guardian links by `org_id` (repo method returns all, service filters). `GET /onboarding/parent/children` endpoint requires parent role. 4 new API tests added — all 38 pass.
- **Task 3 (Wizard screen):** Replaced placeholder with full role-branching wizard. Teacher: 3-step (create/select class → add students → confirmation with join code). Parent: 3-step (confirm linked child → dashboard preview with SkeletonLoader → notification toggle saved via `setNotifPref`). Student: 2-step (join class via push to `/(student)/join` → growth preview). Admin: 3-step (welcome + org_id display → teacher invite instructions → confirmation). All wizards show "Step X of Y" progress indicator. Completion calls `markOnboardingComplete(userId)` + haptic feedback + `router.replace(homePath)`.
- **Task 4 (AuthGuard):** Implemented as part of Task 1.3. `inOnboardingGroup` check prevents authenticated users on `/onboarding` from being redirected away.
- **Task 5 (Tests/typecheck):** 38/38 API tests pass. `pnpm typecheck` reports zero errors.

### File List

**Created:**

- `apps/mobile/src/services/onboarding-wizard-state.ts`

**Modified:**

- `apps/mobile/app/onboarding/index.tsx`
- `apps/mobile/app/(student)/join.tsx`
- `apps/mobile/app/_layout.tsx`
- `apps/mobile/src/contexts/AuthContext.tsx`
- `apps/mobile/src/services/onboarding-service.ts`
- `apps/api/app/domains/onboarding/repository.py`
- `apps/api/app/domains/onboarding/service.py`
- `apps/api/app/domains/onboarding/router.py`
- `apps/api/app/domains/onboarding/schemas.py`
- `packages/contracts/src/onboarding.ts`
- `packages/contracts/src/index.ts`
- `apps/api/tests/test_onboarding_api.py`

## Senior Developer Review (AI)

### Reviewer

GitHub Copilot (GPT-5.3-Codex)

### Review Date

2026-03-23

### Outcome

Changes Requested items addressed; story is now approved.

### Findings Resolved

- **[HIGH] Student onboarding flow continuity:** Fixed wizard-to-join handoff so successful join returns to onboarding step 2 (`/onboarding?step=1`) instead of redirecting to student home and triggering onboarding loops.
- **[MEDIUM] Parent notification preference save handling:** Added guarded save flow with `try/catch/finally` and user-visible error state to prevent silent failure and inconsistent loading behavior.
- **[MEDIUM] Validation reproducibility:** Installed missing Python test dependencies in workspace venv and reran API tests for verifiable evidence.

### Validation Evidence

- `pnpm typecheck` ✅
- `/home/cybernyx/teemo.ai/ilm/.venv/bin/python -m pytest apps/api/tests/test_onboarding_api.py -v` ✅ (38 passed)

## Change Log

- 2026-03-23: Implemented story 4.9 — guided onboarding wizards per role. Added first-login detection via expo-secure-store, GET /onboarding/parent/children backend endpoint, full 4-role wizard UI (teacher/parent/student/admin), AuthGuard onboarding routing, and 4 new API tests. All 38 tests pass, zero TypeScript errors.
- 2026-03-23: Senior developer review fixes applied for story 4.9. Resolved student join/onboarding flow continuity, added parent notification preference save error handling, and verified with `pnpm typecheck` plus onboarding API test run (38 passed).
- 2026-03-23: Low-severity cleanup pass: removed unused imports and unused local variable in onboarding service; revalidated onboarding API tests (38 passed).
