import { styled, Stack } from "@tamagui/core";

/**
 * Content-shaped loading placeholder with warm-toned shimmer.
 * Cycle: 1.5s per UX spec.
 */
export const SkeletonLoader = styled(Stack, {
  backgroundColor: "$surfaceSecondary",
  borderRadius: "$md",
  overflow: "hidden",
  animation: "lazy",

  variants: {
    variant: {
      line: {
        height: 14,
        width: "80%",
      },
      circle: {
        height: 48,
        width: 48,
        borderRadius: "$full",
      },
      card: {
        height: 120,
        width: "100%",
      },
      thumbnail: {
        height: 80,
        width: 80,
      },
    },
  } as const,

  defaultVariants: {
    variant: "line",
  },
});
