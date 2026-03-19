/**
 * Teacher OS color tokens — "Clear Path" design direction.
 * Warm growth palette: greens/golds for progress, amber for focus, terracotta for errors.
 */
export const colors = {
  // Primary
  primary: "#2D6A4F",
  primaryLight: "#40916C",
  primaryDark: "#1B4332",

  // Background & Surface
  background: "#FAFAF5",
  surface: "#FFFFFF",
  surfaceSecondary: "#F5F5F0",

  // Accent — growth celebrations
  gold: "#DDA15E",
  goldLight: "#E9C46A",

  // Focus areas — warm amber (never red for below-average)
  amber: "#E76F51",
  amberLight: "#F4A261",

  // Error — terracotta (errors only)
  error: "#BC4749",
  errorLight: "#D4726A",

  // Text hierarchy
  textPrimary: "#1A1A1A",
  textSecondary: "#6B7280",
  textTertiary: "#9CA3AF",
  textInverse: "#FFFFFF",

  // Borders & dividers
  border: "#E5E5E0",
  borderFocus: "#2D6A4F",

  // AI confidence badges
  confidenceHigh: "#2D6A4F",
  confidenceMedium: "#F4A261",
  confidenceLow: "#BC4749",

  // Status
  success: "#2D6A4F",
  warning: "#F4A261",
  info: "#3B82F6",
} as const;
