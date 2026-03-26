import { useEffect, useRef, useState } from "react";
import {
  Animated,
  Image,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";
import type { GradingJobWithResultResponse } from "@ilm/contracts";
import { colors, fonts, fontWeights, radii } from "@ilm/design-tokens";

interface GradingCardProps {
  status: "uploading" | "processing" | "completed" | "failed";
  result: GradingJobWithResultResponse | null;
  photoUri: string | null;
  error: string | null;
}

const CONFIDENCE_COLORS: Record<string, string> = {
  high: colors.confidenceHigh,
  medium: colors.confidenceMedium,
  low: colors.confidenceLow,
};

function SkeletonBox({ style }: { style?: object }) {
  const fadeAnim = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(fadeAnim, { toValue: 0.8, duration: 800, useNativeDriver: true }),
        Animated.timing(fadeAnim, { toValue: 0.3, duration: 800, useNativeDriver: true }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [fadeAnim]);

  return (
    <Animated.View
      style={[styles.skeletonBox, style, { opacity: fadeAnim }]}
    />
  );
}

export function GradingCard({ status, result, photoUri, error }: GradingCardProps) {
  const [rubricExpanded, setRubricExpanded] = useState(false);

  if (status === "uploading" || status === "processing") {
    return (
      <View style={styles.card}>
        <View style={styles.skeletonRow}>
          <SkeletonBox style={styles.skeletonPhoto} />
          <View style={styles.skeletonTextColumn}>
            <SkeletonBox style={styles.skeletonScore} />
            <SkeletonBox style={styles.skeletonBadge} />
          </View>
        </View>
        <SkeletonBox style={styles.skeletonFeedback} />
        <SkeletonBox style={styles.skeletonFeedbackLine2} />
      </View>
    );
  }

  if (status === "failed") {
    return (
      <View style={styles.card}>
        <Text style={styles.errorTitle}>Couldn't analyze this one</Text>
        {error ? <Text style={styles.errorDetail}>{error}</Text> : null}
      </View>
    );
  }

  // Completed state
  if (!result?.result) {
    return (
      <View style={styles.card}>
        <Text style={styles.errorTitle}>No grading result available</Text>
      </View>
    );
  }

  const { proposed_score, draft_feedback, confidence_level, rubric_mapping } = result.result;
  const confidenceColor = CONFIDENCE_COLORS[confidence_level] ?? colors.confidenceMedium;
  const confidenceLabel =
    confidence_level === "high" ? "High" : confidence_level === "medium" ? "Medium" : "Low";

  return (
    <View style={styles.card}>
      <View style={styles.resultRow}>
        {photoUri ? (
          <Image source={{ uri: photoUri }} style={styles.thumbnail} />
        ) : (
          <View style={[styles.thumbnail, styles.thumbnailPlaceholder]} />
        )}
        <View style={styles.scoreColumn}>
          <Text style={styles.scoreText}>{proposed_score}</Text>
          <View style={[styles.confidenceBadge, { backgroundColor: confidenceColor }]}>
            <Text style={styles.confidenceBadgeText}>{confidenceLabel}</Text>
          </View>
        </View>
      </View>

      <Text style={styles.feedbackText}>{draft_feedback}</Text>

      {rubric_mapping && Object.keys(rubric_mapping).length > 0 ? (
        <View style={styles.rubricSection}>
          <Pressable
            onPress={() => setRubricExpanded((v) => !v)}
            accessibilityRole="button"
            style={styles.rubricToggle}
          >
            <Text style={styles.rubricToggleText}>
              Rubric breakdown {rubricExpanded ? "▲" : "▼"}
            </Text>
          </Pressable>
          {rubricExpanded ? (
            <View style={styles.rubricList}>
              {Object.entries(rubric_mapping).map(([criterion, rating]) => (
                <View key={criterion} style={styles.rubricRow}>
                  <Text style={styles.rubricCriterion}>{criterion}</Text>
                  <Text style={styles.rubricRating}>{rating}</Text>
                </View>
              ))}
            </View>
          ) : null}
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radii.lg,
    padding: 16,
    gap: 12,
  },
  skeletonBox: {
    backgroundColor: colors.border,
    borderRadius: radii.sm,
  },
  skeletonRow: {
    flexDirection: "row",
    gap: 12,
  },
  skeletonPhoto: {
    width: 80,
    height: 80,
    borderRadius: radii.md,
  },
  skeletonTextColumn: {
    flex: 1,
    gap: 8,
    justifyContent: "center",
  },
  skeletonScore: {
    height: 28,
    width: "60%",
  },
  skeletonBadge: {
    height: 20,
    width: "40%",
    borderRadius: radii.full,
  },
  skeletonFeedback: {
    height: 16,
    width: "100%",
  },
  skeletonFeedbackLine2: {
    height: 16,
    width: "80%",
  },
  resultRow: {
    flexDirection: "row",
    gap: 12,
    alignItems: "flex-start",
  },
  thumbnail: {
    width: 80,
    height: 80,
    borderRadius: radii.md,
  },
  thumbnailPlaceholder: {
    backgroundColor: colors.border,
  },
  scoreColumn: {
    flex: 1,
    gap: 8,
    justifyContent: "center",
  },
  scoreText: {
    fontSize: 28,
    fontFamily: fonts.heading,
    fontWeight: fontWeights.bold,
    color: colors.textPrimary,
  },
  confidenceBadge: {
    alignSelf: "flex-start",
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: radii.full,
  },
  confidenceBadgeText: {
    fontSize: 12,
    fontFamily: fonts.body,
    fontWeight: fontWeights.semibold,
    color: colors.textInverse,
  },
  feedbackText: {
    fontSize: 15,
    fontFamily: fonts.body,
    color: colors.textSecondary,
    lineHeight: 22,
  },
  rubricSection: {
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: 8,
  },
  rubricToggle: {
    paddingVertical: 4,
  },
  rubricToggleText: {
    fontSize: 14,
    fontFamily: fonts.body,
    fontWeight: fontWeights.medium,
    color: colors.primary,
  },
  rubricList: {
    marginTop: 8,
    gap: 6,
  },
  rubricRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 8,
  },
  rubricCriterion: {
    flex: 1,
    fontSize: 13,
    fontFamily: fonts.body,
    color: colors.textPrimary,
  },
  rubricRating: {
    fontSize: 13,
    fontFamily: fonts.body,
    fontWeight: fontWeights.medium,
    color: colors.textSecondary,
  },
  errorTitle: {
    fontSize: 17,
    fontFamily: fonts.heading,
    fontWeight: fontWeights.semibold,
    color: colors.error,
    textAlign: "center",
  },
  errorDetail: {
    fontSize: 14,
    fontFamily: fonts.body,
    color: colors.textSecondary,
    textAlign: "center",
  },
});
