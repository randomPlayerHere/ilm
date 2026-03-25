# Story 4.8: Invite Links, Join Codes and Parent-Student Linking

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a teacher,
I want to generate parent invite links and student join codes,
So that parents are automatically connected to their child and students can join my class easily.

## Acceptance Criteria

1. **Generate parent invite link:**
   Given a teacher viewing a student in their class roster,
   When they generate a parent invite link for that student,
   Then a unique invite URL is created that is pre-linked to the specific student,
   And the link can be shared via copy-to-clipboard or device share sheet.

2. **Parent accepts invite link:**
   Given a parent taps an invite link,
   When they complete sign-up or sign-in (email/password or Google),
   Then their account is automatically linked to the student specified in the invite,
   And they land on the parent dashboard showing that child's data without manual linking.

3. **Student joins via join code:**
   Given a student has a class join code,
   When they enter the code on the join screen after signing in,
   Then they are enrolled in the corresponding class,
   And they see the class appear in their student view.

4. **Invite link used or expired:**
   Given an invite link has been used or has expired,
   When someone attempts to use it,
   Then the system shows an appropriate message (already used / expired),
   And does not create duplicate linkages.

## Tasks / Subtasks

### PREREQUISITE CHECK

- [x] Task 0: Verify Story 4.7 is fully implemented before starting 4.8 (AC: all)
  - [x] Confirm `apps/api/app/domains/onboarding/` exists with models.py, repository.py, service.py, router.py, schemas.py
  - [x] Confirm `OnboardingRepository` protocol + `InMemoryOnboardingRepository` is complete
  - [x] Confirm `ClassRecord`, `StudentRecord`, `EnrollmentRecord` dataclasses exist
  - [x] Confirm `apps/mobile/app/(teacher)/class/[classId].tsx` exists (the roster screen 4.8 will extend)
  - [x] Confirm `packages/contracts/src/onboarding.ts` exists with class/student types
  - **If any of the above don't exist: STOP and implement Story 4.7 first**

### Backend: Extend `onboarding` domain with invite links and join codes

- [x] Task 1: Add new models to `apps/api/app/domains/onboarding/models.py` (AC: #1, #2, #3, #4)
  - [x] Add `InviteLinkRecord` dataclass (see Data Model section)
  - [x] Add `GuardianStudentLinkRecord` dataclass (see Data Model section)

- [x] Task 2: Extend `InMemoryOnboardingRepository` in `apps/api/app/domains/onboarding/repository.py` (AC: all)
  - [x] Add `_invite_links: dict[str, InviteLinkRecord] = {}` class-level dict
  - [x] Add `_guardian_links: list[GuardianStudentLinkRecord] = []` class-level list
  - [x] Add `_invite_seq: int = 0` class-level counter
  - [x] Add `_guardian_link_seq: int = 0` class-level counter
  - [x] Add `create_invite_link(org_id, class_id, student_id, generated_by) -> InviteLinkRecord` method
  - [x] Add `get_invite_link(token) -> InviteLinkRecord | None` method
  - [x] Add `accept_invite_link(token, parent_user_id) -> GuardianStudentLinkRecord` method (mark used_at, create link)
  - [x] Add `get_guardian_links_for_parent(parent_user_id) -> list[GuardianStudentLinkRecord]` method
  - [x] Add `join_class_by_code(join_code, student_user_id, org_id) -> EnrollmentRecord` method
  - [x] Update `reset_state()` to also reset invite/guardian state
  - [x] Add seed data: one pre-generated invite link for `stu_1` / `cls_1` (token: `inv_demo_abc123`) for testing

- [x] Task 3: Add Pydantic schemas to `apps/api/app/domains/onboarding/schemas.py` (AC: all)
  - [x] `InviteLinkResponse` schema
  - [x] `InviteLinkResolveResponse` schema (student preview for deep link landing page)
  - [x] `JoinCodeRequest` schema
  - [x] `JoinCodeResponse` schema
  - [x] `GuardianStudentLinkResponse` schema

- [x] Task 4: Add invite/join endpoints to `apps/api/app/domains/onboarding/router.py` (AC: all)
  - [x] `POST /onboarding/classes/{class_id}/students/{student_id}/invite-link` → generate invite link (teacher only)
  - [x] `GET /onboarding/invite/{token}` → resolve invite (public: no auth required — parent clicks link before signing in)
  - [x] `POST /onboarding/invite/{token}/accept` → accept invite (parent role required, authenticated)
  - [x] `POST /onboarding/join` → student enters join code → enrolled in class (student role required)

- [x] Task 5: Add service business logic to `apps/api/app/domains/onboarding/service.py` (AC: all)
  - [x] `generate_invite_link(actor, class_id, student_id) -> InviteLinkRecord` — teacher-only
  - [x] `resolve_invite_link(token) -> InviteLinkResolveResponse` — returns student/class info for preview
  - [x] `accept_invite_link(actor, token) -> GuardianStudentLinkRecord` — parent-only, marks used_at
  - [x] `join_by_code(actor, join_code) -> EnrollmentRecord` — student-only

### Contracts: New TypeScript types

- [x] Task 6: Add invite/join types to `packages/contracts/src/onboarding.ts` (AC: all)
  - [x] `InviteLinkResponse`, `InviteLinkResolveResponse`, `JoinCodeRequest`, `JoinCodeResponse` interfaces
  - [x] Export all new types from `packages/contracts/src/index.ts`

### Mobile: Teacher roster extension (add invite link generation)

- [x] Task 7: Extend `apps/mobile/app/(teacher)/class/[classId].tsx` (AC: #1)
  - [x] Add "Generate Invite Link" button/icon next to each student row in the roster list
  - [x] On tap: call `POST /onboarding/classes/{classId}/students/{studentId}/invite-link`
  - [x] On success: show bottom sheet with:
    - The invite URL (displayed in monospace text)
    - "Copy Link" button → `Clipboard.setStringAsync(url)` from `expo-clipboard`
    - "Share" button → `Share.share({ message: url })` from React Native's `Share` API
  - [x] Show activity indicator while generating; show error toast if generation fails

- [x] Task 8: Create `apps/mobile/src/services/invite-service.ts` (AC: #1, #2, #4)
  - [x] `generateInviteLink(token, classId, studentId): Promise<InviteLinkResponse>`
  - [x] `resolveInviteLink(token): Promise<InviteLinkResolveResponse>` (no auth token needed)
  - [x] `acceptInviteLink(authToken, inviteToken): Promise<void>`

### Mobile: Student join code screen

- [x] Task 9: Create `apps/mobile/app/(student)/join.tsx` (AC: #3)
  - [x] Text input for join code entry (uppercase, max 6 chars, auto-uppercase transform)
  - [x] "Join Class" button → calls `POST /onboarding/join` with the code
  - [x] On success: use `router.replace("/(student)")` — NOT `router.back()` (no guaranteed back stack)
  - [x] On 404: "Invalid or expired join code" error message
  - [x] On 409: "You are already enrolled in this class" message
  - [x] Add "Join a Class" entry point in `apps/mobile/app/(student)/index.tsx` (e.g., a "+" button or empty state CTA) — keep it minimal; just a navigation link to join.tsx

- [x] Task 9b: Hide `join` from student tab bar in `apps/mobile/app/(student)/_layout.tsx` (AC: #3)
  - **CRITICAL:** `(student)/_layout.tsx` uses `<Tabs>` — any file in that directory auto-appears as a tab
  - [x] Add `<Tabs.Screen name="join" options={{ href: null }} />` inside the `<Tabs>` block
  - [x] This prevents a "Join" tab from appearing in the student bottom navigation bar
  - See Dev Notes for complete example

- [x] Task 10: Add `joinClass` to `apps/mobile/src/services/onboarding-service.ts` (AC: #3)
  - [x] `joinClassByCode(token, joinCode): Promise<JoinCodeResponse>`

### Mobile: Deep link handling for invite flow

- [x] Task 11: Configure deep link scheme in `apps/mobile/app.json` (AC: #2)
  - **⚠️ SCHEME CONFLICT — READ BEFORE ACTING:** `app.json` currently has `"scheme": "teacheros"` (set in Story 4.4). The invite URLs in this story use `ilm://invite/{token}`. You must resolve this before proceeding — see Dev Notes: Deep Link Scheme Decision.
  - [x] Add `intentFilters` for Android and `associatedDomains` placeholder for iOS (see Dev Notes)

- [x] Task 12: Handle invite deep link in `apps/mobile/app/_layout.tsx` (AC: #2, #4)
  - [x] **First: update `AuthGuard` destructuring** — add `role` and `token` to `const { isLoading, isAuthenticated, homePath } = useAuth()` (currently missing these)
  - [x] Add `Linking.addEventListener("url", handleDeepLink)` in `RootLayout` effect
  - [x] Parse deep link URL using the scheme decided in Task 11 (either `ilm://invite/` or `teacheros://invite/`)
  - [x] If authenticated as parent: call `acceptInviteLink(token)` and navigate to `/(parent)` on success
  - [x] If NOT authenticated: store token in module-level variable or context, redirect to `/auth`
  - [x] In `AuthGuard`, **modify the existing useEffect** (add pending invite check into it, do NOT add a second useEffect)
  - [x] Add `useRef(false)` guard so `Linking.getInitialURL()` only fires once on mount, not on every auth state change
  - [x] See Dev Notes for complete implementation pattern

- [x] Task 13: TypeScript verification (AC: all)
  - [x] Run `pnpm typecheck` from monorepo root — must pass with zero errors

- [x] Task 14: Backend API tests for new endpoints (AC: all)
  - [x] Extend `apps/api/tests/test_onboarding_api.py` with tests covering:
    - [x] `POST .../invite-link` — teacher generates link for enrolled student → 200 with token/url
    - [x] `POST .../invite-link` — idempotent: second call for same student returns existing active link
    - [x] `POST .../invite-link` — teacher doesn't own class → 403
    - [x] `GET /onboarding/invite/{token}` — valid unused link → valid=True, student/class name returned
    - [x] `GET /onboarding/invite/{token}` — already used link → valid=False, reason="already_used"
    - [x] `GET /onboarding/invite/{token}` — unknown token → 404
    - [x] `POST /onboarding/invite/{token}/accept` — parent accepts valid link → 200, guardian link created
    - [x] `POST /onboarding/invite/{token}/accept` — parent re-accepts already used link → 400
    - [x] `POST /onboarding/invite/{token}/accept` — parent already linked to student → 409
    - [x] `POST /onboarding/invite/{token}/accept` — non-parent role → 403
    - [x] `POST /onboarding/join` — valid join code → 200, enrollment created
    - [x] `POST /onboarding/join` — invalid code → 404
    - [x] `POST /onboarding/join` — student already enrolled → 409
    - [x] `POST /onboarding/join` — non-student role → 403
  - [x] All existing tests must continue passing (no regressions in test_onboarding_api.py)

### Review Follow-ups (AI)

- [x] [AI-Review][High] Enforce org consistency when accepting invite links to prevent cross-tenant linking via token reuse ([apps/api/app/domains/onboarding/service.py]).
- [x] [AI-Review][High] Surface explicit user messaging for invite states (already used / expired) in deep-link acceptance flow instead of silent catch ([apps/mobile/app/_layout.tsx], AC #4).
- [x] [AI-Review][High] Fix student join identity mapping to avoid double-prefixed IDs (`usr_usr_*`) and align enrollment linkage with auth user IDs ([apps/api/app/domains/onboarding/service.py], [apps/api/app/domains/onboarding/repository.py]).
- [x] [AI-Review][Medium] Align join-code length constraints between story/task claim (max 6) and implementation/schema ([apps/mobile/app/(student)/join.tsx], [apps/api/app/domains/onboarding/schemas.py]).
- [x] [AI-Review][Medium] Reconcile story File List with actual modified source files; include omitted app file changes ([apps/mobile/app/(teacher)/index.tsx]).
- [x] [AI-Review][Low] Remove or map unused invite error type (`InviteLinkAlreadyUsedError`) to avoid dead-path client handling ([apps/mobile/src/services/invite-service.ts]).

## Dev Notes

### CRITICAL DEPENDENCY: Story 4.7 Must Be Complete First

Story 4.8 **extends** the `onboarding` domain created in Story 4.7. All of the following must exist before starting 4.8:
- `apps/api/app/domains/onboarding/models.py` — `ClassRecord`, `StudentRecord`, `EnrollmentRecord`
- `apps/api/app/domains/onboarding/repository.py` — `InMemoryOnboardingRepository` with class/student/enrollment methods
- `apps/api/app/domains/onboarding/service.py` — `OnboardingService`
- `apps/api/app/domains/onboarding/router.py` — class/student/CSV endpoints
- `apps/mobile/app/(teacher)/class/[classId].tsx` — the roster screen that Task 7 extends

If these don't exist, implement Story 4.7 first.

### Architecture: Data Model

```python
# Add to apps/api/app/domains/onboarding/models.py

@dataclass(frozen=True)
class InviteLinkRecord:
    invite_id: str         # e.g., "inv_1"
    org_id: str
    class_id: str
    student_id: str        # StudentRecord.student_id (NOT a user account — see 4.7 notes)
    token: str             # URL-safe random token, e.g., "abc123xyz789..."
    generated_by: str      # teacher user_id
    expires_at: str        # ISO 8601 UTC — 72 hours from creation
    used_at: str | None    # ISO 8601 UTC when accepted, None if unused
    created_at: str

@dataclass(frozen=True)
class GuardianStudentLinkRecord:
    link_id: str           # e.g., "gsl_1"
    parent_user_id: str    # usr_* from auth domain (the parent's auth user)
    student_id: str        # StudentRecord.student_id from onboarding domain
    org_id: str
    linked_via: str        # "invite_link" | "manual"
    invite_id: str | None  # InviteLinkRecord.invite_id, None if manual
    created_at: str
```

**Token generation:**
```python
from secrets import token_urlsafe

def _generate_invite_token() -> str:
    return token_urlsafe(18)   # 24-char URL-safe string
```

**Invite URL format:**
```python
INVITE_URL_SCHEME = "ilm://invite/"

def _build_invite_url(token: str) -> str:
    return f"{INVITE_URL_SCHEME}{token}"
    # Produces: ilm://invite/abc123xyz789...
    # This is the deep link URL shared with parents
```

**Expiry:**
```python
from datetime import UTC, datetime, timedelta
expires_at = (datetime.now(UTC) + timedelta(hours=72)).isoformat()
```

**Seed data (add to `InMemoryOnboardingRepository._ensure_seed_data`):**
```python
# One pre-existing invite link for stu_1 in cls_1, generated by teacher
InviteLinkRecord(
    invite_id="inv_1",
    org_id="org_demo_1",
    class_id="cls_1",
    student_id="stu_1",
    token="inv_demo_abc123",
    generated_by="usr_teacher_1",
    expires_at=(datetime.now(UTC) + timedelta(hours=72)).isoformat(),
    used_at=None,
    created_at="2026-03-22T08:00:00Z",
)
```

### Architecture: API Endpoints

All under `/onboarding/*` prefix (existing router prefix from Story 4.7).

```
POST /onboarding/classes/{class_id}/students/{student_id}/invite-link
  → Auth: teacher required
  → Returns: InviteLinkResponse { invite_id, token, url, student_id, expires_at }

GET /onboarding/invite/{token}
  → Auth: NOT required (parent hasn't signed in yet)
  → Returns: InviteLinkResolveResponse { student_name, class_name, valid, reason }
  → On not found: 404
  → On already used: 200 with valid=False, reason="already_used"
  → On expired: 200 with valid=False, reason="expired"

POST /onboarding/invite/{token}/accept
  → Auth: parent role required (MUST be authenticated)
  → Body: {} (empty — parent identity from JWT)
  → Returns: GuardianStudentLinkResponse { link_id, student_id, student_name }
  → On already linked: 409 with detail "Already linked to this student"
  → On invalid/expired/used token: 400

POST /onboarding/join
  → Auth: student role required
  → Body: JoinCodeRequest { join_code: str }
  → Returns: JoinCodeResponse { class_id, class_name, subject }
  → On invalid code: 404 with detail "Invalid or expired join code"
  → On already enrolled: 409 with detail "Already enrolled in this class"
```

**Router helper for role enforcement (follow pattern from courses domain):**
```python
from fastapi import HTTPException, status

def _require_parent(actor: ActorContext) -> None:
    if actor.role != "parent":
        raise HTTPException(status_code=403, detail="Parent access required")

def _require_student(actor: ActorContext) -> None:
    if actor.role != "student":
        raise HTTPException(status_code=403, detail="Student access required")
```

**GET /onboarding/invite/{token} is PUBLIC (no auth dependency):**
```python
@router.get("/invite/{token}", response_model=InviteLinkResolveResponse)
async def resolve_invite_link(
    token: str,
    service: OnboardingService = Depends(get_onboarding_service),
) -> InviteLinkResolveResponse:
    # No actor context — this endpoint is unauthenticated
    return service.resolve_invite_link(token)
```

### Architecture: Service Business Rules

```python
# In OnboardingService

def generate_invite_link(self, actor_user_id: str, actor_org_id: str, class_id: str, student_id: str) -> InviteLinkRecord:
    # 1. Verify class exists and belongs to actor (teacher owns it)
    # 2. Verify student is enrolled in this class
    # 3. Check if an active (non-expired, non-used) invite already exists for this student
    #    → If yes, return existing (idempotent — don't create duplicates)
    # 4. Create new InviteLinkRecord with 72h expiry

def resolve_invite_link(self, token: str) -> InviteLinkResolveResponse:
    # Returns student_name, class_name for link preview
    # If not found: raise 404
    # If used or expired: return valid=False with reason

def accept_invite_link(self, parent_user_id: str, parent_org_id: str, token: str) -> GuardianStudentLinkRecord:
    # 1. Validate token (exists, not expired, not already used)
    # 2. Check parent is not already linked to this student → 409 if duplicate
    # 3. Mark invite as used (set used_at = now)
    # 4. Create GuardianStudentLinkRecord

def join_by_code(self, student_user_id: str, org_id: str, join_code: str) -> dict:
    # 1. Find class by join_code AND org_id (org-scoped)
    # 2. If not found: raise 404
    # 3. Create StudentRecord for this student_user_id if not exists (link auth user to student record)
    # 4. Check if already enrolled → 409 if duplicate
    # 5. Create EnrollmentRecord and return class info
```

**Important:** `StudentRecord` in 4.7 is a lightweight enrollment record (name + grade_level), NOT an auth user.
When a student uses a join code, we link their auth user (`student_user_id` from JWT) to the class.
Extend the repository to support looking up enrollments by `student_user_id` in addition to `student_id`.

### Pydantic Schemas (Backend)

```python
# Add to apps/api/app/domains/onboarding/schemas.py

class InviteLinkResponse(BaseModel):
    invite_id: str
    token: str
    url: str          # "ilm://invite/{token}"
    student_id: str
    expires_at: str

class InviteLinkResolveResponse(BaseModel):
    valid: bool
    reason: str | None  # "already_used" | "expired" | None (if valid=True)
    student_name: str | None
    class_name: str | None
    subject: str | None

class JoinCodeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    join_code: Annotated[str, StringConstraints(min_length=1, max_length=10, strip_whitespace=True)]

class JoinCodeResponse(BaseModel):
    class_id: str
    class_name: str
    subject: str

class GuardianStudentLinkResponse(BaseModel):
    link_id: str
    student_id: str
    student_name: str
```

### Contracts: TypeScript Types

Add to `packages/contracts/src/onboarding.ts`:

```typescript
export interface InviteLinkResponse {
  invite_id: string;
  token: string;
  url: string;         // "ilm://invite/{token}"
  student_id: string;
  expires_at: string;
}

export interface InviteLinkResolveResponse {
  valid: boolean;
  reason: string | null;    // "already_used" | "expired" | null
  student_name: string | null;
  class_name: string | null;
  subject: string | null;
}

export interface JoinCodeRequest {
  join_code: string;
}

export interface JoinCodeResponse {
  class_id: string;
  class_name: string;
  subject: string;
}

export interface GuardianStudentLinkResponse {
  link_id: string;
  student_id: string;
  student_name: string;
}
```

Add to the **existing** export block in `packages/contracts/src/index.ts` (do not create a second block — append to the existing `from "./onboarding"` export):
```typescript
// Existing line — extend it to include the 5 new types:
export type {
  ClassCreateRequest, ClassResponse, ClassListResponse,
  StudentCreateRequest, StudentResponse, RosterResponse,
  CsvImportRowResult, CsvImportResponse,
  InviteLinkResponse, InviteLinkResolveResponse,
  JoinCodeRequest, JoinCodeResponse,
  GuardianStudentLinkResponse,
} from "./onboarding";
```

### Mobile: Invite Service

Create `apps/mobile/src/services/invite-service.ts`:

```typescript
import type { InviteLinkResponse, InviteLinkResolveResponse, GuardianStudentLinkResponse } from "@ilm/contracts";
import { apiRequest, ApiError } from "./api-client";

export class InviteLinkExpiredError extends Error {
  name = "InviteLinkExpiredError" as const;
}
export class InviteLinkAlreadyUsedError extends Error {
  name = "InviteLinkAlreadyUsedError" as const;
}
export class AlreadyLinkedError extends Error {
  name = "AlreadyLinkedError" as const;
}

export async function generateInviteLink(
  token: string,
  classId: string,
  studentId: string,
): Promise<InviteLinkResponse> {
  return apiRequest<InviteLinkResponse>(
    `/onboarding/classes/${classId}/students/${studentId}/invite-link`,
    { method: "POST", token },
  );
}

export async function resolveInviteLink(
  inviteToken: string,
): Promise<InviteLinkResolveResponse> {
  // No auth token — this is a public endpoint
  return apiRequest<InviteLinkResolveResponse>(`/onboarding/invite/${inviteToken}`);
}

export async function acceptInviteLink(
  authToken: string,
  inviteToken: string,
): Promise<GuardianStudentLinkResponse> {
  try {
    return await apiRequest<GuardianStudentLinkResponse>(
      `/onboarding/invite/${inviteToken}/accept`,
      { method: "POST", token: authToken },
    );
  } catch (error) {
    if (error instanceof ApiError) {
      switch (error.status) {
        case 400: throw new InviteLinkExpiredError("This invite link is no longer valid.");
        case 409: throw new AlreadyLinkedError("You are already linked to this student.");
      }
    }
    throw error;
  }
}
```

### Mobile: Join Class Service (extend onboarding-service.ts)

Add to `apps/mobile/src/services/onboarding-service.ts`:

```typescript
import type { JoinCodeRequest, JoinCodeResponse } from "@ilm/contracts";

export class InvalidJoinCodeError extends Error {
  name = "InvalidJoinCodeError" as const;
}
export class AlreadyEnrolledError extends Error {
  name = "AlreadyEnrolledError" as const;
}

export async function joinClassByCode(
  token: string,
  joinCode: string,
): Promise<JoinCodeResponse> {
  const body: JoinCodeRequest = { join_code: joinCode.toUpperCase().trim() };
  try {
    return await apiRequest<JoinCodeResponse>("/onboarding/join", {
      method: "POST",
      body,
      token,
    });
  } catch (error) {
    if (error instanceof ApiError) {
      switch (error.status) {
        case 404: throw new InvalidJoinCodeError("Invalid or expired join code.");
        case 409: throw new AlreadyEnrolledError("You are already enrolled in this class.");
      }
    }
    throw error;
  }
}
```

### Mobile: Deep Link Configuration and Handling

#### ⚠️ STEP 0 (CRITICAL): Deep Link Scheme Decision

The current `apps/mobile/app.json` (line 38) already contains:
```json
"scheme": "teacheros"
```

This was set during Story 4.4 and is the registered deep link scheme for the app. This story uses `ilm://invite/{token}` throughout, which **conflicts** with the existing scheme. You must choose **one of these options** before writing any code:

**Option A — Change scheme to `ilm` (recommended if brand alignment is desired):**
- Replace `"scheme": "teacheros"` with `"scheme": "ilm"` in `app.json`
- Update `INVITE_URL_SCHEME` to `"ilm://invite/"` (already correct in story)
- Note: This changes the app's deep link identity — coordinate if Universal Links / App Store submission is planned

**Option B — Keep `teacheros` scheme:**
- Leave `app.json` unchanged (`"scheme": "teacheros"` stays)
- Change `INVITE_URL_SCHEME = "teacheros://invite/"` in the backend service
- Update all URL regex patterns in the deep link handler to `^teacheros:\/\/invite\/(.+)$`
- Update the `data` filter in `intentFilters` to use `"scheme": "teacheros"`

**Pick one option and apply it consistently across all files.** The tasks and code below use `ilm://` (Option A) — adjust if you choose Option B.

---

**Step 1: Configure scheme in `apps/mobile/app.json`**

Add/update the `expo` config object (using Option A):
```json
{
  "expo": {
    "scheme": "ilm",
    "android": {
      "intentFilters": [
        {
          "action": "VIEW",
          "autoVerify": true,
          "data": [{ "scheme": "ilm", "host": "invite" }],
          "category": ["BROWSABLE", "DEFAULT"]
        }
      ]
    }
  }
}
```

---

**Step 2: Handle deep links in `apps/mobile/app/_layout.tsx`**

**Delta from current `_layout.tsx`:**
1. `AuthGuard` currently destructures `{ isLoading, isAuthenticated, homePath }` — **update to add `role` and `token`**
2. The existing `useEffect` (auth guard logic) must be **modified** to add the pending invite check — do NOT add a second `useEffect`
3. Add a `useRef(false)` guard so `Linking.getInitialURL()` only fires once on mount

```typescript
import { useEffect, useRef } from "react";
import { Linking } from "react-native";
import { acceptInviteLink } from "../src/services/invite-service";

// Module-level pending token (survives navigation during auth flow)
let pendingInviteToken: string | null = null;

export function getPendingInviteToken(): string | null { return pendingInviteToken; }
export function clearPendingInviteToken(): void { pendingInviteToken = null; }

// In AuthGuard component — update existing destructuring:
const router = useRouter();
const { isAuthenticated, isLoading, role, token, homePath } = useAuth();  // ADD role, token
const initialUrlHandled = useRef(false);  // ADD: prevent double-processing

// ADD: deep link listener (separate useEffect, only for the listener itself)
useEffect(() => {
  function handleUrl({ url }: { url: string }) {
    const match = url.match(/^ilm:\/\/invite\/(.+)$/);
    if (!match) return;
    const inviteToken = match[1];
    if (isAuthenticated && role === "parent" && token) {
      acceptInviteLink(token, inviteToken)
        .then(() => router.replace("/(parent)"))
        .catch(() => { /* show error toast */ });
    } else {
      pendingInviteToken = inviteToken;
      router.replace("/auth");
    }
  }
  const sub = Linking.addEventListener("url", handleUrl);
  // Check initial URL only once (cold start via deep link)
  if (!initialUrlHandled.current) {
    initialUrlHandled.current = true;
    Linking.getInitialURL().then((url) => { if (url) handleUrl({ url }); });
  }
  return () => sub.remove();
}, [isAuthenticated, role, token, router]);

// MODIFY existing useEffect (auth guard) — add pending invite check at the top:
useEffect(() => {
  if (isLoading) return;

  // Handle pending invite token (parent just signed in after tapping invite link)
  if (isAuthenticated && role === "parent" && token && pendingInviteToken) {
    const inviteToken = pendingInviteToken;
    clearPendingInviteToken();
    acceptInviteLink(token, inviteToken)
      .then(() => router.replace("/(parent)"))
      .catch(() => router.replace(homePath as Parameters<typeof router.replace>[0]));
    return;
  }

  // ... existing auth guard logic unchanged below ...
  const inAuthGroup = segments[0] === "auth";
  if (!isAuthenticated && !inAuthGroup) {
    router.replace("/auth");
  } else if (isAuthenticated && inAuthGroup && homePath) {
    router.replace(homePath as Parameters<typeof router.replace>[0]);
  }
}, [isAuthenticated, isLoading, role, token, homePath, segments, router]);
```

**Note:** The `acceptInviteLink` import in `_layout.tsx` must come from `invite-service.ts`. Import direction is `_layout.tsx` → `invite-service.ts` (one way only — no risk of circular imports).

**In-Memory Limitation Note:** Deep links require the app to be registered with the scheme. In Expo Go, custom schemes work. The invite link URL (`ilm://invite/{token}` or `teacheros://invite/{token}`) can be pasted into the Expo Go URL bar on simulator for testing.

### Mobile: Teacher Roster — Add Invite Link UI

Extend `apps/mobile/app/(teacher)/class/[classId].tsx` (created in Story 4.7):

```tsx
import { Share } from "react-native";
import * as Clipboard from "expo-clipboard";
import { generateInviteLink } from "../../src/services/invite-service";

// In each student row, add an "Invite Parent" icon button:
// Use a chain-link or person+ icon (Expo vector icons, already available)
// On press: generateInviteLink(token, classId, student.student_id)
//   → show bottom sheet (Tamagui Sheet) with:
//     - Student name + "Share with their parent"
//     - Monospace URL display
//     - [Copy Link] button → Clipboard.setStringAsync(url)
//     - [Share] button → Share.share({ message: `Join ${studentName} on ILM: ${url}` })
//     - [Done] button → close sheet
//   → show Spinner while loading
//   → show error inline if generation fails

// State per-student (or use a single "selected student + loading" approach):
const [inviteSheet, setInviteSheet] = useState<{
  studentId: string;
  studentName: string;
  url: string | null;
  loading: boolean;
  error: string | null;
} | null>(null);
```

**`expo-clipboard` availability — VERIFY BEFORE USE:**
Story 4.7 discovered that `expo-document-picker` was NOT installed despite being bundled with Expo SDK 52 (types were missing, causing `pnpm typecheck` failures). The same risk applies here.

Check if `expo-clipboard` is in `apps/mobile/package.json`. If not, add it:

```bash
# From apps/mobile/
pnpm add expo-clipboard
```

Then import directly:

### Mobile: Student Join Code Screen

Create `apps/mobile/app/(student)/join.tsx`:

```tsx
import { useState } from "react";
import { YStack, XStack, Text, Button, Input, Spinner } from "tamagui";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { colors, spacing, fontSizes } from "@ilm/design-tokens";
import { useAuth } from "../../src/contexts/AuthContext";
import { joinClassByCode, InvalidJoinCodeError, AlreadyEnrolledError } from "../../src/services/onboarding-service";

export default function JoinClassScreen() {
  const { token } = useAuth();
  const router = useRouter();
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleJoin = async () => {
    if (!token || !code.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await joinClassByCode(token, code);
      // Success: navigate to student home (router.back() is unsafe — no guaranteed back stack)
      router.replace("/(student)");
      // Optional: show toast (if a toast system exists — check Story 4.7 patterns first)
    } catch (err) {
      if (err instanceof InvalidJoinCodeError) {
        setError("Invalid or expired join code. Check with your teacher.");
      } else if (err instanceof AlreadyEnrolledError) {
        setError("You are already enrolled in this class.");
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.background }} edges={["top"]}>
      <YStack flex={1} padding={spacing.lg} gap={spacing.lg} backgroundColor={colors.background}>
        <Text fontSize={fontSizes.xl} fontWeight="700" color="$textPrimary">Join a Class</Text>
        <Text fontSize={fontSizes.md} color="$textSecondary">
          Enter the join code from your teacher
        </Text>
        <Input
          placeholder="e.g. A3BX9K"
          value={code}
          onChangeText={(text) => setCode(text.toUpperCase().trim())}
          autoCapitalize="characters"
          maxLength={10}
          fontSize={fontSizes.lg}
          letterSpacing={4}
          textAlign="center"
          borderColor={colors.border}
        />
        {error && (
          <Text color="$red10" fontSize={fontSizes.sm}>{error}</Text>
        )}
        <Button
          onPress={handleJoin}
          disabled={loading || !code.trim()}
          backgroundColor={colors.primary}
          icon={loading ? <Spinner /> : undefined}
        >
          {loading ? "Joining..." : "Join Class"}
        </Button>
        <Button variant="outlined" onPress={() => router.back()}>
          Cancel
        </Button>
      </YStack>
    </SafeAreaView>
  );
}
```

**⚠️ CRITICAL: Hide `join.tsx` from the student tab bar**

The `(student)/_layout.tsx` uses `<Tabs>` navigator. Expo Router **automatically adds every file in the directory as a tab screen**. Creating `join.tsx` will add an unwanted "Join" tab to the student navigation bar. You MUST add this to `apps/mobile/app/(student)/_layout.tsx` inside the `<Tabs>` block:

```tsx
<Tabs.Screen name="join" options={{ href: null }} />
```

`href: null` removes the screen from the tab bar while keeping the route accessible via `router.push("/(student)/join")`. Add it after the existing 4 `<Tabs.Screen>` entries.

---

**Student home: Add "Join a Class" entry point in `apps/mobile/app/(student)/index.tsx`:**

The student home is currently a skeleton screen. Only add a minimal "Join Class" button without replacing the skeleton content:
```tsx
// Add below existing skeleton content:
<Button
  variant="outlined"
  onPress={() => router.push("/(student)/join")}
  borderColor={colors.border}
>
  Join a Class
</Button>
```

### Design Token Reference (CRITICAL — use exact names from `@ilm/design-tokens`)

- `colors.surfaceSecondary` (NOT `surfaceDim`) — hover/pressed states
- `colors.textTertiary` (NOT `textMuted`) — secondary text
- `colors.surface` — card/sheet backgrounds
- `colors.primary` — primary buttons
- `colors.border` — dividers and input borders
- `colors.background` — screen background
- `spacing.sm`, `spacing.md`, `spacing.lg` — gaps and padding
- `fontSizes.sm`, `fontSizes.md`, `fontSizes.lg`, `fontSizes.xl` — text sizes
- `fontWeights.medium`, `fontWeights.bold` — font weight

**Import pattern:**
```typescript
import { colors, spacing, fontSizes, fontWeights } from "@ilm/design-tokens";
```

### Tamagui Component Pattern

Follow patterns established in 4.4–4.7:
```tsx
import { YStack, XStack, Text, Button, Sheet, Input, Spinner } from "tamagui";
import { SafeAreaView } from "react-native-safe-area-context";
// SafeAreaView with edges={["top"]} for content screens
// FlatList: use React Native's FlatList directly (Tamagui doesn't wrap it)
// Wrap list items in XStack/YStack
```

**expo-clipboard** — included in Expo SDK 52, no install needed:
```typescript
import * as Clipboard from "expo-clipboard";
// Usage: await Clipboard.setStringAsync(url);
```

**Share API** — from React Native core, no install needed:
```typescript
import { Share } from "react-native";
// Usage: await Share.share({ message: "Join on ILM: ilm://invite/TOKEN" });
```

### AuthContext: Getting the Token

```typescript
const { token, role } = useAuth();
// token is string | null — check before making API calls
// role is UserRole | null
```

### What NOT to Do

- **Do NOT implement the guided onboarding wizard** — multi-step onboarding flow is Story 4.9.
- **Do NOT implement COPPA consent gate** — Story 4.10.
- **Do NOT create a full web landing page for invite links** — the mobile deep link (`ilm://`) is sufficient for this story.
- **Do NOT implement push notifications** for invite acceptance — messaging/notifications are Epic 8.
- **Do NOT modify auth domain** — `parent@example.com` (usr_parent_1) is already seeded; use as test parent.
- **Do NOT add universal links (HTTPS domain links)** — `ilm://` scheme deep links are sufficient for MVP.
- **Do NOT implement `guardian_student_links` in the auth repository** — keep it in the onboarding repository to maintain domain separation.
- **Do NOT create student user accounts in Story 4.8** — `StudentRecord` is a lightweight enrollment record. The `join_by_code` flow maps the auth user (`student_user_id` from JWT) to the class, but does NOT create a new `StudentRecord` unless needed.
- **Do NOT rewrite `_layout.tsx` auth guard logic** — only ADD the invite deep link handling on top of it; preserve existing behavior exactly.
- **Do NOT process the invite link on the server during sign-up** — the accept step is a separate POST after authentication; server does not auto-accept on account creation.

### Previous Story Intelligence (Story 4.7)

**Patterns confirmed in Story 4.7:**
- `apiRequest()` from `api-client.ts` handles GET/POST/DELETE with token — works as expected
- Error class pattern: throw typed domain errors from service layer, catch in UI for user messages
- `useAuth()` provides `token`, `role`, `user`, `signOut`
- Tamagui `Sheet` (bottom sheet) is available and working for modals/overlays
- `expo-haptics` available: use `Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light)` for primary actions
- File structure: `apps/mobile/src/services/` for service files
- Naming: `kebab-case.ts` for TS files, `PascalCase.tsx` for components
- `pnpm typecheck` must pass with zero TypeScript errors before marking done

**In-Memory Repository Pattern (from Story 4.7 + auth domain):**
```python
class InMemoryOnboardingRepository:
    _classes: dict[str, ClassRecord] = {}
    _students: dict[str, StudentRecord] = {}
    _enrollments: list[EnrollmentRecord] = []
    # ↑ These exist from Story 4.7. ADD the following for 4.8:
    _invite_links: dict[str, InviteLinkRecord] = {}      # key: token
    _guardian_links: list[GuardianStudentLinkRecord] = []
    _invite_seq: int = 0
    _guardian_link_seq: int = 0
```

Always follow the `InMemoryAuthRepository` pattern:
- Class-level dicts (shared state across instances)
- `_ensure_seed_data()` with `_seeded` guard
- Frozen dataclasses (replace entire record to "update")
- `reset_state()` must reset ALL class-level state

### Project Structure Notes

**New files to create:**
```
apps/mobile/app/(student)/join.tsx
apps/mobile/src/services/invite-service.ts
```

**Files to modify:**
```
apps/api/app/domains/onboarding/models.py         # ADD: InviteLinkRecord, GuardianStudentLinkRecord
apps/api/app/domains/onboarding/repository.py     # ADD: invite/guardian methods + seed data
apps/api/app/domains/onboarding/schemas.py        # ADD: invite/join schemas
apps/api/app/domains/onboarding/service.py        # ADD: invite/join business logic
apps/api/app/domains/onboarding/router.py         # ADD: invite/join endpoints
packages/contracts/src/onboarding.ts              # ADD: invite/join TypeScript types
packages/contracts/src/index.ts                   # ADD: new type exports
apps/mobile/src/services/onboarding-service.ts    # ADD: joinClassByCode function
apps/mobile/app/(teacher)/class/[classId].tsx     # ADD: invite link generation UI
apps/mobile/app/(student)/index.tsx               # ADD: "Join a Class" button (minimal)
apps/mobile/app/_layout.tsx                       # ADD: deep link handler
apps/mobile/app.json                              # ADD: scheme + intentFilters
```

**Naming conventions (from architecture.md):**
- Python files: `snake_case.py`
- Python classes: `PascalCase`
- Python functions/vars: `snake_case`
- TypeScript files: `kebab-case.ts`
- TypeScript components: `PascalCase.tsx`
- TypeScript vars/functions: `camelCase`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.8] — Story requirements and acceptance criteria
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 4] — Epic objective: teachers generate parent invite links and student join codes
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Layer] — `invite_links(id, org_id, type, target_student_id, token, expires_at, accepted_at)`, `guardian_student_links(guardian_id, student_id, linked_via)` schema
- [Source: _bmad-output/planning-artifacts/architecture.md#API Boundaries] — `/onboarding/*` prefix for invite links and join codes
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Flow 2] — "Parent First Visit: Invite Link → Sign In → Child pre-linked → Dashboard visible"
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Zero-Friction Flows] — "Parent sign-up via invite link: Tap invite link → Google sign-in → child already linked → dashboard visible. No manual child-linking."
- [Source: _bmad-output/implementation-artifacts/4-7-teacher-class-setup-and-student-management.md] — Onboarding domain patterns, InMemoryOnboardingRepository structure, design token corrections
- [Source: apps/api/app/domains/auth/repository.py] — InMemoryAuthRepository pattern to follow exactly
- [Source: apps/api/app/domains/onboarding/] — Domain created in Story 4.7 (verify exists before starting)
- [Source: apps/mobile/src/services/auth-service.ts] — Error class + typed error pattern
- [Source: apps/mobile/src/services/api-client.ts] — `apiRequest()` usage, `ApiError` class, `API_BASE_URL`
- [Source: apps/mobile/src/contexts/AuthContext.tsx] — `useAuth()` API: token, role, isAuthenticated, homePath
- [Source: apps/mobile/app/_layout.tsx] — Root layout + AuthGuard: must extend, not replace
- [Source: apps/mobile/app/(teacher)/class/[classId].tsx] — Teacher roster screen from Story 4.7 (add invite link UI to this file)
- [Source: apps/mobile/app/(student)/index.tsx] — Student home screen (add "Join a Class" CTA)

## Senior Developer Review (AI)

- Reviewer: elephant
- Date: 2026-03-23
- Outcome: Approved after fixes
- Summary: 3 High and 2 Medium findings fixed in code and validated. 34 onboarding API tests pass and mobile typecheck passes.
- Issues Fixed: 5 (High/Medium)
- Action Items Created: 0

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- expo-clipboard was not installed despite Expo SDK 52 bundle claim (same as expo-document-picker in 4.7). Added via `pnpm add expo-clipboard` in apps/mobile.
- `usr_parent_2` does not exist in InMemoryAuthRepository seed — `require_authenticated_actor` returns 403 for unregistered users even with valid JWT. Test for "already_used → 400" uses same parent (usr_parent_1) since `used_at` check fires before the linked check.
- Deep link scheme changed from `teacheros` to `ilm` (Option A) per story recommendation.

### Completion Notes List

- Implemented InviteLinkRecord and GuardianStudentLinkRecord models in models.py
- Extended InMemoryOnboardingRepository with invite link and guardian link CRUD, class join-by-code, and seed data (inv_demo_abc123 for stu_1/cls_1)
- Added 5 new Pydantic schemas to schemas.py; 4 new API endpoints to router.py; 4 new service methods to service.py
- Added 5 TypeScript interfaces to contracts/onboarding.ts and updated index.ts exports
- Created apps/mobile/src/services/invite-service.ts with generateInviteLink, resolveInviteLink, acceptInviteLink
- Extended onboarding-service.ts with joinClassByCode, InvalidJoinCodeError, AlreadyEnrolledError
- Extended teacher roster [classId].tsx with per-student "Invite" button and invite link Tamagui Sheet (copy + share)
- Created apps/mobile/app/(student)/join.tsx join code screen with auto-uppercase input and error handling
- Updated (student)/_layout.tsx to hide join route from tab bar; added "Join a Class" CTA to student index
- Updated app.json: scheme changed from "teacheros" to "ilm", added Android intentFilters for deep links
- Updated _layout.tsx AuthGuard with deep link listener, initialUrlHandled ref guard, and pending invite token flow
- Enforced invite org consistency and fixed join-by-code identity mapping
- Added explicit invite deep-link user messaging for already used/expired/already linked scenarios
- Aligned join code max length to 6 across mobile input and backend schema; updated invalid-code test fixture accordingly
- 34 backend tests all pass (20 pre-existing + 14 new); pnpm typecheck passes with zero errors

### File List

- apps/api/app/domains/onboarding/models.py
- apps/api/app/domains/onboarding/repository.py
- apps/api/app/domains/onboarding/schemas.py
- apps/api/app/domains/onboarding/service.py
- apps/api/app/domains/onboarding/router.py
- apps/api/tests/test_onboarding_api.py
- packages/contracts/src/onboarding.ts
- packages/contracts/src/index.ts
- apps/mobile/src/services/invite-service.ts (new)
- apps/mobile/src/services/onboarding-service.ts
- apps/mobile/app/(teacher)/class/[classId].tsx
- apps/mobile/app/(teacher)/index.tsx
- apps/mobile/app/(student)/join.tsx (new)
- apps/mobile/app/(student)/_layout.tsx
- apps/mobile/app/(student)/index.tsx
- apps/mobile/app/_layout.tsx
- apps/mobile/app.json
- apps/mobile/package.json

## Change Log

- 2026-03-23: Story 4.8 implemented — invite link generation and acceptance, student join codes, deep link handling. 14 new tests added. pnpm typecheck passes. Status → review.
- 2026-03-23: Senior Developer Review (AI) completed. Action-item mode selected; added follow-ups and set Status → in-progress.
- 2026-03-23: High/Medium review findings fixed, validation rerun (34 API tests + mobile typecheck), Status → done.
