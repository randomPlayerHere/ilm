# Story 4.4: Mobile App Shell with Role-Scoped Navigation

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want to open the mobile app and see navigation tailored to my role,
so that I can access the features relevant to me without confusion.

## Acceptance Criteria

1. **Teacher bottom tab navigation:**
   - Teacher sees 5 tabs: Home, Grade, Plan, Messages, More
   - A persistent camera FAB button (56px circle, `primary` background, white camera icon) is visible on all teacher screens
   - FAB positioned bottom-right, 24px from edges, above the tab bar, with `elevation-2` shadow
   - Tab bar: 56px height + safe area inset, `primary` active icon (filled), `text-secondary` inactive (outlined), `caption` labels (12px)
   - Light haptic feedback on tab switch

2. **Parent bottom tab navigation:**
   - Parent sees 4 tabs: Dashboard, Progress, Messages, Settings
   - Same tab bar styling as teacher (56px + safe area, `primary`/`text-secondary` colors)

3. **Student bottom tab navigation:**
   - Student sees 4 tabs: Growth, Progress, Tips, Settings
   - Same tab bar styling as teacher

4. **Navigation behavior and UX:**
   - Tab transitions use cross-fade at 200ms (per UX spec)
   - Skeleton loading states appear on all data-dependent screens
   - App uses "Clear Path" design: warm off-white background (`#FAFAF5`), surface cards (`#FFFFFF`), sage green primary (`#2D6A4F`)
   - All screens use `SafeAreaView` for proper inset handling
   - Tab icons use filled variant when active, outlined when inactive
   - Minimum 44x44px touch targets on all interactive elements

5. **Reduced motion and accessibility:**
   - Respects OS `prefers-reduced-motion` setting (instant transitions when active)
   - Screen reader labels on all tab bar items and FAB
   - Focus indicators on all focusable elements

## Tasks / Subtasks

- [x] Task 1: Add `expo-haptics` dependency (AC: #1)
  - [x] Run `npx expo install expo-haptics` in `apps/mobile/`

- [x] Task 2: Create tab bar icon mapping component (AC: #1, #2, #3)
  - [x] Create `apps/mobile/src/navigation/tab-icons.tsx` — centralized icon mapping using `@expo/vector-icons/MaterialCommunityIcons`
  - [x] Map each tab name to filled (active) and outlined (inactive) icon variants
  - [x] Teacher icons: `home`/`home-outline`, `clipboard-check`/`clipboard-check-outline`, `book-open-page-variant`/`book-open-page-variant-outline`, `message`/`message-outline`, `dots-horizontal`/`menu`
  - [x] Parent icons: `view-dashboard`/`view-dashboard-outline`, `chart-line`/`chart-line-variant`, `message`/`message-outline`, `cog`/`cog-outline`
  - [x] Student icons: `trending-up`/`chart-timeline-variant`, `chart-line`/`chart-line-variant`, `lightbulb`/`lightbulb-outline`, `cog`/`cog-outline`

- [x] Task 3: Create Camera FAB component (AC: #1)
  - [x] Create `apps/mobile/src/components/CameraFab.tsx`
  - [x] 56px diameter circle, `primary` (`#2D6A4F`) background, white camera icon (`camera` from MaterialCommunityIcons)
  - [x] Position: absolute, bottom-right, 24px from right edge, positioned above tab bar (bottom = tabBarHeight + safeArea.bottom + 24)
  - [x] `elevation-2` shadow from design tokens (`shadows.md`)
  - [x] Press state: slightly darker green (`primaryDark` `#1B4332`) + `Haptics.impactAsync(ImpactFeedbackStyle.Light)`
  - [x] `accessibilityLabel="Open camera for grading"` and `accessibilityRole="button"`
  - [x] onPress: no-op for now (wired in future grading story) — navigate to placeholder or log

- [x] Task 4: Update root layout with SafeAreaProvider (AC: #4, #5)
  - [x] Wrap `TamaguiProvider` content with `SafeAreaProvider` from `react-native-safe-area-context` in `apps/mobile/app/_layout.tsx`

- [x] Task 5: Update teacher tab layout (AC: #1, #4, #5)
  - [x] Update `apps/mobile/app/(teacher)/_layout.tsx`:
    - Add `tabBarIcon` to each `Tabs.Screen` using the icon mapping from Task 2
    - Set `tabBarStyle` to include safe area bottom inset, `surface` background, `elevation-2` top border/shadow
    - Add `tabBarLabelStyle` with `caption` font size (12px) from design tokens
    - Add haptic feedback via `tabBarButton` wrapper or `screenListeners.tabPress`
    - Import and render `<CameraFab />` as an overlay above the Tabs

- [x] Task 6: Update parent tab layout (AC: #2, #4, #5)
  - [x] Update `apps/mobile/app/(parent)/_layout.tsx` with icons, tab bar styling, haptics (same pattern as teacher, no FAB)

- [x] Task 7: Update student tab layout (AC: #3, #4, #5)
  - [x] Update `apps/mobile/app/(student)/_layout.tsx` with icons, tab bar styling, haptics (same pattern as parent)

- [x] Task 8: Create placeholder screen components with skeleton states (AC: #4)
  - [x] Update all 13 screen files (`(teacher)/*.tsx`, `(parent)/*.tsx`, `(student)/*.tsx`) to:
    - Replace `react-native` View/Text with Tamagui `YStack`/`XStack`/`Text` components
    - Use `background` color (`#FAFAF5`) as screen background
    - Add `SafeAreaView` wrapper
    - Include a title text and 2-3 `SkeletonLoader` components (from `@ilm/ui`) to simulate loading state
    - Add `card` variant skeletons in a `YStack` with `lg` (16px) gap

- [x] Task 9: Add reduced motion support (AC: #5)
  - [x] Create `apps/mobile/src/hooks/useReducedMotion.ts` — wraps `AccessibilityInfo.isReduceMotionEnabled()` (or use `useReducedMotion` from `react-native-reanimated` if installed, otherwise plain RN API)
  - [x] When reduced motion is active, set transition duration to 0ms for tab switches and disable skeleton shimmer animation

- [x] Task 10: Verify and test (AC: all)
  - [x] Verify all 3 role layouts render correct number of tabs with correct labels
  - [x] Verify FAB appears only on teacher screens
  - [x] Verify tab icons switch between filled/outlined on active/inactive
  - [x] Verify skeleton loaders appear on placeholder screens
  - [x] Run `pnpm typecheck` from monorepo root — zero TypeScript errors

## Dev Notes

### Existing Code Foundation (from Story 4.1)

The mobile app scaffold is already in place with Expo Router file-based routing. Key files:

```
apps/mobile/
├── app/
│   ├── _layout.tsx          # Root: TamaguiProvider + Slot (UPDATE: add SafeAreaProvider)
│   ├── index.tsx            # Redirect to /auth
│   ├── auth/index.tsx       # Auth placeholder
│   ├── onboarding/index.tsx # Onboarding placeholder
│   ├── (teacher)/
│   │   ├── _layout.tsx      # Tabs with 5 screens (UPDATE: add icons, FAB, haptics)
│   │   ├── index.tsx        # Home placeholder (UPDATE: add skeleton)
│   │   ├── grade.tsx        # Grade placeholder (UPDATE)
│   │   ├── plan.tsx         # Plan placeholder (UPDATE)
│   │   ├── messages.tsx     # Messages placeholder (UPDATE)
│   │   └── settings.tsx     # More/Settings placeholder (UPDATE)
│   ├── (parent)/
│   │   ├── _layout.tsx      # Tabs with 4 screens (UPDATE: add icons, haptics)
│   │   └── ... 4 screen files (UPDATE each)
│   └── (student)/
│       ├── _layout.tsx      # Tabs with 4 screens (UPDATE: add icons, haptics)
│       └── ... 4 screen files (UPDATE each)
```

### Design Tokens Already Available

All tokens are importable from `@ilm/design-tokens`:

```typescript
import { colors, layout, spacing, radii, shadows, fonts, fontSizes } from "@ilm/design-tokens";

// colors.primary = "#2D6A4F" (active tab, FAB bg)
// colors.textSecondary = "#6B7280" (inactive tab)
// colors.background = "#FAFAF5" (screen bg)
// colors.surface = "#FFFFFF" (card bg, tab bar bg)
// colors.primaryDark = "#1B4332" (FAB pressed state)
// layout.tabBarHeight = 56
// layout.minTouchTarget = 44
// layout.transitionDuration = 225
// shadows.md = elevation-2 shadow
// radii.full = 9999 (circular FAB)
```

### SkeletonLoader Already Available

Import from `@ilm/ui`:

```typescript
import { SkeletonLoader } from "@ilm/ui";

// Variants: "line", "circle", "card", "thumbnail"
// Uses $surfaceSecondary bg, $md border radius, "lazy" animation
```

### Icon Library — @expo/vector-icons

Bundled with Expo SDK 52 — no install needed. Import:

```typescript
import MaterialCommunityIcons from '@expo/vector-icons/MaterialCommunityIcons';
```

Use with `tabBarIcon`:
```typescript
tabBarIcon: ({ focused, color, size }) => (
  <MaterialCommunityIcons
    name={focused ? "home" : "home-outline"}
    size={size}
    color={color}
  />
)
```

### expo-haptics API

```typescript
import * as Haptics from 'expo-haptics';

// Tab switch: Haptics.selectionAsync()
// FAB press: Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light)
```

Add to tab press listener in each layout:
```typescript
screenListeners={{
  tabPress: () => Haptics.selectionAsync(),
}}
```

### Camera FAB Positioning

The FAB must float above the tab bar on ALL teacher screens. Implementation approach:

```typescript
// In (teacher)/_layout.tsx, wrap Tabs in a View and overlay FAB:
export default function TeacherLayout() {
  const insets = useSafeAreaInsets();
  return (
    <View style={{ flex: 1 }}>
      <Tabs screenOptions={...}>
        {/* screens */}
      </Tabs>
      <CameraFab bottomOffset={layout.tabBarHeight + insets.bottom + 24} />
    </View>
  );
}
```

FAB is purely presentational in this story — `onPress` should be a no-op or console.log. The camera grading flow is wired in Epic 5.

### Tab Bar Styling Spec

```typescript
tabBarStyle: {
  height: layout.tabBarHeight + insets.bottom,
  paddingBottom: insets.bottom,
  backgroundColor: colors.surface,
  borderTopWidth: 1,
  borderTopColor: colors.border,
  ...shadows.md, // elevation-2
}
tabBarLabelStyle: {
  fontSize: 12,
  fontFamily: fonts.body, // "Inter"
  fontWeight: fontWeights.medium, // "500"
}
```

### Screen Placeholder Pattern

Each screen should look like this (replace View/Text with Tamagui):

```tsx
import { YStack, Text } from "tamagui";
import { SafeAreaView } from "react-native-safe-area-context";
import { SkeletonLoader } from "@ilm/ui";
import { colors, spacing } from "@ilm/design-tokens";

export default function TeacherHome() {
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.background }} edges={["top"]}>
      <YStack flex={1} padding="$lg" gap="$lg" backgroundColor="$background">
        <Text fontSize="$2xl" fontWeight="700" color="$textPrimary">Home</Text>
        <SkeletonLoader variant="card" />
        <SkeletonLoader variant="card" />
        <SkeletonLoader variant="line" />
      </YStack>
    </SafeAreaView>
  );
}
```

**Critical:** Use `edges={["top"]}` on SafeAreaView so the tab bar handles bottom safe area — do NOT double-pad bottom.

### What NOT to Do

- **Do NOT install react-native-reanimated** — not needed for tab navigation. Expo Router handles transitions natively.
- **Do NOT create a custom tab bar component** — use React Navigation's built-in tab bar via `screenOptions`. Custom tab bars introduce unnecessary complexity and break default accessibility.
- **Do NOT modify any API code** (apps/api/) — this story is mobile-only.
- **Do NOT implement auth flow or role detection** — Story 4.5/4.6 handles auth. For now, use direct navigation to a role group for testing.
- **Do NOT add TanStack Query or API client** — no data fetching in this story. Screens are placeholders with skeletons.
- **Do NOT add `expo-router/drawer`** or nested stack navigators — only bottom tabs in this story.
- **Do NOT use `Animated` or `react-native-reanimated` for skeleton shimmer** — the `@ilm/ui` SkeletonLoader already handles animation via Tamagui's `animation: "lazy"`.

### Reduced Motion Support

React Native provides `AccessibilityInfo.isReduceMotionEnabled()`. Create a simple hook:

```typescript
import { useEffect, useState } from "react";
import { AccessibilityInfo } from "react-native";

export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    AccessibilityInfo.isReduceMotionEnabled().then(setReduced);
    const sub = AccessibilityInfo.addEventListener("reduceMotionChanged", setReduced);
    return () => sub.remove();
  }, []);
  return reduced;
}
```

### Project Structure Notes

New files this story creates:

```text
apps/mobile/src/navigation/tab-icons.tsx    # NEW: centralized icon mapping
apps/mobile/src/components/CameraFab.tsx    # NEW: teacher camera FAB
apps/mobile/src/hooks/useReducedMotion.ts   # NEW: accessibility hook
```

Modified files:

```text
apps/mobile/app/_layout.tsx                 # ADD SafeAreaProvider wrapper
apps/mobile/app/(teacher)/_layout.tsx       # ADD icons, FAB, haptics, styling
apps/mobile/app/(parent)/_layout.tsx        # ADD icons, haptics, styling
apps/mobile/app/(student)/_layout.tsx       # ADD icons, haptics, styling
apps/mobile/app/(teacher)/index.tsx         # REPLACE with Tamagui + skeleton
apps/mobile/app/(teacher)/grade.tsx         # REPLACE with Tamagui + skeleton
apps/mobile/app/(teacher)/plan.tsx          # REPLACE with Tamagui + skeleton
apps/mobile/app/(teacher)/messages.tsx      # REPLACE with Tamagui + skeleton
apps/mobile/app/(teacher)/settings.tsx      # REPLACE with Tamagui + skeleton
apps/mobile/app/(parent)/index.tsx          # REPLACE with Tamagui + skeleton
apps/mobile/app/(parent)/progress.tsx       # REPLACE with Tamagui + skeleton
apps/mobile/app/(parent)/messages.tsx       # REPLACE with Tamagui + skeleton
apps/mobile/app/(parent)/settings.tsx       # REPLACE with Tamagui + skeleton
apps/mobile/app/(student)/index.tsx         # REPLACE with Tamagui + skeleton
apps/mobile/app/(student)/progress.tsx      # REPLACE with Tamagui + skeleton
apps/mobile/app/(student)/tips.tsx          # REPLACE with Tamagui + skeleton
apps/mobile/app/(student)/settings.tsx      # REPLACE with Tamagui + skeleton
apps/mobile/package.json                    # ADD expo-haptics dependency
```

**No other files should be modified.** The `packages/design-tokens/` and `packages/ui/` packages are used as-is.

### Technology Versions (from Story 4.1 baseline)

- **Expo SDK:** ~52.0.0
- **Expo Router:** ~4.0.0 (built on React Navigation v7)
- **React Native:** 0.76.7 (New Architecture enabled)
- **Tamagui:** ^1.114.0
- **react-native-safe-area-context:** ~5.0.0
- **@expo/vector-icons:** bundled with Expo SDK 52 (no separate install)
- **expo-haptics:** install via `npx expo install expo-haptics`

### Previous Story Intelligence (Story 4.3)

Story 4.3 was backend-only (SQLAlchemy models + Alembic migrations). Key learnings:
- The project uses `uv` for Python dependency management in `apps/api/`
- Docker Compose runs the backend services (PostgreSQL, MinIO, API, Worker)
- Code review caught duplicate indexes and false task completions — be thorough about marking tasks done only when verified
- The mobile app was untouched in 4.3 — the scaffold from 4.1 is the baseline

### Git Intelligence

Recent commits (4.1 → 4.3) focused on backend infrastructure. The mobile app files were created in 4.1 with minimal placeholders. No mobile-specific patterns or conventions have been established beyond the initial scaffold — this story sets the mobile UI foundation.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.4] — Story requirements and BDD acceptance criteria
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Navigation Patterns] — Tab bar specs, FAB, role-scoped navigation
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Design Tokens] — Colors, typography, spacing, shadows, radii
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Animation & Motion] — Transition specs, haptics, reduced motion
- [Source: _bmad-output/planning-artifacts/architecture.md#Mobile Architecture] — Expo/React Native patterns, offline support, state management
- [Source: _bmad-output/implementation-artifacts/4-3-database-schema-initialization-and-migrations.md] — Previous story context (backend-only, no mobile changes)
- [Source: packages/design-tokens/src/] — All token definitions (colors.ts, typography.ts, spacing.ts, tamagui.config.ts)
- [Source: packages/ui/src/SkeletonLoader.tsx] — Existing skeleton component

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- TypeScript initially failed on `@expo/vector-icons/MaterialCommunityIcons` subpath import due to pnpm strict node_modules. Fixed by using named import `{ MaterialCommunityIcons } from "@expo/vector-icons"` and adding `@expo/vector-icons` as explicit dependency.

### Completion Notes List

- Installed `expo-haptics@~14.0.1` and `@expo/vector-icons@~14.0.4` as explicit dependencies
- Created centralized icon mapping (`tab-icons.tsx`) with `getTabBarIcon()` helper for all 3 roles
- Created `CameraFab` component: 56px circle, primary green, absolute positioning above tab bar, haptic feedback on press, accessibility labels
- Added `SafeAreaProvider` wrapper in root layout
- Updated all 3 role layouts with: icons, tab bar styling (56px + safe area, surface bg, elevation-2 shadow, 12px caption labels), haptic feedback via `screenListeners.tabPress`, fade animation with reduced motion support
- Teacher layout additionally renders CameraFab overlay
- Updated all 13 screen files: replaced `react-native` View/Text with Tamagui YStack/Text, added SafeAreaView with `edges={["top"]}`, added SkeletonLoader (2x card + 1x line) with warm off-white background
- Created `useReducedMotion` hook using `AccessibilityInfo` API; integrated into all 3 layouts to disable animations when OS reduced motion is active
- `pnpm typecheck` passes with zero errors across all packages

### File List

New files:
- apps/mobile/src/navigation/tab-icons.tsx
- apps/mobile/src/components/CameraFab.tsx
- apps/mobile/src/hooks/useReducedMotion.ts
- apps/mobile/src/contexts/ReducedMotionContext.tsx

Modified files:
- apps/mobile/app/_layout.tsx
- apps/mobile/app/(teacher)/_layout.tsx
- apps/mobile/app/(teacher)/index.tsx
- apps/mobile/app/(teacher)/grade.tsx
- apps/mobile/app/(teacher)/plan.tsx
- apps/mobile/app/(teacher)/messages.tsx
- apps/mobile/app/(teacher)/settings.tsx
- apps/mobile/app/(parent)/_layout.tsx
- apps/mobile/app/(parent)/index.tsx
- apps/mobile/app/(parent)/progress.tsx
- apps/mobile/app/(parent)/messages.tsx
- apps/mobile/app/(parent)/settings.tsx
- apps/mobile/app/(student)/_layout.tsx
- apps/mobile/app/(student)/index.tsx
- apps/mobile/app/(student)/progress.tsx
- apps/mobile/app/(student)/tips.tsx
- apps/mobile/app/(student)/settings.tsx
- apps/mobile/package.json
- pnpm-lock.yaml

## Change Log

- 2026-03-20: Implemented mobile app shell with role-scoped bottom tab navigation (teacher 5 tabs + camera FAB, parent 4 tabs, student 4 tabs), skeleton placeholder screens using Tamagui + @ilm/ui SkeletonLoader, haptic feedback on tab switches, reduced motion accessibility support, and Clear Path design token integration.
- 2026-03-21: Code review fixes — (H1) Fixed student tab order to match UX spec: Growth/Tips/Progress/Settings. (H2) Added ReducedMotionContext and disabled skeleton shimmer animation when OS reduced-motion is active across all 13 screens. (H4) Added focus indicator styling to CameraFab, added tabBarAccessibilityLabel to all tab screens across all 3 role layouts. (M2) Explicit screen reader labels on all tab bar items. (M3) CameraFab RTL layout support via I18nManager.isRTL. (H3-noted) Tab fade transition uses React Navigation's default duration (~150ms) — exact 200ms not configurable without custom tab bar, which is explicitly prohibited by this story.
