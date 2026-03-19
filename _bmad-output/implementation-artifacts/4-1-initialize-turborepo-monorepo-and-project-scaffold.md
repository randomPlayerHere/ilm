# Story 4.1: Initialize Turborepo Monorepo and Project Scaffold

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want the repository restructured as a Turborepo monorepo with mobile, admin-web, and API workspaces plus shared packages,
So that all teams can develop, build, and share code across surfaces from a single repo.

## Acceptance Criteria

1. **Monorepo workspaces exist with real tooling:**
   - `apps/mobile` contains a working Expo/React Native project with Tamagui design system installed and base theme tokens configured
   - `apps/admin-web` contains a working Vite + React + Tamagui project
   - `apps/api` (existing FastAPI backend) remains functional and unchanged
   - Shared packages exist: `packages/contracts`, `packages/design-tokens`, `packages/ui`

2. **Turborepo task orchestration works end-to-end:**
   - Running `pnpm dev` starts all three app workspaces concurrently via Turborepo
   - Changes to shared packages propagate to consuming apps
   - `pnpm build`, `pnpm lint`, `pnpm typecheck` run across all TS workspaces

3. **Mobile workspace is properly initialized:**
   - Expo project created with Expo Router (file-based routing)
   - Tamagui installed with base theme tokens from UX spec (colors, typography, spacing)
   - TypeScript configured with shared tsconfig base
   - Role-scoped route group stubs exist: `(teacher)/`, `(parent)/`, `(student)/`, `auth/`, `onboarding/`

4. **Admin-web workspace is properly initialized:**
   - Vite + React + TypeScript project with Tamagui web target
   - Shared design tokens consumed from `packages/design-tokens`
   - Basic routing shell with placeholder pages

5. **Shared packages contain real content:**
   - `packages/design-tokens`: Tamagui config with UX-spec color palette, typography (Inter + JetBrains Mono), spacing scale, radii, shadows
   - `packages/contracts`: TypeScript package structure ready for OpenAPI types (can start empty but buildable)
   - `packages/ui`: Tamagui component library structure with at least a `SkeletonLoader` placeholder component
   - `packages/eslint-config`: Shared ESLint configuration
   - `packages/tsconfig`: Shared TypeScript base configs

6. **TypeScript configured across all workspaces:**
   - Shared `tsconfig` base in `packages/tsconfig`
   - Each TS workspace extends the shared base
   - Path aliases work for package imports (e.g., `@ilm/design-tokens`, `@ilm/ui`, `@ilm/contracts`)

## Tasks / Subtasks

- [x] Task 1: Initialize `packages/tsconfig` with shared TS base configs (AC: #6)
  - [x] Create `base.json`, `react-native.json`, `react-web.json` configs
  - [x] Configure strict mode, path resolution, module settings
- [x] Task 2: Initialize `packages/eslint-config` with shared lint rules (AC: #5)
  - [x] TypeScript + React rules
  - [x] Import ordering rules
- [x] Task 3: Initialize `packages/design-tokens` with Tamagui config (AC: #5)
  - [x] Define color tokens from UX spec: primary (#2D6A4F sage green), background (#FAFAF5 warm off-white), surface (#FFFFFF), gold accent (#DDA15E), amber focus, terracotta error
  - [x] Typography: Inter family, JetBrains Mono for numerics
  - [x] Spacing scale, radii, shadows per UX spec
  - [x] Export `tamagui.config.ts` consumable by mobile and web
- [x] Task 4: Initialize `packages/ui` with shared Tamagui components (AC: #5)
  - [x] Create component library structure
  - [x] Implement `SkeletonLoader` placeholder component
  - [x] Export barrel file (`index.ts`)
- [x] Task 5: Initialize `packages/contracts` as buildable TS package (AC: #5)
  - [x] Set up package structure with `src/` directory
  - [x] Configure build tooling (tsup or tsc)
  - [x] Export empty barrel file ready for OpenAPI types
- [x] Task 6: Initialize `apps/mobile` with Expo + Tamagui (AC: #1, #3)
  - [x] Run `npx create-expo-app` or set up Expo project manually
  - [x] Install and configure Expo Router for file-based routing
  - [x] Install and configure Tamagui with `@ilm/design-tokens`
  - [x] Create role-scoped route groups: `app/(teacher)/`, `app/(parent)/`, `app/(student)/`, `app/auth/`, `app/onboarding/`
  - [x] Create `_layout.tsx` files with placeholder navigation
  - [x] Verify `pnpm dev` starts Expo dev server
- [x] Task 7: Initialize `apps/admin-web` with Vite + React + Tamagui (AC: #4)
  - [x] Set up Vite project with React and TypeScript
  - [x] Install and configure Tamagui (web target) with `@ilm/design-tokens`
  - [x] Set up React Router with sidebar navigation shell
  - [x] Create placeholder pages for admin sections
  - [x] Verify `pnpm dev` starts Vite dev server
- [x] Task 8: Wire up Turborepo task orchestration (AC: #2)
  - [x] Update `turbo.json` if needed for new workspaces
  - [x] Ensure `pnpm dev` runs mobile, admin-web, and api concurrently
  - [x] Verify shared package changes propagate to consuming apps
  - [x] Verify `pnpm build` works across all TS workspaces
- [x] Task 9: Update root configuration (AC: #2, #6)
  - [x] Update `pnpm-workspace.yaml` if needed
  - [x] Update root `package.json` scripts if needed
  - [x] Update `.gitignore` for Expo, Vite build artifacts, iOS/Android directories

## Dev Notes

### Critical: Existing Code Preservation

The `apps/api/` directory contains a **fully functional FastAPI backend** from Epics 1-3 with:
- Complete auth system (email/password + Google OIDC) with JWT tokens
- Admin endpoints (org/user/role management, invitations)
- Course generation with revision history
- Grading pipeline with async AI jobs, recommendations
- Student/progress/notification endpoints
- Comprehensive test suite (13 test files)
- **All repositories use in-memory storage** (no database yet — that's Story 4.3)

**DO NOT modify, move, or break any existing API code.** The API already works with `uvicorn app.main:app`. Ensure Turborepo's `dev` task for the API workspace calls the correct command.

### Current Monorepo State (What Already Exists)

| Component | Current State | Action Needed |
|-----------|--------------|---------------|
| `turbo.json` | Configured with build/dev/lint/test/typecheck tasks | May need updates for new workspace deps |
| `package.json` (root) | pnpm@10.28.2, turbo@^2.5.6 | May need script updates |
| `pnpm-workspace.yaml` | `apps/*` and `packages/*` configured | Already correct |
| `apps/mobile/package.json` | Stub only (`@ilm/mobile`), no deps, no code | **Needs full Expo setup** |
| `apps/admin-web/package.json` | Stub only (`@ilm/admin-web`), no deps, no code | **Needs full Vite setup** |
| `apps/api/` | Fully functional FastAPI app | **Preserve as-is** |
| `packages/contracts/package.json` | Stub only (`@ilm/contracts`), no code | **Needs real TS package setup** |
| `packages/design-tokens/` | **Does not exist** | **Create from scratch** |
| `packages/ui/` | **Does not exist** | **Create from scratch** |
| `packages/eslint-config/` | **Does not exist** | **Create from scratch** |
| `packages/tsconfig/` | **Does not exist** | **Create from scratch** |
| `node_modules/` | Exists with turbo installed | Will grow with new deps |
| `.pnpm-store/` | Exists | pnpm manages this |

### Architecture Patterns and Constraints

**Package naming convention:** `@ilm/<package-name>` (already established)

**Tamagui Design Tokens (from UX Spec):**
- Primary: `#2D6A4F` (sage green)
- Background: `#FAFAF5` (warm off-white)
- Surface: `#FFFFFF`
- Gold accent: `#DDA15E` (growth celebrations)
- Amber: focus areas / attention (never red for below-average)
- Terracotta: errors only
- Font: Inter family throughout; JetBrains Mono for numerical data
- Touch targets: 44px minimum on mobile
- Tab bar: 56px height + safe area
- Transitions: 200-250ms slide/fade
- Loading: warm-toned shimmer, 1.5s cycle
- Token naming: `$camelCase` (e.g., `$primary`, `$textPrimary`, `$radiusMd`)

**File Naming Conventions:**
- TypeScript components: `PascalCase.tsx`
- Non-component TS files: `kebab-case.ts`
- Python: `snake_case.py` (existing API convention)

**Mobile Route Structure (Expo Router):**
```
app/
├── (teacher)/
│   ├── _layout.tsx (5-tab bottom nav + camera FAB)
│   ├── index.tsx (Home)
│   ├── grade.tsx
│   ├── plan.tsx
│   ├── messages.tsx
│   └── settings.tsx
├── (parent)/
│   ├── _layout.tsx (4-tab bottom nav)
│   ├── index.tsx (Dashboard)
│   ├── progress.tsx
│   ├── messages.tsx
│   └── settings.tsx
├── (student)/
│   ├── _layout.tsx (4-tab bottom nav)
│   ├── index.tsx (Growth)
│   ├── progress.tsx
│   ├── tips.tsx
│   └── settings.tsx
├── auth/
├── onboarding/
└── _layout.tsx
```

**Admin-Web Route Structure:**
- Sidebar navigation: Organizations, Users, Roles, Settings, Standards
- React Router (not Expo Router)

**State Management (for later stories but inform structure now):**
- TanStack Query for server state
- Zustand or React context for UI-only state

### Technology Version Guidance

- **Expo SDK:** Use latest stable (SDK 52+ as of early 2026). Verify Tamagui compatibility.
- **Tamagui:** Use latest stable. Ensure `@tamagui/core`, `@tamagui/config`, and web/native targets both work.
- **Vite:** Use latest stable (v6+).
- **React:** 18.x (ensure Expo and Vite agree on React version).
- **TypeScript:** 5.x (shared across all workspaces).
- **pnpm:** Already pinned to 10.28.2 in root package.json.

### What This Story Does NOT Include

- No database setup (Story 4.2/4.3)
- No Docker Compose (Story 4.2)
- No authentication flows in mobile/web (Stories 4.5/4.6)
- No actual screen implementations beyond route stubs
- No CI/CD pipeline changes
- No app store configuration (EAS Build)

### Project Structure Notes

- All new packages MUST be under `packages/` and all new apps under `apps/` per the existing `pnpm-workspace.yaml`
- The API workspace is Python-based; Turborepo handles it alongside TS workspaces via custom task definitions
- Shared packages should use `tsup` for building (fast, zero-config TS bundler) or plain `tsc`

### Testing Standards

- Mobile: co-located `*.test.tsx` for components/hooks
- Admin-web: co-located `*.test.tsx` for components/hooks
- Shared packages: co-located tests or `__tests__/` directory
- For this scaffold story: verify workspaces build and run (no feature tests needed yet)

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries] — Complete directory structure
- [Source: _bmad-output/planning-artifacts/architecture.md#Starter Template Evaluation] — Turborepo selection rationale
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend Architecture] — Mobile and web architecture details
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns & Consistency Rules] — Naming, structure, format patterns
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Core User Experience] — Design system tokens and platform strategy
- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.1] — Story requirements and acceptance criteria

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

N/A

### Completion Notes List

- All 5 TS workspaces typecheck clean (`pnpm run typecheck` — 5/5 tasks pass)
- Admin-web Vite build succeeds (826 modules, 253KB gzip bundle)
- All 268 API tests pass — zero regressions to existing backend
- Scaffold verification tests pass (4/4 in `tests/scaffold.test.mjs`)
- Added `@ilm/tsconfig` as workspace devDep to all consuming packages (was missing, causing tsconfig extends resolution failure)
- Added `@tamagui/themes` as dep to design-tokens (needed for TypeScript type inference of `createTamagui` return type)
- Added missing `test` scripts to contracts, design-tokens, and ui packages
- Network issue required switching npm registry to `registry.npmmirror.com` to complete `pnpm install`

**Code Review Fixes (2026-03-20):**
- Replaced all hardcoded hex color values with `@ilm/design-tokens` imports in mobile tab layouts, auth screen, and admin-web App.tsx
- Created placeholder PNG assets (`icon.png`, `splash-icon.png`, `adaptive-icon.png`, `favicon.png`) in `apps/mobile/assets/`
- Added `*.tsbuildinfo` to `.gitignore`
- Wired up `eslint-plugin-import` ordering rules in `packages/eslint-config/index.js`
- Removed unnecessary `jsx: "react-jsx"` from `packages/design-tokens/tsconfig.json`
- Removed dead `fonts`/`fontSizes` imports from `tamagui.config.ts`

### File List

**packages/tsconfig/**
- `package.json`
- `base.json`
- `react-native.json`
- `react-web.json`

**packages/eslint-config/**
- `package.json`
- `index.js`

**packages/design-tokens/**
- `package.json`
- `tsconfig.json`
- `src/index.ts`
- `src/colors.ts`
- `src/typography.ts`
- `src/spacing.ts`
- `src/tamagui.config.ts`

**packages/ui/**
- `package.json`
- `tsconfig.json`
- `src/index.ts`
- `src/SkeletonLoader.tsx`

**packages/contracts/**
- `package.json`
- `tsconfig.json`
- `src/index.ts`

**apps/mobile/**
- `package.json`
- `tsconfig.json`
- `app.json`
- `assets/icon.png`
- `assets/splash-icon.png`
- `assets/adaptive-icon.png`
- `assets/favicon.png`
- `app/_layout.tsx`
- `app/index.tsx`
- `app/(teacher)/_layout.tsx`
- `app/(teacher)/index.tsx`
- `app/(teacher)/grade.tsx`
- `app/(teacher)/plan.tsx`
- `app/(teacher)/messages.tsx`
- `app/(teacher)/settings.tsx`
- `app/(parent)/_layout.tsx`
- `app/(parent)/index.tsx`
- `app/(parent)/progress.tsx`
- `app/(parent)/messages.tsx`
- `app/(parent)/settings.tsx`
- `app/(student)/_layout.tsx`
- `app/(student)/index.tsx`
- `app/(student)/progress.tsx`
- `app/(student)/tips.tsx`
- `app/(student)/settings.tsx`
- `app/auth/index.tsx`
- `app/onboarding/index.tsx`

**apps/admin-web/**
- `package.json`
- `tsconfig.json`
- `vite.config.ts`
- `index.html`
- `vite-env.d.ts`
- `src/main.tsx`
- `src/App.tsx`

**Root (modified)**
- `.gitignore`
- `package.json`
- `pnpm-lock.yaml`
