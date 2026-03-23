# Story 4.7: Teacher Class Setup and Student Management

Status: done

## Story

As a teacher,
I want to create classes and add students manually or via CSV import,
So that I can set up my classroom and begin using the platform.

## Acceptance Criteria

1. **Create class with name and subject:**
   Given an authenticated teacher,
   When they create a new class with name and subject,
   Then the class is persisted under their organization scope,
   And a unique join code is generated for the class.

2. **Add student manually:**
   Given a teacher with an existing class,
   When they add a student manually by entering name and grade level,
   Then the student is enrolled in the class,
   And linked to the teacher's organization.

3. **CSV import of students:**
   Given a teacher with an existing class,
   When they upload a CSV file with student names and grade levels,
   Then the system validates the CSV format and creates/enrolls all valid students,
   And displays a summary showing successful imports and any validation errors with row numbers.

4. **View and manage class roster:**
   Given a teacher viewing their class roster,
   When they view the class management screen,
   Then they see all enrolled students with names and status,
   And can remove a student from the class.

## Tasks / Subtasks

### Backend: New `onboarding` domain

- [x] Task 1: Create `apps/api/app/domains/onboarding/` domain (AC: #1, #2, #3, #4)
  - [x] Create `models.py` with `ClassRecord` and `StudentRecord` and `EnrollmentRecord` dataclasses
  - [x] Create `repository.py` with `OnboardingRepository` Protocol + `InMemoryOnboardingRepository` (follow InMemoryAuthRepository pattern with class-level dicts + seeded data)
  - [x] Create `schemas.py` with all Pydantic request/response models
  - [x] Create `service.py` with `OnboardingService` business logic
  - [x] Create `router.py` with FastAPI endpoints
  - [x] Create `__init__.py` (empty)

- [x] Task 2: Register onboarding router in `apps/api/app/main.py` (AC: all)
  - [x] Add `from app.domains.onboarding.router import router as onboarding_router`
  - [x] Add `app.include_router(onboarding_router)`

### Contracts: New types

- [x] Task 3: Add class/student contract types in `packages/contracts/src/` (AC: all)
  - [x] Create `packages/contracts/src/onboarding.ts` with all interfaces
  - [x] Export from `packages/contracts/src/index.ts`

### Mobile: Teacher home + class management UI

- [x] Task 4: Replace teacher home skeleton with class list (AC: #1, #4)
  - [x] Create `apps/mobile/src/services/onboarding-service.ts` with API call functions
  - [x] Update `apps/mobile/app/(teacher)/index.tsx` to show real class list
  - [x] Add "Create Class" flow (modal or stack screen)
  - [x] Display class cards with name, subject, student count, join code

- [x] Task 5: Class detail / roster screen (AC: #2, #3, #4)
  - [x] Create `apps/mobile/app/(teacher)/class/[classId].tsx` (or modal) for class roster
  - [x] Show enrolled student list (name, grade level)
  - [x] "Add Student" button → manual entry form
  - [x] "Import CSV" button → document picker → POST to backend → show import summary
  - [x] Remove student via swipe or button

- [x] Task 6: TypeScript verification (AC: all)
  - [x] Run `pnpm typecheck` from monorepo root — must pass with zero errors
  - [x] Verify `expo-document-picker` is available (included in Expo SDK 52)

## Dev Notes

### Architecture: API Endpoint Design

The architecture spec maps class setup, CSV import, and invite links to the `/onboarding/*` prefix:
> `/onboarding/*` (invite links, join codes, guided setup, CSV import)

**Endpoints for this story:**

```
POST   /onboarding/classes                              → Create class → returns ClassResponse with join_code
GET    /onboarding/classes                              → List teacher's classes (teacher-scoped)
GET    /onboarding/classes/{class_id}/roster            → Get all students in class
POST   /onboarding/classes/{class_id}/students          → Add student manually
DELETE /onboarding/classes/{class_id}/students/{student_id} → Remove student from class
POST   /onboarding/classes/{class_id}/students/import   → CSV import (multipart/form-data)
```

All endpoints require `Authorization: Bearer {token}` and `role == "teacher"`.

**Do NOT use `/courses` prefix** — that domain is exclusively for AI lesson draft generation.

### Data Model (In-Memory Repository)

Follow `InMemoryAuthRepository` pattern exactly: class-level dicts, class-level sequence counter, `_seeded` guard.

```python
# models.py
from dataclasses import dataclass

@dataclass(frozen=True)
class ClassRecord:
    class_id: str        # e.g., "cls_1"
    org_id: str
    teacher_user_id: str
    name: str            # e.g., "Math Period 3"
    subject: str         # e.g., "Mathematics"
    join_code: str       # e.g., "A3BX9K" — 6-char uppercase alphanumeric
    created_at: str      # ISO 8601 UTC

@dataclass(frozen=True)
class StudentRecord:
    student_id: str      # e.g., "stu_1"
    org_id: str
    name: str            # full name, e.g., "Jane Smith"
    grade_level: str     # e.g., "Grade 5", "Year 7", "10th Grade"
    created_at: str

@dataclass(frozen=True)
class EnrollmentRecord:
    enrollment_id: str   # e.g., "enr_1"
    class_id: str
    student_id: str
    org_id: str
    enrolled_by: str     # teacher user_id
    created_at: str
```

**Join code generation:**
```python
import secrets
import string

def _generate_join_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(6))
```

**Seed data for in-memory repo:**
```python
# Seed one class for teacher@example.com (usr_teacher_1 / org_demo_1) for easier testing
ClassRecord(
    class_id="cls_1",
    org_id="org_demo_1",
    teacher_user_id="usr_teacher_1",
    name="Math Period 3",
    subject="Mathematics",
    join_code="A3BX9K",
    created_at="2026-03-01T08:00:00Z",
)
```

### Pydantic Schemas (Backend)

```python
# schemas.py
from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated
from pydantic import StringConstraints

class ClassCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Annotated[str, StringConstraints(min_length=1, max_length=100)]
    subject: Annotated[str, StringConstraints(min_length=1, max_length=100)]

class ClassResponse(BaseModel):
    class_id: str
    org_id: str
    teacher_user_id: str
    name: str
    subject: str
    join_code: str
    student_count: int
    created_at: str

class ClassListResponse(BaseModel):
    classes: list[ClassResponse]

class StudentCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Annotated[str, StringConstraints(min_length=1, max_length=200)]
    grade_level: Annotated[str, StringConstraints(min_length=1, max_length=50)]

class StudentResponse(BaseModel):
    student_id: str
    name: str
    grade_level: str
    org_id: str
    created_at: str

class RosterResponse(BaseModel):
    class_id: str
    students: list[StudentResponse]

class CsvImportRowResult(BaseModel):
    row: int
    success: bool
    student_name: str | None
    error: str | None

class CsvImportResponse(BaseModel):
    total_rows: int
    successful: int
    failed: int
    results: list[CsvImportRowResult]
```

### CSV Import: Backend Logic

The backend receives `multipart/form-data` with a `file` field. Expected CSV format:

```
name,grade_level
Jane Smith,Grade 5
John Doe,Grade 5
```

Backend validation rules:
- Must have `name` and `grade_level` columns (case-insensitive header match)
- `name`: non-empty, max 200 chars
- `grade_level`: non-empty, max 50 chars
- Rows with errors are skipped (not enrolled); valid rows are enrolled
- Report row numbers in results (1-indexed, excluding header = row 1 is first data row)
- Maximum 200 rows per import (return 400 if exceeded)

**Router endpoint for CSV import:**
```python
from fastapi import File, UploadFile
import csv
import io

@router.post("/classes/{class_id}/students/import", response_model=CsvImportResponse)
async def import_students_csv(
    class_id: str,
    file: UploadFile = File(...),
    actor: ActorContext = Depends(require_authenticated_actor),
    service: OnboardingService = Depends(get_onboarding_service),
) -> CsvImportResponse:
    _require_teacher(actor)
    content = await file.read()
    text = content.decode("utf-8-sig")  # utf-8-sig strips BOM from Excel-exported CSVs
    return service.import_students_csv(
        actor_user_id=actor.user_id,
        actor_org_id=actor.org_id,
        class_id=class_id,
        csv_text=text,
    )
```

### Service Layer: Business Rules

```python
# Error classes
class ClassNotFoundError(Exception): pass
class ClassAccessError(Exception): pass  # Teacher doesn't own this class
class StudentNotFoundError(Exception): pass
class StudentNotEnrolledError(Exception): pass
```

- Teachers can only manage classes they created (verify `teacher_user_id == actor.user_id`)
- Students are org-scoped — reuse student if same name+grade already exists in org (idempotent CSV imports)
- `student_count` in ClassResponse = count of active enrollments for that class
- Removing a student deletes the EnrollmentRecord (not the StudentRecord — student may be in other classes)

### Contracts: TypeScript Types

Create `packages/contracts/src/onboarding.ts`:

```typescript
/** POST /onboarding/classes request body */
export interface ClassCreateRequest {
  name: string;
  subject: string;
}

/** Class resource */
export interface ClassResponse {
  class_id: string;
  org_id: string;
  teacher_user_id: string;
  name: string;
  subject: string;
  join_code: string;
  student_count: number;
  created_at: string;
}

export interface ClassListResponse {
  classes: ClassResponse[];
}

/** POST /onboarding/classes/{classId}/students request body */
export interface StudentCreateRequest {
  name: string;
  grade_level: string;
}

export interface StudentResponse {
  student_id: string;
  name: string;
  grade_level: string;
  org_id: string;
  created_at: string;
}

export interface RosterResponse {
  class_id: string;
  students: StudentResponse[];
}

export interface CsvImportRowResult {
  row: number;
  success: boolean;
  student_name: string | null;
  error: string | null;
}

export interface CsvImportResponse {
  total_rows: number;
  successful: number;
  failed: number;
  results: CsvImportRowResult[];
}
```

Export from `packages/contracts/src/index.ts`:
```typescript
export type {
  ClassCreateRequest, ClassResponse, ClassListResponse,
  StudentCreateRequest, StudentResponse, RosterResponse,
  CsvImportRowResult, CsvImportResponse,
} from "./onboarding";
```

### Mobile: Service Layer

Create `apps/mobile/src/services/onboarding-service.ts`:

```typescript
import type {
  ClassCreateRequest, ClassResponse, ClassListResponse,
  StudentCreateRequest, RosterResponse, CsvImportResponse,
} from "@ilm/contracts";
import { apiRequest, ApiError } from "./api-client";

export class ClassNotFoundError extends Error {
  name = "ClassNotFoundError" as const;
}
export class ClassAccessError extends Error {
  name = "ClassAccessError" as const;
}

export async function createClass(
  token: string,
  data: ClassCreateRequest,
): Promise<ClassResponse> {
  return apiRequest<ClassResponse>("/onboarding/classes", {
    method: "POST",
    body: data,
    token,
  });
}

export async function listClasses(token: string): Promise<ClassListResponse> {
  return apiRequest<ClassListResponse>("/onboarding/classes", { token });
}

export async function getRoster(token: string, classId: string): Promise<RosterResponse> {
  return apiRequest<RosterResponse>(`/onboarding/classes/${classId}/roster`, { token });
}

export async function addStudent(
  token: string,
  classId: string,
  data: StudentCreateRequest,
): Promise<void> {
  await apiRequest(`/onboarding/classes/${classId}/students`, {
    method: "POST",
    body: data,
    token,
  });
}

export async function removeStudent(
  token: string,
  classId: string,
  studentId: string,
): Promise<void> {
  await apiRequest(`/onboarding/classes/${classId}/students/${studentId}`, {
    method: "DELETE",
    token,
  });
}

export async function importStudentsCsv(
  token: string,
  classId: string,
  fileUri: string,
  fileName: string,
): Promise<CsvImportResponse> {
  const formData = new FormData();
  formData.append("file", {
    uri: fileUri,
    name: fileName,
    type: "text/csv",
  } as unknown as Blob);

  const response = await fetch(
    `${/* API_BASE_URL */""}/onboarding/classes/${classId}/students/import`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    },
  );
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new ApiError(String(response.status), err.detail ?? "Import failed", response.status);
  }
  return response.json() as Promise<CsvImportResponse>;
}
```

**Note on `importStudentsCsv`:** The `API_BASE_URL` constant is not exported from `api-client.ts`. Options:
1. Export `API_BASE_URL` from `api-client.ts` (preferred — single source of truth)
2. Duplicate the base URL resolution logic in `onboarding-service.ts`

**Choose Option 1:** Add `export const API_BASE_URL = ...` to `api-client.ts` and import in `onboarding-service.ts`.

### Mobile: Teacher Home Screen

Replace the skeleton in `apps/mobile/app/(teacher)/index.tsx` with a class list:

```tsx
// Uses: AuthContext (for token), onboarding-service (for listClasses)
// UI pattern: FlatList of class cards, each showing name, subject, student count, join code
// "+" FAB or header button to create a new class
// Tap class → navigate to class detail (roster)
```

**Create class modal pattern:**
- Use Tamagui `Sheet` component (bottom sheet) or push a new route
- Form: name (TextInput), subject (TextInput), "Create" button
- On success: invalidate/refetch class list, show join code in confirmation

**Class card UI:**
```tsx
// Each class card shows:
// - Class name (large text)
// - Subject (secondary text)
// - "X students" count
// - Join code badge: "Code: A3BX9K" (monospace or badge style)
```

### Mobile: Class Roster Screen

Create `apps/mobile/app/(teacher)/class/[classId].tsx` (dynamic route in Expo Router):

- **Route structure:** Expo Router supports `app/(teacher)/class/[classId].tsx`
- **Navigation:** `router.push(`/(teacher)/class/${classId}`)` from teacher home
- The `(teacher)` group layout does NOT apply to sub-routes by default — use `Stack` if needed
- **Alternatively:** Use `router.push({ pathname: "/(teacher)/class/[classId]", params: { classId } })`

**Roster screen layout:**
```
[Header: Class Name] [Back button]
[Subject badge] [Join code badge]
[Add Student] [Import CSV] — action buttons
[Separator]
[FlatList of student rows]
  Row: name, grade_level, [Remove] button
[Empty state: "No students yet. Add your first student above."]
```

**CSV import flow:**
```typescript
import * as DocumentPicker from "expo-document-picker";

const handleImportCsv = async () => {
  const result = await DocumentPicker.getDocumentAsync({
    type: ["text/csv", "text/comma-separated-values"],
    copyToCacheDirectory: true,
  });
  if (result.canceled) return;
  const file = result.assets[0];
  const importResult = await importStudentsCsv(token, classId, file.uri, file.name);
  // Show summary modal/sheet
};
```

**CSV summary display after import:**
```
✅ 18 students imported successfully
⚠️  2 rows had errors:
   Row 3: Missing grade_level
   Row 7: Name too long (max 200 characters)
```

### Design Token Reference (CRITICAL — from Story 4.5/4.6 corrections)

**Use these exact token names from `@ilm/design-tokens`:**
- `colors.surfaceSecondary` (NOT `surfaceDim`) — for hover/pressed states
- `colors.textTertiary` (NOT `textMuted`) — for secondary text
- `colors.surface` — for card/sheet backgrounds
- `colors.primary` — for primary action buttons
- `colors.border` — for dividers and input borders
- `spacing.sm`, `spacing.md`, `spacing.lg` — for gaps and padding
- `fontSizes.sm`, `fontSizes.md`, `fontSizes.lg` — for text sizes
- `fontWeights.medium`, `fontWeights.bold` — for font weight

**Import pattern:**
```typescript
import { colors, spacing, fontSizes, fontWeights } from "@ilm/design-tokens";
```

### Tamagui Component Pattern (established in 4.4–4.6)

Use Tamagui components — NOT React Native primitives:
```tsx
import { YStack, XStack, Text, Button, Sheet, Input, Spinner } from "tamagui";
import { SafeAreaView } from "react-native-safe-area-context";
// SafeAreaView with edges={["top"]} for content screens
// edges={["top", "bottom"]} for full-screen flows
```

**FlatList note:** Tamagui doesn't wrap `FlatList` — use React Native's `FlatList` directly for the student roster list. Wrap items in `XStack`/`YStack`.

### Expo Document Picker

`expo-document-picker` is part of Expo SDK 52 and does NOT require a native build — it works in Expo Go. No installation needed. Import directly:

```typescript
import * as DocumentPicker from "expo-document-picker";
```

On iOS, the document picker opens Files app. On Android, it opens the system file picker. The `type` filter for CSV:
- `"text/csv"` — standard MIME type
- `"text/comma-separated-values"` — some systems use this
- Pass both in array for maximum compatibility

### AuthContext: Getting the Token

The token is available via `useAuth()`:
```typescript
const { token } = useAuth();
// token is string | null — check before making API calls
// If null, the auth guard in _layout.tsx should have redirected; add defensive check
```

### Error Handling Pattern (from auth-service.ts)

Follow the same error class + switch pattern:
```typescript
try {
  return await apiRequest<ClassResponse>("/onboarding/classes", { ... });
} catch (error) {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 403: throw new ClassAccessError("You don't have permission to manage this class.");
      case 404: throw new ClassNotFoundError("Class not found.");
    }
  }
  throw error; // NetworkError or unknown — let caller handle
}
```

### Project Structure Notes

**New files to create:**
```
apps/api/app/domains/onboarding/__init__.py
apps/api/app/domains/onboarding/models.py
apps/api/app/domains/onboarding/repository.py
apps/api/app/domains/onboarding/schemas.py
apps/api/app/domains/onboarding/service.py
apps/api/app/domains/onboarding/router.py
packages/contracts/src/onboarding.ts
apps/mobile/src/services/onboarding-service.ts
apps/mobile/app/(teacher)/class/[classId].tsx
```

**Files to modify:**
```
apps/api/app/main.py                        # ADD: onboarding router
packages/contracts/src/index.ts             # ADD: onboarding type exports
apps/mobile/app/(teacher)/index.tsx         # REPLACE: skeleton with class list
apps/mobile/src/services/api-client.ts      # ADD: export API_BASE_URL (for multipart in onboarding-service)
```

**Naming conventions (from architecture.md):**
- Python files: `snake_case.py`
- Python classes: `PascalCase`
- Python functions/vars: `snake_case`
- TypeScript files: `kebab-case.ts`
- TypeScript components: `PascalCase.tsx`
- TypeScript vars/functions: `camelCase`

### What NOT to Do

- **Do NOT create student user accounts** — `StudentRecord` is a lightweight enrollment record (name, grade_level), NOT a full auth user. Full student user accounts (for sign-in) are out of scope for this story.
- **Do NOT implement invite links or join code redemption** — the join code is generated and displayed, but the logic for a student to USE the join code is Story 4.8.
- **Do NOT implement the onboarding wizard flow** — guided multi-step onboarding is Story 4.9.
- **Do NOT implement COPPA consent gating** — that is Story 4.10.
- **Do NOT put class management under `/courses`** — that domain is exclusively for AI lesson draft generation (Epic 6).
- **Do NOT add class picker to the Plan or Grade screens** — those screens will reference classes in later epics.
- **Do NOT use `npx expo install expo-document-picker`** — it's already bundled with Expo SDK 52.
- **Do NOT process CSV on mobile** — send raw CSV bytes to backend; let backend validate and parse.
- **Do NOT store the full CSV in SecureStore** — it's ephemeral for import; no persistence needed.
- **Do NOT rewrite the teacher `_layout.tsx`** — keep the tab structure intact, only replace content in `index.tsx`.
- **Do NOT modify the auth domain** — teacher authentication is complete.

### Previous Story Intelligence (Story 4.6)

**Critical fixes applied in Story 4.6 code review (H1, H2):**
- H1: `networkErrorSource` state pattern to track which flow (email vs Google) triggered a network error for proper retry routing — apply analogous pattern for class management screens if multiple async actions coexist
- H2: `PlayServicesUnavailableError` added to `auth-service.ts` — not relevant to this story

**Established patterns confirmed working:**
- `apiRequest()` from `api-client.ts` handles GET/POST/DELETE with token; works exactly as expected
- Error class pattern: throw typed errors from service layer, catch in UI layer for user-friendly messages
- `useAuth()` from `AuthContext` provides `token`, `user`, `signOut` — use `token` for all authenticated requests
- Tamagui `Sheet` (bottom sheet) is available and working for modals
- `expo-haptics` (`Haptics.selectionAsync()`) used for tab press — use `Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light)` for form submit button press feedback
- File structure: `apps/mobile/src/services/` for service files, `apps/mobile/src/contexts/` for contexts, `apps/mobile/src/components/` for shared components

**Git context (last commits):**
- `f8f7e897 4.4 done, .gitignore removed to sync` — 4.4 mobile shell complete
- `c023b151 story 4.3 completed` — DB migrations complete (Epic 3 context, not directly relevant)

**What 4.6 confirmed is working end-to-end:**
- `apiRequest()` with `token` parameter for authenticated calls
- `packages/contracts` types used across mobile without issues
- `pnpm typecheck` must pass with zero TypeScript errors before marking done

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.7] — Story requirements and acceptance criteria
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 4] — Epic objective: teachers create classes, generate parent invite links, generate student join codes
- [Source: _bmad-output/planning-artifacts/architecture.md#API Boundaries] — `/onboarding/*` prefix for class setup and CSV import
- [Source: _bmad-output/planning-artifacts/architecture.md#Core Domain Model] — `classes`, `enrollments`, `students` tables in target schema
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns] — Naming conventions, error format, database naming
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure] — Directory layout, feature-to-epic domain mapping
- [Source: apps/api/app/domains/auth/repository.py] — InMemoryAuthRepository pattern to follow exactly
- [Source: apps/api/app/domains/auth/models.py] — Dataclass record pattern
- [Source: apps/api/app/domains/courses/router.py] — FastAPI router pattern, `_require_teacher()` guard pattern
- [Source: apps/api/app/domains/courses/schemas.py] — Pydantic schema patterns (`ConfigDict(extra="forbid")`, `StringConstraints`)
- [Source: apps/api/app/main.py] — Router registration pattern
- [Source: apps/mobile/src/services/auth-service.ts] — Error class + typed error pattern for service layer
- [Source: apps/mobile/src/services/api-client.ts] — `apiRequest()` usage, `ApiError` class
- [Source: apps/mobile/app/(teacher)/_layout.tsx] — Tab structure (do not modify)
- [Source: apps/mobile/app/(teacher)/index.tsx] — Current teacher home (replace skeleton content)
- [Source: _bmad-output/implementation-artifacts/4-6-google-sign-in-on-mobile.md] — Design token corrections, established Tamagui patterns, `useAuth()` token access

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Code Review Fixes (claude-sonnet-4-6)

- H1: Added `className: item.name` to class roster navigation params — header now shows actual class name instead of "Class Roster".
- M1: Removed unused `import io` from `router.py`.
- M2+M7: Added `actor_org_id` parameter to `_get_owned_class` with explicit org-scope check (`cls.org_id != actor_org_id`). Updated all callers to pass `actor_org_id`.
- M3: Added `actor_org_id` to `remove_student` service method and router call for consistency with org-scope enforcement.
- M3 (stale count): Replaced `useEffect` with `useFocusEffect` in teacher home — class list now refreshes on back-navigation from roster screen, keeping `student_count` accurate.
- M4: Added `Alert.alert` after successful class creation to display the join code immediately.
- M5: Added `test_csv_import_too_many_rows_returns_error_summary` test covering the 200-row limit.
- M6: Made `_csv_upload` test helper `async def` with `await` — corrects the misleading sync wrapper pattern.

### Completion Notes List

- Implemented full onboarding domain (models, repository, schemas, service, router) following InMemoryAuthRepository class-level dict pattern with `_seeded` guard and `reset_state()` for tests.
- All 6 REST endpoints implemented under `/onboarding/*` prefix with teacher-role enforcement.
- CSV import supports case-insensitive headers, BOM stripping (utf-8-sig), per-row error reporting, 200-row limit, and idempotent student creation (same name+grade_level reuses existing StudentRecord).
- Teacher home replaced with FlatList of class cards (name, subject, student count, join code badge) + Tamagui Sheet create-class modal.
- Class roster screen at `(teacher)/class/[classId].tsx` with add-student sheet, CSV document picker via `expo-document-picker`, import summary sheet, and remove-student confirmation dialog.
- `expo-document-picker` added to `apps/mobile/package.json` (was not installed despite being in Expo SDK 52 — types were missing).
- `API_BASE_URL` exported from `api-client.ts` for use in multipart form-data fetch in `onboarding-service.ts`.
- Stack layout added at `(teacher)/class/_layout.tsx` to enable correct nested navigation within the Tabs group.
- `pnpm typecheck` passes with zero errors across all packages.
- 19 new backend API tests covering create/list/roster/add/remove/CSV-import scenarios; all pass. No regressions in existing test suite (pre-existing failures in `test_db_models` and 2 auth home-path assertions are unrelated to this story).

### File List

**New files:**

- `apps/api/app/domains/onboarding/__init__.py`
- `apps/api/app/domains/onboarding/models.py`
- `apps/api/app/domains/onboarding/repository.py`
- `apps/api/app/domains/onboarding/schemas.py`
- `apps/api/app/domains/onboarding/service.py`
- `apps/api/app/domains/onboarding/router.py`
- `packages/contracts/src/onboarding.ts`
- `apps/mobile/src/services/onboarding-service.ts`
- `apps/mobile/app/(teacher)/class/_layout.tsx`
- `apps/mobile/app/(teacher)/class/[classId].tsx`
- `apps/api/tests/test_onboarding_api.py`

**Modified files:**

- `apps/api/app/main.py`
- `packages/contracts/src/index.ts`
- `apps/mobile/app/(teacher)/index.tsx`
- `apps/mobile/src/services/api-client.ts`
- `apps/mobile/package.json`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
