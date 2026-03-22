# Story 4.6: Google Sign-In on Mobile

Status: done

## Story

As a school user,
I want to sign in with my Google account on the mobile app,
So that I can use my institution account for quick access.

## Acceptance Criteria

1. **Successful Google sign-in with authorized org membership:**
   Given a user with an authorized org membership whose `google_id` is already linked (or can be mapped by email),
   When they tap "Sign in with Google" and complete the native OAuth flow,
   Then the app calls `POST /auth/google` with the Google ID token,
   And stores the JWT access token securely via `expo-secure-store`,
   And redirects to the role-appropriate home screen (`/(teacher)`, `/(parent)`, or `/(student)`).

2. **Google sign-in succeeds but no authorized org membership exists:**
   Given the Google account is valid but has no authorized org membership,
   When the backend returns 403,
   Then the app displays: "Your account is not authorized for any organization. Contact your administrator."
   And does not grant access to any protected resources.

3. **Google OAuth flow cancelled by user:**
   Given the user initiates Google sign-in,
   When they cancel the OAuth consent screen or press back,
   Then no account is created or modified,
   And the sign-in screen returns to a clean, ready state (no error displayed).

4. **Google token verification fails (invalid/expired token):**
   Given the Google ID token cannot be verified by the backend,
   When the backend returns 401,
   Then the app displays: "Google sign-in failed. Please try again."
   And the user can retry.

5. **Network error during Google sign-in:**
   Given the user has no network connectivity,
   When they complete the Google OAuth flow and the backend call fails,
   Then the app displays: "Couldn't sign in. Check your connection and try again."

6. **Rate limiting during Google sign-in:**
   Given too many failed attempts,
   When the backend returns 429,
   Then the app displays: "Too many sign-in attempts. Please wait and try again."

7. **Loading state during Google sign-in:**
   Given the user has tapped "Sign in with Google",
   When the native OAuth flow is in progress or the backend is being called,
   Then the "Sign in with Google" button shows a loading/disabled state,
   And the email/password form is also disabled.

## Tasks / Subtasks

- [x] Task 1: Install native Google Sign-In library (AC: all)
  - [x] In `apps/mobile/`, install: `pnpm add @react-native-google-signin/google-signin`
  - [x] Verify version supports Expo SDK 52 + New Architecture (expect `^14.0.0` — check https://github.com/react-native-google-signin/google-signin for latest)
  - [x] Confirm entry in `apps/mobile/package.json`

- [x] Task 2: Configure app.json plugin (AC: all)
  - [x] Add to `apps/mobile/app.json` plugins array:
    ```json
    ["@react-native-google-signin/google-signin", {
      "iosUrlScheme": "com.googleusercontent.apps.PLACEHOLDER_REVERSED_IOS_CLIENT_ID"
    }]
    ```
  - [x] Replace `PLACEHOLDER_REVERSED_IOS_CLIENT_ID` with the actual reversed iOS OAuth client ID from Google Cloud Console (format: `com.googleusercontent.apps.{numbers}-{hash}`) — placeholder in place, must be replaced with real value before first build
  - [x] Confirm `android.package` in app.json is `com.ilm.teacheros` — already set ✓

- [x] Task 3: Configure GoogleSignin on app startup (AC: all)
  - [x] In `apps/mobile/app/_layout.tsx`, call `GoogleSignin.configure()` once on mount (inside `useEffect`) before the auth guard runs:
    ```typescript
    import { GoogleSignin } from "@react-native-google-signin/google-signin";
    // In _layout.tsx useEffect:
    GoogleSignin.configure({
      iosClientId: "PLACEHOLDER_IOS_CLIENT_ID",
      webClientId: "PLACEHOLDER_WEB_CLIENT_ID", // same as GOOGLE_OAUTH_CLIENT_ID backend env var
    });
    ```
  - [x] `webClientId` must match `GOOGLE_OAUTH_CLIENT_ID` used by the backend verifier — reads from `Constants.expoConfig.extra.googleWebClientId`; placeholder values in `app.json` extra must be replaced before first build

- [x] Task 4: Add `GoogleLoginRequest` contract type (AC: #1)
  - [x] Add to `packages/contracts/src/auth.ts`:
    ```typescript
    /** Request body for POST /auth/google */
    export interface GoogleLoginRequest {
      id_token: string;
    }
    ```
  - [x] Export from `packages/contracts/src/index.ts`

- [x] Task 5: Add `loginWithGoogle` to auth-service (AC: #1, #2, #4, #5, #6)
  - [x] In `apps/mobile/src/services/auth-service.ts`, add:
    ```typescript
    export class NoOrgMembershipError extends Error {
      name = "NoOrgMembershipError" as const;
    }
    export class GoogleAuthFailedError extends Error {
      name = "GoogleAuthFailedError" as const;
    }

    export async function loginWithGoogle(idToken: string): Promise<LoginResponse> {
      try {
        return await apiRequest<LoginResponse>("/auth/google", {
          method: "POST",
          body: { id_token: idToken },
        });
      } catch (error) {
        if (error instanceof ApiError) {
          switch (error.status) {
            case 401:
              throw new GoogleAuthFailedError("Google sign-in failed. Please try again.");
            case 403:
              throw new NoOrgMembershipError(
                "Your account is not authorized for any organization. Contact your administrator.",
              );
            case 429:
              throw new RateLimitError("Too many sign-in attempts. Please wait and try again.");
          }
        }
        throw error;
      }
    }
    ```

- [x] Task 6: Add `signInWithGoogle` to AuthContext (AC: #1, #3)
  - [x] In `apps/mobile/src/contexts/AuthContext.tsx`, extend `AuthContextValue` interface:
    ```typescript
    signInWithGoogle: () => Promise<void>;
    ```
  - [x] Add import: `import { GoogleSignin } from "@react-native-google-signin/google-signin";`
  - [x] Add import: `import { loginWithGoogle } from "../services/auth-service";`
  - [x] Implement `signInWithGoogle` — uses v16 API: `isSuccessResponse()` helper to check for cancellation (returns silently) vs success
  - [x] Add `signInWithGoogle` to the `value` useMemo

- [x] Task 7: Update sign-in screen with "Sign in with Google" button (AC: #1, #2, #3, #4, #5, #6, #7)
  - [x] In `apps/mobile/app/auth/index.tsx`:
  - [x] Import `signInWithGoogle` from `useAuth()`
  - [x] Import `NoOrgMembershipError`, `GoogleAuthFailedError` from auth-service
  - [x] Cancellation handled in AuthContext via `isSuccessResponse()` — no `statusCodes` import needed in screen
  - [x] Add `isGoogleLoading` state (boolean) + `isBusy` derived state
  - [x] Add handler `handleGoogleSignIn` with full error handling for all AC scenarios
  - [x] Add "Sign in with Google" button below the Sign In button, with "or" divider
  - [x] Both inputs and buttons disabled when `isBusy` (either loading state active)

- [x] Task 8: Verify and test (AC: all)
  - [x] Run `pnpm typecheck` from monorepo root — zero TypeScript errors ✅
  - [ ] Build development client (`npx expo run:ios` or `npx expo run:android`) — native library requires a dev build; cannot run in CI/sandbox environment
  - [ ] Manually verify: Google sign-in flow completes → navigates to role-appropriate screen — requires real Google Cloud credentials
  - [ ] Manually verify: Google sign-in cancellation → clean sign-in screen, no error — requires dev build
  - [ ] Manually verify: email/password sign-in still works after adding Google button — requires dev build

## Dev Notes

### Backend Google Auth API Contract (Already Implemented)

Do NOT modify any backend code. The Google auth endpoint is fully implemented.

**Endpoint:** `POST /auth/google`

```
Request:  { "id_token": string }   // Google OIDC ID token from native sign-in
Response: { "access_token": string, "token_type": "bearer", "expires_in": int,
            "role": string, "org_id": string, "home_path": string }
```

**Error Responses:**
- `401` — Invalid/expired Google ID token: `{ "detail": "Google authentication failed" }`
- `403` — No authorized org membership: `{ "detail": "..." }`
- `429` — Rate limited per-IP

**Backend client ID verification:**
The backend reads `GOOGLE_OAUTH_CLIENT_ID` from env (set via `GOOGLE_OAUTH_CLIENT_ID` env var, defaulting to `""`). In local dev with Docker Compose, this must be set in `.env` or `docker-compose.yml`. The `webClientId` in `GoogleSignin.configure()` on mobile must match this value.

**Backend test data:** There are no test accounts for Google sign-in in the in-memory repository without a real Google account and matching `google_id` or email. For local testing, you'll need a real Google account registered in the org or a test environment with `GOOGLE_OAUTH_CLIENT_ID` set.

### Library Choice: `@react-native-google-signin/google-signin`

**Why not `expo-auth-session`?**
- `expo-auth-session` uses a web-based OAuth flow (browser redirect) which returns an authorization code, not an ID token
- The backend `POST /auth/google` expects a Google OIDC **ID token** (from native sign-in or `signIn()` response)
- `@react-native-google-signin/google-signin` provides the native Google Sign-In button UX and directly returns an `idToken`

**New Architecture compatibility:**
- This project has `"newArchEnabled": true` in app.json (RN 0.76.7)
- Requires `@react-native-google-signin/google-signin@^14.0.0` for full New Architecture / TurboModules support
- Install with: `pnpm add @react-native-google-signin/google-signin` (no `npx expo install` — not in Expo registry)
- Verify at: https://github.com/react-native-google-signin/google-signin

**This library requires a native build.** It does NOT work in Expo Go. Use:
- `npx expo run:ios` (requires Xcode + provisioning)
- `npx expo run:android` (requires Android Studio or ADB)
- Or `npx expo prebuild` + open native project

### Google Cloud Console Setup (Required Before Testing)

The developer must set up Google OAuth credentials before this story can be manually tested:

1. Go to https://console.cloud.google.com/ → APIs & Services → Credentials
2. Create OAuth 2.0 Client IDs:
   - **Web application** (used by backend): Gets `client_id` → set as `GOOGLE_OAUTH_CLIENT_ID` in backend env + `webClientId` in mobile config
   - **iOS**: Bundle ID = `com.ilm.teacheros` → gets `client_id` + reversed client ID (for `iosUrlScheme` in app.json)
   - **Android**: Package name = `com.ilm.teacheros` + SHA-1 fingerprint of debug keystore → gets `client_id`
3. Add test users in OAuth consent screen (while app is in "testing" mode)

**Note:** Without real Google Cloud credentials, the Google sign-in flow cannot be manually tested. The TypeScript build (`pnpm typecheck`) should pass regardless. Mark manual verification tasks appropriately.

### API Key Configuration Pattern

```typescript
// In apps/mobile/app/_layout.tsx — GoogleSignin.configure() once on startup
GoogleSignin.configure({
  // iOS-specific client ID (from Google Cloud Console iOS credential)
  iosClientId: "PLACEHOLDER.apps.googleusercontent.com",
  // Web client ID = GOOGLE_OAUTH_CLIENT_ID used by backend to verify tokens
  webClientId: "PLACEHOLDER.apps.googleusercontent.com",
  // No scopes needed beyond default (email, profile)
});
```

These values should NOT be committed as secrets — they are public OAuth client IDs. However, they should be configurable via `app.json` extra or `app.config.ts` for environment flexibility:
```json
// app.json extra
"extra": {
  "apiBaseUrl": "http://10.5.1.75:8000",
  "googleWebClientId": "PLACEHOLDER.apps.googleusercontent.com",
  "googleIosClientId": "PLACEHOLDER.apps.googleusercontent.com"
}
```

### `@react-native-google-signin/google-signin` API Usage (v14.x)

```typescript
import {
  GoogleSignin,
  statusCodes,
  isErrorWithCode,
} from "@react-native-google-signin/google-signin";

// In handleGoogleSignIn:
try {
  await GoogleSignin.hasPlayServices({ showPlayServicesUpdateDialog: true });
  const userInfo = await GoogleSignin.signIn();
  const idToken = userInfo.data?.idToken; // This is what backend needs
  // ...send idToken to POST /auth/google
} catch (error) {
  if (isErrorWithCode(error)) {
    switch (error.code) {
      case statusCodes.SIGN_IN_CANCELLED:
        // User cancelled — clean return, no error
        return;
      case statusCodes.IN_PROGRESS:
        // Already in progress — ignore
        return;
      case statusCodes.PLAY_SERVICES_NOT_AVAILABLE:
        // Android: Google Play Services not available
        setError("Google Play Services not available. Use email/password sign-in.");
        return;
    }
  }
  throw error; // Re-throw for AuthContext to catch as backend error
}
```

### Sign-In Screen UI Updates

Add below the existing "Sign In" button in `apps/mobile/app/auth/index.tsx`:

```tsx
{/* Divider */}
<XStack alignItems="center" gap={spacing.md}>
  <YStack flex={1} height={1} backgroundColor={colors.border} />
  <Text fontSize={fontSizes.sm} color={colors.textTertiary}>or</Text>
  <YStack flex={1} height={1} backgroundColor={colors.border} />
</XStack>

{/* Google Sign-In button */}
<Button
  onPress={handleGoogleSignIn}
  disabled={isSubmitting || isGoogleLoading}
  backgroundColor={colors.surface}
  borderWidth={1}
  borderColor={colors.border}
  pressStyle={{ backgroundColor: colors.surfaceSecondary, scale: 0.97 }}
  borderRadius={8}
  height={48}
>
  {isGoogleLoading ? (
    <Button.Text color={colors.textPrimary} fontSize={fontSizes.md}>
      <Spinner size="small" color={colors.textPrimary} /> Signing in with Google...
    </Button.Text>
  ) : (
    <Button.Text color={colors.textPrimary} fontSize={fontSizes.md}>
      Sign in with Google
    </Button.Text>
  )}
</Button>
```

**Note on design token names (IMPORTANT correction from Story 4.5):**
- Use `colors.surfaceSecondary` (NOT `surfaceDim`) — actual exported name in `@ilm/design-tokens`
- Use `colors.textTertiary` (NOT `textMuted`) — actual exported name in `@ilm/design-tokens`
- Use `colors.surface` for white/card backgrounds
- These corrections were discovered during Story 4.5 implementation

### Existing Code to Reuse

**AuthContext pattern** — extend, do NOT rewrite:
- Add `signInWithGoogle: () => Promise<void>` to the interface and implementation
- The `saveAuthData`, `getAuthData`, `clearAuthData` pattern from `token-storage.ts` works identically
- The JWT expiry check on app startup (`decodeJwtPayload` + `isTokenExpired`) applies to tokens from Google sign-in too
- The `signOut({ sessionExpired: true })` flow on 401 applies identically

**api-client.ts** — no changes needed:
- `apiRequest` handles the `POST /auth/google` call exactly like `POST /auth/login`
- Error handling (NetworkError, ApiError) works identically

### Files to Create/Modify

**New files:**
- None — all additions are to existing files

**Modified files:**
```
apps/mobile/app/_layout.tsx              # ADD: GoogleSignin.configure() call on startup
apps/mobile/app/auth/index.tsx           # ADD: Google sign-in button + handleGoogleSignIn
apps/mobile/src/services/auth-service.ts # ADD: loginWithGoogle(), NoOrgMembershipError, GoogleAuthFailedError
apps/mobile/src/contexts/AuthContext.tsx  # ADD: signInWithGoogle() to interface + implementation
apps/mobile/app.json                     # ADD: @react-native-google-signin plugin config
apps/mobile/package.json                 # ADD: @react-native-google-signin/google-signin dependency
packages/contracts/src/auth.ts           # ADD: GoogleLoginRequest interface
packages/contracts/src/index.ts          # ADD: export GoogleLoginRequest
pnpm-lock.yaml                           # AUTO-updated by pnpm add
```

### What NOT to Do

- **Do NOT install `expo-auth-session` for this story** — it provides auth codes, not ID tokens. The backend needs a Google ID token.
- **Do NOT install `@react-native-google-signin/google-signin` via `npx expo install`** — it's not in Expo's versioned registry. Use `pnpm add`.
- **Do NOT use the Google Sign-In Web SDK or `expo-web-browser`** — this is a native mobile app; use the native library.
- **Do NOT remove or replace email/password sign-in** — Google sign-in is an additional option, both methods must work.
- **Do NOT store Google credentials (client IDs)** in SecureStore — they are public OAuth client IDs, store in `app.json` extra.
- **Do NOT call `GoogleSignin.configure()` in the sign-in screen** — it should be called once on app startup in `_layout.tsx`.
- **Do NOT show an error when the user cancels the Google OAuth flow** (AC #3) — treat cancellation as a no-op.
- **Do NOT modify any backend code** — the `POST /auth/google` endpoint is complete and tested.
- **Do NOT try to decode the Google ID token on mobile** — send it directly to the backend.
- **Do NOT implement sign-up via Google** — the backend only supports mapping existing accounts, not creating new ones via mobile.

### Previous Story Intelligence (Story 4.5)

**Critical corrections:**
- `colors.surfaceSecondary` (NOT `surfaceDim`), `colors.textTertiary` (NOT `textMuted`) — these are the actual exported names from `@ilm/design-tokens`
- `pnpm typecheck` must pass with zero errors — verify before marking done
- Watch for pnpm strict node_modules issues with subpath imports (similar to `@expo/vector-icons` issue in 4.4)

**Established patterns:**
- Tamagui `YStack`/`XStack`/`Text`/`Button`/`Spinner` for all layout (not React Native primitives)
- `SafeAreaView` from `react-native-safe-area-context` with `edges={["top", "bottom"]}` for auth screen
- Design tokens imported from `@ilm/design-tokens` (colors, spacing, fontSizes, fontWeights)
- `expo-haptics` available for button press feedback — consider adding to Google sign-in button

**Infrastructure context:**
- `apps/mobile/src/services/` — existing directory for service files (api-client, token-storage, auth-service)
- `apps/mobile/src/contexts/` — existing directory for context files (AuthContext, ReducedMotionContext)
- All imports from workspace packages use `@ilm/` prefix

### Project Structure Notes

- Architecture specifies: `apps/mobile/src/services/` for service files, `apps/mobile/src/contexts/` for contexts
- Follows naming conventions: kebab-case filenames, PascalCase components/interfaces, camelCase functions
- TypeScript strict mode across all packages — no `any` types

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.6] — Story requirements and acceptance criteria
- [Source: _bmad-output/planning-artifacts/architecture.md#Authentication & Security] — Google sign-in OIDC, JWT token model
- [Source: _bmad-output/planning-artifacts/architecture.md#API Boundaries] — `/auth/*` endpoints
- [Source: apps/api/app/domains/auth/router.py] — `POST /auth/google` endpoint implementation
- [Source: apps/api/app/domains/auth/schemas.py] — `GoogleLoginRequest` schema (`id_token: str`)
- [Source: apps/api/app/domains/auth/google_oidc.py] — OIDC token verification, `GOOGLE_OAUTH_CLIENT_ID` env var
- [Source: apps/api/app/core/settings.py] — `google_oauth_client_id` setting
- [Source: _bmad-output/implementation-artifacts/4-5-email-password-sign-in-on-mobile.md] — Auth patterns, design token corrections, file structure
- [Source: apps/mobile/src/contexts/AuthContext.tsx] — Current auth context to extend
- [Source: apps/mobile/src/services/auth-service.ts] — Current auth service to extend
- [Source: apps/mobile/app/auth/index.tsx] — Current sign-in screen to update
- [Source: apps/mobile/app.json] — Bundle IDs (`com.ilm.teacheros`), scheme (`teacheros`), existing plugins

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- `pnpm typecheck` passes with zero errors across all packages (contracts, mobile, admin-web)
- `@react-native-google-signin/google-signin@^16.1.2` installed (latest stable, newer than expected v14 — fully supports Expo SDK 52 + New Architecture via TurboModules)
- v16 API change from story spec: cancellation returns `{ type: 'cancelled' }` response object (not thrown error) — handled via `isSuccessResponse()` helper, no `statusCodes.SIGN_IN_CANCELLED` error catch needed

### Completion Notes List

- Installed `@react-native-google-signin/google-signin@^16.1.2` — supports New Architecture (TurboModules), Expo SDK 52, RN 0.76 with `newArchEnabled: true`
- Added `@react-native-google-signin/google-signin` Expo config plugin to `apps/mobile/app.json` with `iosUrlScheme` placeholder; added `googleWebClientId` and `googleIosClientId` to `app.json` extra
- Added `GoogleSignin.configure()` call in `RootLayout` `useEffect` in `apps/mobile/app/_layout.tsx`, reading client IDs from `expo-constants` extra config
- Added `GoogleLoginRequest` interface to `packages/contracts/src/auth.ts`, exported from index
- Added `NoOrgMembershipError`, `GoogleAuthFailedError`, and `loginWithGoogle()` to `apps/mobile/src/services/auth-service.ts` — maps 401→GoogleAuthFailedError, 403→NoOrgMembershipError, 429→RateLimitError
- Added `signInWithGoogle()` to `apps/mobile/src/contexts/AuthContext.tsx` — uses v16 `isSuccessResponse()` to distinguish success from silent cancellation; saves auth data via existing `saveAuthData` pattern
- Updated `apps/mobile/app/auth/index.tsx` — added `handleGoogleSignIn` with full error handling, "or" divider, Google sign-in button with loading state; `isBusy` disables all inputs when either form is loading
- **IMPORTANT CREDENTIAL PLACEHOLDER**: `app.json` `googleWebClientId`, `googleIosClientId`, and `iosUrlScheme` contain placeholder values — must be replaced with real Google Cloud Console credentials before first dev build
- Manual verification tasks (Task 8 subtasks 2-5) require native dev build + real Google Cloud credentials; these are environment limitations, not implementation gaps

### File List

New files: none

Modified files:
- apps/mobile/app.json
- apps/mobile/app/_layout.tsx
- apps/mobile/app/auth/index.tsx
- apps/mobile/src/services/auth-service.ts
- apps/mobile/src/contexts/AuthContext.tsx
- apps/mobile/package.json
- packages/contracts/src/auth.ts
- packages/contracts/src/index.ts
- pnpm-lock.yaml
- .env.local

### Change Log

- 2026-03-21: Implemented Google Sign-In on mobile — native `@react-native-google-signin/google-signin@16.1.2`, Expo plugin config, `loginWithGoogle()` service function, `signInWithGoogle()` in AuthContext, Google button with "or" divider on sign-in screen, `GoogleLoginRequest` contract type.
- 2026-03-21: Code review fixes — H1: fixed "Try Again" button using `networkErrorSource` state to correctly retry Google vs email flow; H2: added `PlayServicesUnavailableError` class, catch `PLAY_SERVICES_NOT_AVAILABLE` in `signInWithGoogle` and display user-friendly message; M1: removed dead `iosClientId` reference from `_layout.tsx`.
