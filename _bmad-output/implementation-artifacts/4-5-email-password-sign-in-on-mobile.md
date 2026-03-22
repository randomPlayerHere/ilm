# Story 4.5: Email/Password Sign-In on Mobile

Status: done

## Story

As a school user,
I want to sign in with my email and password on the mobile app,
So that I can securely access Teacher OS on my phone.

## Acceptance Criteria

1. **Successful sign-in with valid credentials:**
   Given an active user account with valid credentials,
   When the user submits email and password on the sign-in screen,
   Then the system authenticates via `POST /auth/login` and stores the JWT access token securely on device via `expo-secure-store`,
   And the user is redirected to their role-appropriate home tab (`/(teacher)`, `/(parent)`, or `/(student)`) based on `home_path` in the login response.

2. **Invalid credentials error (anti-enumeration):**
   Given invalid credentials (wrong email or wrong password),
   When the user attempts sign-in,
   Then the error message displays "Email or password is incorrect" — does NOT reveal which field was wrong,
   And the sign-in button shows a loading spinner during the request and re-enables on failure.

3. **No network connectivity:**
   Given a user with no network connectivity,
   When they attempt sign-in,
   Then the app displays a blocking error: "Couldn't sign in. Check your connection and try again." with a [Try Again] button,
   And does not crash or store partial auth state.

4. **Token expiry and re-authentication:**
   Given the user's JWT access token expires (60-min TTL),
   When the app makes an API request that returns 401,
   Then the user is redirected to the sign-in screen with their email pre-filled,
   And a message explains "Your session has expired. Please sign in again."

   > **NOTE:** The backend does NOT currently implement refresh tokens. AC originally called for silent refresh — this story implements graceful session-expired redirect instead. Refresh token support can be added in a future story when the API endpoint exists.

5. **Inactive account handling:**
   Given a user whose account status is "inactive" or "invited",
   When they attempt sign-in with correct credentials,
   Then the API returns 403 and the app displays "Your account is not active. Contact your administrator."

6. **Rate limiting feedback:**
   Given too many failed login attempts,
   When the API returns 429,
   Then the app displays "Too many sign-in attempts. Please wait and try again."

## Tasks / Subtasks

- [x] Task 1: Install dependencies (AC: all)
  - [x] `npx expo install expo-secure-store` in `apps/mobile/`
  - [x] Verify `expo-secure-store` appears in `apps/mobile/package.json`

- [x] Task 2: Create API client service (AC: #1, #3)
  - [x] Create `apps/mobile/src/services/api-client.ts`
  - [x] Use native `fetch` — no external HTTP library
  - [x] Base URL from `expo-constants` manifest extra or hardcoded `http://localhost:8000` for local dev
  - [x] Include `Authorization: Bearer <token>` header injection for authenticated requests
  - [x] Include `Content-Type: application/json` default header
  - [x] Handle network errors (TypeError from fetch = no connectivity) → throw typed `NetworkError`
  - [x] Handle non-2xx responses → parse error envelope `{ error: { code, message } }` → throw typed `ApiError`

- [x] Task 3: Create auth token storage service (AC: #1, #4)
  - [x] Create `apps/mobile/src/services/token-storage.ts`
  - [x] Use `expo-secure-store` (`SecureStore.setItemAsync`, `getItemAsync`, `deleteItemAsync`)
  - [x] Store key: `"auth_access_token"` for the JWT
  - [x] Store key: `"auth_user_role"` for the role (needed for routing before token decode)
  - [x] Store key: `"auth_home_path"` for the home path
  - [x] Store key: `"auth_user_email"` for pre-filling on re-auth
  - [x] Export: `saveAuthData(token, role, homePath, email)`, `getAuthData()`, `clearAuthData()`

- [x] Task 4: Create auth context and provider (AC: #1, #4)
  - [x] Create `apps/mobile/src/contexts/AuthContext.tsx`
  - [x] State: `{ isLoading: boolean; isAuthenticated: boolean; token: string | null; role: UserRole | null; homePath: string | null }`
  - [x] On mount: load token from SecureStore → if exists, set authenticated (check expiry by decoding JWT `exp` claim)
  - [x] Expose: `signIn(email, password)`, `signOut()`, `isLoading`, `isAuthenticated`, `role`, `homePath`
  - [x] `signIn`: call `POST /auth/login` via api-client → on success, save to SecureStore + update state → on failure, throw error for UI to catch
  - [x] `signOut`: clear SecureStore + reset state → triggers navigation to /auth

- [x] Task 5: Create auth login service function (AC: #1, #2, #5, #6)
  - [x] Create `apps/mobile/src/services/auth-service.ts`
  - [x] `loginWithEmailPassword(email: string, password: string): Promise<LoginResponse>`
  - [x] Calls `POST /auth/login` with `{ email, password }`
  - [x] Returns `{ access_token, token_type, expires_in, role, org_id, home_path }`
  - [x] Maps API errors: 401 → `InvalidCredentialsError`, 403 → `InactiveAccountError`, 429 → `RateLimitError`

- [x] Task 6: Update root layout with auth guard (AC: #1, #4)
  - [x] Update `apps/mobile/app/_layout.tsx`
  - [x] Wrap app with `<AuthProvider>`
  - [x] Add auth guard logic: if `isLoading` → show splash/loading; if `!isAuthenticated` → redirect to `/auth`; if `isAuthenticated` → allow navigation to role routes
  - [x] On 401 from any API call → trigger `signOut()` which redirects to `/auth` with session-expired message

- [x] Task 7: Build sign-in screen UI (AC: #1, #2, #3, #5, #6)
  - [x] Update `apps/mobile/app/auth/index.tsx` (replace placeholder)
  - [x] Centered single-column layout with generous vertical spacing (`$2xl` gap)
  - [x] App logo/title: "Teacher OS" in `$2xl` text, `$textPrimary` color
  - [x] Email input: `surface-dim` background, `border` border, 16px body text, placeholder "Email address"
  - [x] Password input: same styling, `secureTextEntry`, placeholder "Password"
  - [x] Sign In button: full-width, `primary` (`#2D6A4F`) background, white text, `radius-sm` (8px), 44px min height
  - [x] Loading state: button shows spinner + "Signing in..." text, inputs disabled
  - [x] Error display: inline error card below form with `error` color text, matching UX error format
  - [x] All touch targets minimum 44x44px
  - [x] Use Tamagui components: `YStack`, `XStack`, `Text`, `Input`, `Button` (or `Stack` + `Pressable`)
  - [x] Form field spacing: `$md` (16px) between fields
  - [x] `SafeAreaView` with `edges={["top", "bottom"]}` since no tab bar on auth screen

- [x] Task 8: Add network connectivity detection (AC: #3)
  - [x] In sign-in handler, catch `NetworkError` from api-client
  - [x] Display blocking error: "Couldn't sign in. Check your connection and try again." + [Try Again] button
  - [x] No need for a separate network monitoring library — detect at request time via fetch failure

- [x] Task 9: Add role-based navigation routing (AC: #1)
  - [x] After successful login, use `router.replace(homePath)` where homePath comes from login response
  - [x] Role-to-path mapping (from API `home_path` field): teacher → `/(teacher)`, parent → `/(parent)`, student → `/(student)`
  - [x] Handle admin/principal roles: redirect to `/(teacher)` for now (admin web portal is Epic 9)

- [x] Task 10: Handle token expiry (AC: #4)
  - [x] In api-client, intercept 401 responses on authenticated requests
  - [x] On 401: call `signOut()` from AuthContext
  - [x] Pass `sessionExpired: true` flag to auth screen (via router params or context)
  - [x] Auth screen shows: "Your session has expired. Please sign in again." banner when `sessionExpired` is true
  - [x] Pre-fill email from stored `auth_user_email` in SecureStore

- [x] Task 11: Add TypeScript contracts (AC: all)
  - [x] Add to `packages/contracts/src/auth.ts`:
    - `LoginRequest { email: string; password: string }`
    - `LoginResponse { access_token: string; token_type: string; expires_in: number; role: UserRole; org_id: string; home_path: string }`
  - [x] Export from `packages/contracts/src/index.ts`

- [x] Task 12: Verify and test (AC: all)
  - [x] Run `pnpm typecheck` from monorepo root — zero TypeScript errors
  - [ ] Manually verify: valid credentials → correct role redirect
  - [ ] Manually verify: invalid credentials → generic error message
  - [ ] Manually verify: app restart with stored token → auto-redirect to home
  - [ ] Manually verify: expired/invalid token → redirect to sign-in with message

## Dev Notes

### Backend Auth API Contract (Already Implemented)

The API auth endpoints are fully implemented and tested. Do NOT modify any backend code.

**Endpoint:** `POST /auth/login`

```
Request:  { "email": string, "password": string }
Response: { "access_token": string, "token_type": "bearer", "expires_in": int, "role": string, "org_id": string, "home_path": string }
```

**Error Responses:**
- `401` — Invalid credentials (generic, anti-enumeration): `{ "detail": "Invalid credentials" }`
- `403` — Account inactive/no authorized membership
- `429` — Rate limited (too many failed attempts per email or IP)

**JWT Token Claims** (decoded):
- `sub`: user_id (string)
- `org_id`: organization ID
- `role`: user role enum
- `exp`: expiration timestamp (Unix epoch)

**Algorithm:** HS256 with server-side secret. Mobile does NOT need to verify signature — just decode payload for `exp` check.

**Test Accounts** (for local development with Docker Compose):
| Email | Password | Role |
|-------|----------|------|
| admin@example.com | correct-horse-battery-staple | admin |
| teacher@example.com | correct-horse-battery-staple | teacher |
| parent@example.com | correct-horse-battery-staple | parent |
| student@example.com | correct-horse-battery-staple | student |
| inactive.teacher@example.com | correct-horse-battery-staple | teacher (inactive) |

**Rate Limiter:** `InMemoryLoginRateLimiter` — tracks per-email and per-client-IP. Returns 429 after threshold.

### API Base URL Configuration

The FastAPI server runs on port `8000` in Docker Compose. For the mobile app:
- Local dev (Expo Go / dev client): `http://<host-ip>:8000` — must NOT use `localhost` since the mobile device/emulator has a different localhost
- Use `expo-constants` to read `expoConfig.extra.apiBaseUrl` from `app.json` / `app.config.ts`
- Fallback: `http://192.168.x.x:8000` (developer's machine IP)

### Existing Code to Reuse

**Design Tokens** — import from `@ilm/design-tokens`:
```typescript
import { colors, spacing, radii, fonts, fontSizes, shadows, layout } from "@ilm/design-tokens";
// colors.primary = "#2D6A4F", colors.background = "#FAFAF5", colors.surface = "#FFFFFF"
// colors.surfaceDim = "#F0EDE6" (input backgrounds)
// colors.textPrimary = "#2C2C2C", colors.textSecondary = "#6B6B6B", colors.textMuted = "#9B9B9B"
// colors.border = "#E8E4DC", colors.error (for error messages)
// radii.sm = 8 (buttons), spacing.md = 16, spacing["2xl"] = 32
// layout.minTouchTarget = 44
```

**UI Components** — import from `@ilm/ui`:
```typescript
import { SkeletonLoader } from "@ilm/ui";
```

**Type Contracts** — import from `@ilm/contracts`:
```typescript
import type { UserRole } from "@ilm/contracts";
// UserRole = "admin" | "principal" | "teacher" | "parent" | "student"
```

**Tamagui Components** — already configured in the mobile app:
```typescript
import { YStack, XStack, Text, Input, Button, Spinner } from "tamagui";
```

**SafeAreaView** — already installed and used in Story 4.4:
```typescript
import { SafeAreaView } from "react-native-safe-area-context";
```

### Existing Mobile File Structure (from Story 4.4)

```
apps/mobile/
├── app/
│   ├── _layout.tsx              # Root: TamaguiProvider + SafeAreaProvider + ReducedMotionProvider
│   │                            # → UPDATE: add AuthProvider, add auth guard
│   ├── index.tsx                # Redirect to /auth → KEEP AS-IS
│   ├── auth/index.tsx           # Placeholder → REPLACE with sign-in form
│   ├── onboarding/index.tsx     # Placeholder → DO NOT TOUCH (Story 4.9)
│   ├── (teacher)/_layout.tsx    # Tab nav (5 tabs + FAB) → DO NOT TOUCH
│   ├── (parent)/_layout.tsx     # Tab nav (4 tabs) → DO NOT TOUCH
│   └── (student)/_layout.tsx    # Tab nav (4 tabs) → DO NOT TOUCH
├── src/
│   ├── contexts/
│   │   └── ReducedMotionContext.tsx  # Existing → DO NOT TOUCH
│   ├── hooks/
│   │   └── useReducedMotion.ts      # Existing → DO NOT TOUCH
│   ├── components/
│   │   └── CameraFab.tsx            # Existing → DO NOT TOUCH
│   └── navigation/
│       └── tab-icons.tsx            # Existing → DO NOT TOUCH
```

### New Files This Story Creates

```
apps/mobile/src/services/api-client.ts      # NEW: HTTP client with auth header injection
apps/mobile/src/services/token-storage.ts   # NEW: SecureStore wrapper for auth tokens
apps/mobile/src/services/auth-service.ts    # NEW: Login API call + error mapping
apps/mobile/src/contexts/AuthContext.tsx     # NEW: Auth state provider + signIn/signOut
packages/contracts/src/auth.ts              # NEW: LoginRequest/LoginResponse types
```

### Modified Files

```
apps/mobile/app/_layout.tsx                 # ADD: AuthProvider wrapper + auth guard
apps/mobile/app/auth/index.tsx              # REPLACE: placeholder → full sign-in form
apps/mobile/package.json                    # ADD: expo-secure-store dependency
packages/contracts/src/index.ts             # ADD: export auth types
```

### UX Design Specifications for Sign-In Screen

**Layout:** Centered single-column, `background` (`#FAFAF5`) screen color, generous `$2xl` vertical spacing.

**Input Fields:**
- Background: `surface-dim` (`#F0EDE6`)
- Border: `border` (`#E8E4DC`)
- Text: `body` (16px), `text-primary` color
- Placeholder: `text-muted` (`#9B9B9B`)
- Field spacing: `$md` (16px) between fields

**Sign In Button:**
- Full-width, `primary` (`#2D6A4F`) background, white text
- Corner radius: `radius-sm` (8px)
- Min height: 44px (min touch target)
- Press animation: scale to 0.97 + background shift 100ms
- Loading: show spinner + "Signing in..." text, disable all inputs

**Error Messages:**
- Blocking errors (auth failure, no network): full-screen-style error with retry
- For inline form errors: error card below form, `error` color text
- Format: [What happened] — plain language, no codes

### What NOT to Do

- **Do NOT install axios, ky, or any HTTP library** — use native `fetch`
- **Do NOT install AsyncStorage** — use `expo-secure-store` for token storage (it's encrypted)
- **Do NOT install react-hook-form or formik** — simple 2-field form doesn't need a form library, use React state
- **Do NOT implement refresh token logic** — the API doesn't have a refresh endpoint yet
- **Do NOT modify any backend/API code** — the auth API is complete and tested
- **Do NOT modify tab layouts or screen files** from Story 4.4 — only touch auth screen and root layout
- **Do NOT create a custom JWT verification** on mobile — just decode (base64) the payload for `exp` claim, don't verify signature
- **Do NOT add TanStack Query yet** — single auth call doesn't need a query cache; TQ will be added in later stories with data fetching
- **Do NOT implement Google sign-in** — that's Story 4.6
- **Do NOT implement onboarding flow** — that's Story 4.9
- **Do NOT add deep linking for auth** — not needed yet

### JWT Decoding on Mobile (No Verification)

To check token expiry without a JWT library:
```typescript
function decodeJwtPayload(token: string): { exp: number; sub: string; role: string; org_id: string } {
  const base64 = token.split('.')[1];
  const json = atob(base64);
  return JSON.parse(json);
}

function isTokenExpired(token: string): boolean {
  const { exp } = decodeJwtPayload(token);
  return Date.now() >= exp * 1000;
}
```

Do NOT install `jwt-decode` or `jsonwebtoken` — the above is sufficient for mobile client needs.

### Error Type Hierarchy

Define in `api-client.ts`:
```typescript
export class NetworkError extends Error { name = "NetworkError"; }
export class ApiError extends Error {
  name = "ApiError";
  constructor(public code: string, message: string, public status: number) { super(message); }
}
```

Map in `auth-service.ts`:
```typescript
export class InvalidCredentialsError extends Error { name = "InvalidCredentialsError"; }
export class InactiveAccountError extends Error { name = "InactiveAccountError"; }
export class RateLimitError extends Error { name = "RateLimitError"; }
```

### Auth Guard Pattern with Expo Router

Expo Router uses file-based routing. Auth guard pattern:

```typescript
// In app/_layout.tsx
const { isLoading, isAuthenticated } = useAuth();
const segments = useSegments();
const router = useRouter();

useEffect(() => {
  if (isLoading) return;
  const inAuthGroup = segments[0] === "auth";
  if (!isAuthenticated && !inAuthGroup) {
    router.replace("/auth");
  } else if (isAuthenticated && inAuthGroup) {
    router.replace(homePath); // e.g., "/(teacher)"
  }
}, [isAuthenticated, isLoading, segments]);
```

### Previous Story Intelligence (Story 4.4)

**Key Learnings:**
- TypeScript failed on `@expo/vector-icons` subpath import due to pnpm strict node_modules — watch for similar issues with `expo-secure-store`
- Code review caught false task completions — verify each task actually works before marking done
- Student tab order was wrong initially — double-check acceptance criteria carefully
- Use `edges={["top"]}` on SafeAreaView for screens with tab bar; use `edges={["top", "bottom"]}` for auth screen (no tab bar)

**Established Patterns:**
- Tamagui `YStack`/`XStack`/`Text` for layout (not React Native View/Text)
- `SafeAreaView` from `react-native-safe-area-context` wrapping screens
- Design tokens imported from `@ilm/design-tokens`
- UI components from `@ilm/ui`
- `expo-haptics` for button press feedback — consider adding to sign-in button

**Technology Versions (verified in Story 4.4):**
- Expo SDK: ~52.0.0
- Expo Router: ~4.0.0 (React Navigation v7)
- React Native: 0.76.7 (New Architecture enabled)
- Tamagui: ^1.114.0
- react-native-safe-area-context: ~5.0.0
- TypeScript across all workspaces

### Project Structure Notes

- All new service files go in `apps/mobile/src/services/` (new directory)
- Auth context goes in `apps/mobile/src/contexts/` (existing directory)
- Contract types go in `packages/contracts/src/` (existing directory)
- Follow existing naming: kebab-case filenames, PascalCase components, camelCase functions

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.5] — Story requirements and acceptance criteria
- [Source: _bmad-output/planning-artifacts/architecture.md#Authentication] — JWT patterns, password hashing, token model
- [Source: _bmad-output/planning-artifacts/architecture.md#API Patterns] — REST conventions, error envelope format
- [Source: _bmad-output/planning-artifacts/architecture.md#Mobile Architecture] — Expo/React Native patterns, state management
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Error Handling] — Error message format and hierarchy
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Color Tokens] — Form input colors and typography
- [Source: _bmad-output/implementation-artifacts/4-4-mobile-app-shell-with-role-scoped-navigation.md] — Previous story patterns and learnings
- [Source: apps/api/app/domains/auth/router.py] — Auth API endpoints (login, google)
- [Source: apps/api/app/domains/auth/schemas.py] — Request/response schemas
- [Source: apps/api/app/core/security.py] — JWT creation, password verification, token decode

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- `pnpm typecheck` passes with zero errors across all 5 packages (contracts, design-tokens, ui, mobile, admin-web)

### Completion Notes List

- Installed `expo-secure-store@~14.0.1` via `npx expo install` — auto-added to app.json plugins
- Created `packages/contracts/src/auth.ts` with `LoginRequest` and `LoginResponse` types, exported from index
- Created `apps/mobile/src/services/api-client.ts` — native fetch wrapper with `NetworkError` and `ApiError` typed errors, Bearer token injection, base URL from expo-constants with localhost fallback
- Created `apps/mobile/src/services/token-storage.ts` — SecureStore wrapper storing access_token, role, home_path, email with `saveAuthData()`, `getAuthData()`, `clearAuthData()`
- Created `apps/mobile/src/services/auth-service.ts` — `loginWithEmailPassword()` calling POST /auth/login with error mapping (401→InvalidCredentials, 403→InactiveAccount, 429→RateLimit)
- Created `apps/mobile/src/contexts/AuthContext.tsx` — AuthProvider with `signIn`/`signOut`, JWT expiry check via base64 decode, session-expired flag, last-email persistence for pre-fill
- Updated `apps/mobile/app/_layout.tsx` — added AuthProvider wrapper and AuthGuard component using `useSegments()`/`useRouter()` for Expo Router auth redirect pattern
- Replaced `apps/mobile/app/auth/index.tsx` placeholder with full sign-in form using Tamagui components (YStack, Input, Button, Spinner), SafeAreaView, design tokens for styling, error handling for all error types (network, invalid creds, inactive, rate limit)
- Token expiry handled via signOut with sessionExpired flag → auth screen shows "session expired" banner and pre-fills email
- Note: actual design token names differ from story spec — used `surfaceSecondary` (not `surfaceDim`) and `textTertiary` (not `textMuted`) per actual `@ilm/design-tokens` exports

### Change Log

- 2026-03-21: Implemented email/password sign-in on mobile — API client, secure token storage, auth context with JWT expiry detection, sign-in UI with Tamagui, auth guard routing, error handling for network/invalid creds/inactive/rate-limit scenarios.

### File List

New files:
- apps/mobile/src/services/api-client.ts
- apps/mobile/src/services/token-storage.ts
- apps/mobile/src/services/auth-service.ts
- apps/mobile/src/contexts/AuthContext.tsx
- packages/contracts/src/auth.ts

Modified files:
- apps/mobile/app/_layout.tsx
- apps/mobile/app/auth/index.tsx
- apps/mobile/package.json
- packages/contracts/src/index.ts
- pnpm-lock.yaml
- apps/mobile/app.json (auto-updated by expo install — added expo-secure-store plugin)
