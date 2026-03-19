import { createTamagui } from "@tamagui/core";
import { config as defaultConfig } from "@tamagui/config/v3";
import { colors } from "./colors";
import { spacing, radii } from "./spacing";

const tamaguiConfig = createTamagui({
  ...defaultConfig,
  tokens: {
    ...defaultConfig.tokens,
    color: {
      ...defaultConfig.tokens.color,
      primary: colors.primary,
      primaryLight: colors.primaryLight,
      primaryDark: colors.primaryDark,
      background: colors.background,
      surface: colors.surface,
      surfaceSecondary: colors.surfaceSecondary,
      gold: colors.gold,
      goldLight: colors.goldLight,
      amber: colors.amber,
      amberLight: colors.amberLight,
      error: colors.error,
      errorLight: colors.errorLight,
      textPrimary: colors.textPrimary,
      textSecondary: colors.textSecondary,
      textTertiary: colors.textTertiary,
      textInverse: colors.textInverse,
      border: colors.border,
      borderFocus: colors.borderFocus,
      confidenceHigh: colors.confidenceHigh,
      confidenceMedium: colors.confidenceMedium,
      confidenceLow: colors.confidenceLow,
      success: colors.success,
      warning: colors.warning,
      info: colors.info,
    },
    space: {
      ...defaultConfig.tokens.space,
      xs: spacing.xs,
      sm: spacing.sm,
      md: spacing.md,
      lg: spacing.lg,
      xl: spacing.xl,
      "2xl": spacing["2xl"],
      "3xl": spacing["3xl"],
      "4xl": spacing["4xl"],
    },
    size: {
      ...defaultConfig.tokens.size,
      xs: spacing.xs,
      sm: spacing.sm,
      md: spacing.md,
      lg: spacing.lg,
      xl: spacing.xl,
      "2xl": spacing["2xl"],
      "3xl": spacing["3xl"],
      "4xl": spacing["4xl"],
    },
    radius: {
      ...defaultConfig.tokens.radius,
      sm: radii.sm,
      md: radii.md,
      lg: radii.lg,
      xl: radii.xl,
      full: radii.full,
    },
    zIndex: defaultConfig.tokens.zIndex,
  },
});

export type AppConfig = typeof tamaguiConfig;

declare module "@tamagui/core" {
  interface TamaguiCustomConfig extends AppConfig {}
}

export default tamaguiConfig;
