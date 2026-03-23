# Story 4.9: Guided Onboarding Wizards per Role

Status: ready-for-dev

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

- [ ] Task 1: Add first-login detection mechanism (AC: #6)
  - [ ] 1.1 Create `apps/mobile/src/services/onboarding-wizard-state.ts` with `isOnboardingComplete(userId)` and `markOnboardingComplete(userId)` using `expo-secure-store` (key: `ilm_onboarding_done_{userId}`)
  - [ ] 1.2 Extract `user_id` from JWT in `AuthGuard` (already decoded in `AuthContext` but not exposed — add `userId` to `AuthState` interface and `useAuth()` return value)
  - [ ] 1.3 Update `AuthGuard` in `apps/mobile/app/_layout.tsx` to check `isOnboardingComplete(userId)` and route to `/onboarding` instead of `homePath` on first login

- [ ] Task 2: Add backend endpoint for parent's linked children (AC: #2)
  - [ ] 2.1 Add `get_linked_children(parent_user_id, org_id)` method to `OnboardingService` in `apps/api/app/domains/onboarding/service.py` — returns list of `(GuardianStudentLinkRecord, StudentRecord)` tuples
  - [ ] 2.2 Add `LinkedChildResponse` schema to `apps/api/app/domains/onboarding/schemas.py` (fields: `link_id`, `student_id`, `student_name`, `class_name`, `subject`)
  - [ ] 2.3 Add `GET /onboarding/parent/children` endpoint to `apps/api/app/domains/onboarding/router.py` (requires parent role, calls `service.get_linked_children`)
  - [ ] 2.4 Add `LinkedChildResponse`, `LinkedChildrenResponse` types to `packages/contracts/src/onboarding.ts`
  - [ ] 2.5 Add `getLinkedChildren(token)` function to `apps/mobile/src/services/onboarding-service.ts`
  - [ ] 2.6 Add tests to `apps/api/tests/test_onboarding_api.py`

- [ ] Task 3: Implement onboarding wizard screen (`apps/mobile/app/onboarding/index.tsx`) (AC: #1–5)
  - [ ] 3.1 Replace placeholder with role-branching wizard component that reads `role` from `useAuth()`
  - [ ] 3.2 Implement **Teacher wizard** (3 steps):
    - Step 1: Create/Select class — reuse `createClass` and `listClasses` from `onboarding-service.ts`; if classes exist, allow selecting one or creating new
    - Step 2: Add first students (skip allowed) — reuse `addStudent` from `onboarding-service.ts`; inline form with name + grade_level fields
    - Step 3: Confirmation screen — show class name, join code, student count with value framing ("Your class is ready!")
  - [ ] 3.3 Implement **Parent wizard** (3 steps):
    - Step 1: Confirm linked child — call `getLinkedChildren`; display child name + class; if no child linked, show "Ask your teacher for an invite link" message (forward path, never dead-end)
    - Step 2: Dashboard preview — show encouraging placeholder with child's name ("Emma's progress will appear here")
    - Step 3: Notification preference — toggle for progress updates (store preference locally for now; actual notification infrastructure is Epic 8)
  - [ ] 3.4 Implement **Student wizard** (2 steps):
    - Step 1: Join class — reuse existing join logic from `(student)/join.tsx`; if already enrolled show enrolled class; use growth-framed language ("Ready to track your growth?")
    - Step 2: Growth view preview — show student home skeleton with encouraging message ("Your learning journey starts here")
  - [ ] 3.5 Implement **Admin wizard** (3 steps):
    - Step 1: Welcome to admin — org name display (from JWT `org_id`), confirm setup starting
    - Step 2: Invite first teacher — text input for teacher email, show invite instructions (actual email/invite infrastructure TBD — can display join instructions)
    - Step 3: Confirmation — "Your school is set up and ready"
  - [ ] 3.6 Add progress indicator (step dots or "Step X of Y" label) to all wizards
  - [ ] 3.7 On wizard completion: call `markOnboardingComplete(userId)`, then `router.replace(homePath)`

- [ ] Task 4: Add Expo Router layout for `/onboarding` route (AC: #1–5)
  - [ ] 4.1 Create `apps/mobile/app/onboarding/_layout.tsx` — minimal layout wrapping `<Slot />` inside `TamaguiProvider`/`SafeAreaProvider` (or verify existing root layout covers it)
  - [ ] 4.2 Ensure `AuthGuard` allows navigation to `/onboarding` (it currently only allows `auth` group unauthenticated — add `onboarding` to allowed authenticated paths)

- [ ] Task 5: Tests and typecheck (AC: all)
  - [ ] 5.1 Run `pnpm typecheck` and fix all TypeScript errors
  - [ ] 5.2 Run API tests `python -m pytest apps/api/tests/test_onboarding_api.py -v` and ensure all pass

## Dev Notes

### Overview

This story implements role-specific guided onboarding wizards that are shown once on first login. The core mechanism is **client-side first-login detection** using `expo-secure-store` (not a backend flag — no `first_login` field exists in auth contracts). The wizard is a full-screen experience at `/onboarding` route, rendered before routing to the role home tab.

### Critical: No `first_login` in Auth

The `LoginResponse` (see [`packages/contracts/src/auth.ts`](packages/contracts/src/auth.ts)) has no `first_login` or `onboarding_complete` field. The `AuthContext` ([`apps/mobile/src/contexts/AuthContext.tsx`](apps/mobile/src/contexts/AuthContext.tsx)) derives `userId` from JWT but does NOT currently expose it in `AuthState`.

**Required change to `AuthContext`**: decode and expose `userId` (the JWT `sub` field) in `AuthState` so `AuthGuard` can use it for onboarding state lookup.

```typescript
// In AuthContext.tsx — extend AuthState with:
userId: string | null;

// Decode from JWT in decodeJwtPayload() (already exists):
const { sub: userId } = decodeJwtPayload(token);
```

### First-Login Detection Pattern

```typescript
// apps/mobile/src/services/onboarding-wizard-state.ts
import * as SecureStore from "expo-secure-store";

const key = (userId: string) => `ilm_onboarding_done_${userId}`;

export async function isOnboardingComplete(userId: string): Promise<boolean> {
  const val = await SecureStore.getItemAsync(key(userId));
  return val === "true";
}

export async function markOnboardingComplete(userId: string): Promise<void> {
  await SecureStore.setItemAsync(key(userId), "true");
}
```

### AuthGuard Changes

The `AuthGuard` in [`apps/mobile/app/_layout.tsx`](apps/mobile/app/_layout.tsx) must be extended. Currently when authenticated + not in auth group → redirect to `homePath`. New logic:

```
if isAuthenticated AND userId AND NOT in auth/onboarding groups:
  check isOnboardingComplete(userId)
  if NOT complete → router.replace("/onboarding")
  else → router.replace(homePath)
```

The guard must allow the `onboarding` segment without redirecting away. Add `segments[0] === "onboarding"` to the allowed-path check similar to `"auth"`.

### Backend: New Parent Children Endpoint

**Problem**: No `GET` endpoint exists to retrieve a parent's linked children. Story 4.8 only added `POST /invite/{token}/accept` which returns a single link.

**Solution**: Add `GET /onboarding/parent/children` to the onboarding router.

Service method (add to `apps/api/app/domains/onboarding/service.py`):
```python
def get_linked_children(
    self,
    parent_user_id: str,
    org_id: str,
) -> list[dict]:
    """Returns list of dicts with student_id, student_name, class_name, subject"""
    links = [
        l for l in self._repo.guardian_student_links.values()
        if l.parent_user_id == parent_user_id and l.org_id == org_id
    ]
    result = []
    for link in links:
        student = self._repo.students.get(link.student_id)
        if not student:
            continue
        # Find the student's class via enrollments
        enrollment = next(
            (e for e in self._repo.enrollments.values() if e.student_id == link.student_id and e.org_id == org_id),
            None
        )
        class_record = self._repo.classes.get(enrollment.class_id) if enrollment else None
        result.append({
            "link_id": link.link_id,
            "student_id": link.student_id,
            "student_name": student.name,
            "class_name": class_record.name if class_record else None,
            "subject": class_record.subject if class_record else None,
        })
    return result
```

Contract types to add to `packages/contracts/src/onboarding.ts`:
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

### Onboarding Wizard Implementation Pattern

The onboarding screen at [`apps/mobile/app/onboarding/index.tsx`](apps/mobile/app/onboarding/index.tsx) is currently a placeholder (11 lines). Replace entirely.

Pattern to follow — wizard with step state:
```typescript
export default function OnboardingScreen() {
  const { role, token, userId, homePath } = useAuth();
  const router = useRouter();
  const [step, setStep] = useState(0);

  const handleComplete = async () => {
    if (userId) await markOnboardingComplete(userId);
    router.replace(homePath as Parameters<typeof router.replace>[0]);
  };

  if (role === "teacher") return <TeacherWizard step={step} setStep={setStep} token={token!} onComplete={handleComplete} />;
  if (role === "parent") return <ParentWizard step={step} setStep={setStep} token={token!} onComplete={handleComplete} />;
  if (role === "student") return <StudentWizard step={step} setStep={setStep} token={token!} onComplete={handleComplete} />;
  if (role === "admin") return <AdminWizard step={step} setStep={setStep} onComplete={handleComplete} />;
  // Fallback — unknown role, skip wizard
  handleComplete();
  return null;
}
```

Sub-wizards can be defined in the same file or extracted to `apps/mobile/src/components/onboarding/`.

### Design System Compliance

Use **exact** Tamagui/design-token patterns from Stories 4.7 and 4.8:

```typescript
import { colors, spacing, fontSizes, fontWeights } from "@ilm/design-tokens";
import { YStack, XStack, Text, Button, Input, Spinner } from "tamagui";
import { SafeAreaView } from "react-native-safe-area-context";
// edges={["top"]} for content screens
```

Token usage (always `colors.xxx`, `spacing.xxx` from design-tokens, not hardcoded values):
- Background: `colors.background`
- Cards: `colors.surface`
- Borders: `colors.border`
- Primary action: `colors.primary`
- Text: `colors.textPrimary`, `colors.textSecondary`, `colors.textTertiary`

Progress indicators: use dot row (`XStack` with filled/empty circles) or plain "Step X of Y" text with `colors.textTertiary`.

Celebration / success state: use `Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success)` on wizard completion (already used in 4.7 pattern — `expo-haptics` is installed).

### Existing Endpoints Available (No New API Needed for These)

| Role | Existing endpoints to reuse |
|------|----------------------------|
| Teacher | `POST /onboarding/classes`, `GET /onboarding/classes`, `POST /onboarding/classes/{id}/students` |
| Student | `POST /onboarding/join` (already works via `joinClassByCode` in `onboarding-service.ts`) |
| Parent | `GET /onboarding/parent/children` **(NEW — Task 2)** |
| Admin | No new API needed — admin step 2 is informational only |

### Expo Router Route for `/onboarding`

The file `apps/mobile/app/onboarding/index.tsx` already exists (placeholder). The route `/onboarding` is already registered by Expo Router's file system routing. No new `_layout.tsx` is needed since the root layout in `apps/mobile/app/_layout.tsx` wraps all routes via `<Slot />`.

**Verify**: in `AuthGuard`'s `useEffect`, check `segments[0] === "onboarding"` and allow it (don't redirect away when authenticated user is on `/onboarding`).

### Story 4.8 Dev Patterns (Carry Forward)

From the previous story's implementation:
- In-memory repository uses `_ensure_seed_data()` guard — **do not** add new data structures without this pattern
- Frozen dataclasses for all records — the new `LinkedChildResponse` is a Pydantic schema (response model), not a dataclass
- Repository access pattern: `self._repo.guardian_student_links` (dict, keyed by `link_id`), `self._repo.students` (dict, keyed by `student_id`), `self._repo.enrollments` (dict, keyed by `enrollment_id`), `self._repo.classes` (dict, keyed by `class_id`)
- All API tests use `reset_onboarding_state_for_tests()` fixture already in test file

### What NOT To Implement

- **Push notifications** — notification preference in parent wizard is stored locally (e.g., `AsyncStorage`) only; actual push infrastructure is Epic 8
- **Real email invites for admin** — admin teacher invite step is UI-only (display instructions), not a real email send
- **COPPA consent gate** — this is Story 4.10, separate from the wizard
- **Any Epic 5+ features** (AI grading, analytics) — no references to unbuilt features
- **Google Classroom or roster import UI** in wizard — this is Epic 9
- **Web admin onboarding** — mobile only

### File Structure Impact

Files to **create**:
- `apps/mobile/src/services/onboarding-wizard-state.ts` (new)

Files to **modify**:
- `apps/mobile/app/onboarding/index.tsx` (replace placeholder)
- `apps/mobile/app/_layout.tsx` (update `AuthGuard` for onboarding routing)
- `apps/mobile/src/contexts/AuthContext.tsx` (add `userId` to `AuthState`)
- `apps/mobile/src/services/onboarding-service.ts` (add `getLinkedChildren`)
- `apps/api/app/domains/onboarding/service.py` (add `get_linked_children`)
- `apps/api/app/domains/onboarding/router.py` (add `GET /parent/children`)
- `apps/api/app/domains/onboarding/schemas.py` (add `LinkedChildResponse`, `LinkedChildrenResponse`)
- `packages/contracts/src/onboarding.ts` (add `LinkedChildResponse`, `LinkedChildrenResponse`)
- `packages/contracts/src/index.ts` (re-export new types if not auto-exported)
- `apps/api/tests/test_onboarding_api.py` (add tests for new endpoint)

### Project Structure Notes

- Alignment with unified project structure: onboarding service functions go in `apps/mobile/src/services/onboarding-service.ts` (existing file); new wizard state service goes in `apps/mobile/src/services/` (kebab-case.ts)
- Backend: new service method goes in `apps/api/app/domains/onboarding/service.py`, new schema in `schemas.py`, new endpoint in `router.py` — all consistent with existing domain structure
- The `apps/mobile/app/onboarding/` directory already exists with `index.tsx` placeholder — no new directory needed

### References

- Epic 4 story 4.9 requirements: [Source: `_bmad-output/planning-artifacts/epics.md` #Epic 4 → Story 4.9]
- Auth contracts (LoginResponse, UserRole): [Source: `packages/contracts/src/auth.ts`]
- Onboarding contracts (existing): [Source: `packages/contracts/src/onboarding.ts`]
- AuthContext + AuthGuard: [Source: `apps/mobile/app/_layout.tsx`], [Source: `apps/mobile/src/contexts/AuthContext.tsx`]
- Onboarding service (mobile): [Source: `apps/mobile/src/services/onboarding-service.ts`]
- Onboarding API router: [Source: `apps/api/app/domains/onboarding/router.py`]
- Onboarding domain models: [Source: `apps/api/app/domains/onboarding/models.py`]
- Teacher home screen patterns: [Source: `apps/mobile/app/(teacher)/index.tsx`]
- Student join screen: [Source: `apps/mobile/app/(student)/join.tsx`]
- Deep link handling (Story 4.8 pattern): [Source: `apps/mobile/app/_layout.tsx` #AuthGuard]
- Design tokens usage: [Source: `apps/mobile/app/(teacher)/index.tsx`]
- Tamagui component patterns: [Source: `apps/mobile/app/(teacher)/index.tsx`], [Source: `apps/mobile/app/(student)/join.tsx`]
- expo-secure-store: already a dependency (used by `apps/mobile/src/services/token-storage.ts`)

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

### File List
