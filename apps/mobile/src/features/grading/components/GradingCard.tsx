import { useEffect, useRef, useState } from "react";
import {
  Animated,
  Image,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import type { GradingJobWithResultResponse } from "@ilm/contracts";
import type { GradingReviewControls } from "../hooks/useGradingReview";
import type { GradeApprovalControls } from "../hooks/useGradeApproval";
import type { ManualGradingControls } from "../hooks/useManualGrading";
import { colors, fonts, fontWeights, radii } from "@ilm/design-tokens";

interface GradingCardProps {
  status: "uploading" | "processing" | "completed" | "failed";
  result: GradingJobWithResultResponse | null;
  photoUri: string | null;
  error: string | null;
  reviewControls?: GradingReviewControls | null;
  approvalControls?: GradeApprovalControls | null;
  processingHint?: string | null;
  onRetakePhoto?: () => void;
  onGradeManually?: () => void;
  manualGradingControls?: ManualGradingControls | null;
}

const CONFIDENCE_COLORS: Record<string, string> = {
  high: colors.confidenceHigh,
  medium: colors.confidenceMedium,
  low: colors.confidenceLow,
};

function SkeletonBox({ style }: { style?: object }) {
  const fadeAnim = useRef(new Animated.Value(0.3)).current;
  const shouldAnimate = process.env.NODE_ENV !== "test";

  useEffect(() => {
    if (!shouldAnimate) {
      return;
    }

    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(fadeAnim, { toValue: 0.8, duration: 800, useNativeDriver: true }),
        Animated.timing(fadeAnim, { toValue: 0.3, duration: 800, useNativeDriver: true }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [fadeAnim, shouldAnimate]);

  return (
    <Animated.View
      style={[styles.skeletonBox, style, { opacity: fadeAnim }]}
    />
  );
}

export function GradingCard({ status, result, photoUri, error, reviewControls, approvalControls, processingHint, onRetakePhoto, onGradeManually, manualGradingControls }: GradingCardProps) {
  const [rubricExpanded, setRubricExpanded] = useState(false);
  const [manualRubricExpanded, setManualRubricExpanded] = useState(false);
  const approvedFadeAnim = useRef(new Animated.Value(approvalControls?.isApproved ? 1 : 0)).current;
  const prevIsApprovedRef = useRef(approvalControls?.isApproved ?? false);
  const shouldAnimate = process.env.NODE_ENV !== "test";

  useEffect(() => {
    const wasApproved = prevIsApprovedRef.current;
    const isNowApproved = approvalControls?.isApproved ?? false;
    prevIsApprovedRef.current = isNowApproved;
    if (isNowApproved && !wasApproved && shouldAnimate) {
      Animated.timing(approvedFadeAnim, { toValue: 1, duration: 400, useNativeDriver: true }).start();
    }
  }, [approvalControls?.isApproved, approvedFadeAnim, shouldAnimate]);

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
        {processingHint ? (
          <Text style={styles.processingHint}>{processingHint}</Text>
        ) : null}
      </View>
    );
  }

  if (status === "failed") {
    if (manualGradingControls != null) {
      // Manual grading form
      const { scoreValue, scoreInputText, feedbackValue, isSubmitting, isSubmitted, submitError: manualSubmitError, rubricCriteria, increment: manualIncrement, decrement: manualDecrement, setScore: manualSetScore, setFeedback: manualSetFeedback, submit } = manualGradingControls;
      return (
        <View style={styles.card}>
          <Text style={styles.manualHeading}>Grade Manually</Text>
          {photoUri ? (
            <Image source={{ uri: photoUri }} style={styles.thumbnail} accessibilityLabel="Student work" />
          ) : null}
          <View style={styles.scoreEditRow}>
            <Pressable
              onPress={manualDecrement}
              accessibilityRole="button"
              accessibilityLabel="Decrease manual score"
              style={styles.scoreButton}
              hitSlop={8}
            >
              <Text style={styles.scoreButtonText}>−</Text>
            </Pressable>
            <TextInput
              style={styles.scoreInput}
              value={scoreInputText}
              onChangeText={manualSetScore}
              keyboardType="number-pad"
              maxLength={3}
              accessibilityLabel="Manual score"
              accessibilityValue={{ min: 0, max: 100, now: scoreValue }}
            />
            <Text style={styles.scoreDivider}>/100</Text>
            <Pressable
              onPress={manualIncrement}
              accessibilityRole="button"
              accessibilityLabel="Increase manual score"
              style={styles.scoreButton}
              hitSlop={8}
            >
              <Text style={styles.scoreButtonText}>+</Text>
            </Pressable>
          </View>
          <TextInput
            style={styles.feedbackInput}
            value={feedbackValue}
            onChangeText={manualSetFeedback}
            multiline
            accessibilityLabel="Manual feedback"
            placeholder="Enter feedback..."
          />
          {rubricCriteria.length > 0 ? (
            <View style={styles.rubricSection}>
              <Pressable
                onPress={() => setManualRubricExpanded((v) => !v)}
                accessibilityRole="button"
                style={styles.rubricToggle}
              >
                <Text style={styles.rubricToggleText}>
                  Rubric criteria {manualRubricExpanded ? "▲" : "▼"}
                </Text>
              </Pressable>
              {manualRubricExpanded ? (
                <View style={styles.rubricList}>
                  {rubricCriteria.map((item) => (
                    <View key={item.criterion} style={styles.rubricRow}>
                      <Text style={styles.rubricCriterion}>{item.criterion}</Text>
                      {item.description ? (
                        <Text style={styles.rubricRating}>{item.description}</Text>
                      ) : null}
                    </View>
                  ))}
                </View>
              ) : null}
            </View>
          ) : null}
          {manualSubmitError ? (
            <Text style={styles.approvalErrorText}>{manualSubmitError}</Text>
          ) : null}
          {isSubmitted ? (
            <Text style={styles.submittedText}>Grade submitted ✓</Text>
          ) : (
            <Pressable
              onPress={submit}
              accessibilityRole="button"
              accessibilityLabel="Submit manual grade"
              accessibilityState={{ disabled: isSubmitting }}
              style={[styles.submitButton, isSubmitting && styles.approveButtonDisabled]}
              disabled={isSubmitting}
              hitSlop={8}
            >
              <Text style={styles.approveButtonText}>
                {isSubmitting ? "Submitting..." : "Submit Grade"}
              </Text>
            </Pressable>
          )}
        </View>
      );
    }

    // Default failed state with fallback action buttons
    return (
      <View style={styles.card}>
        <Text style={styles.errorTitle}>Couldn't analyze this one</Text>
        {error ? <Text style={styles.errorDetail}>{error}</Text> : null}
        {(onRetakePhoto || onGradeManually) ? (
          <View style={styles.failedActions}>
            {onRetakePhoto ? (
              <Pressable
                onPress={onRetakePhoto}
                accessibilityRole="button"
                accessibilityLabel="Retake Photo"
                style={styles.retakeButton}
                hitSlop={8}
              >
                <Text style={styles.retakeButtonText}>Retake Photo</Text>
              </Pressable>
            ) : null}
            {onGradeManually ? (
              <Pressable
                onPress={onGradeManually}
                accessibilityRole="button"
                accessibilityLabel="Grade Manually"
                style={styles.gradeManuallyButton}
                hitSlop={8}
              >
                <Text style={styles.gradeManuallyButtonText}>Grade Manually</Text>
              </Pressable>
            ) : null}
          </View>
        ) : null}
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
  const showConfidenceNote = confidence_level === "medium" || confidence_level === "low";

  const hasReviewControls = reviewControls != null;

  return (
    <View style={styles.card}>
      <View style={styles.resultRow}>
        {photoUri ? (
          <Image source={{ uri: photoUri }} style={styles.thumbnail} />
        ) : (
          <View style={[styles.thumbnail, styles.thumbnailPlaceholder]} />
        )}
        <View style={styles.scoreColumn}>
          {hasReviewControls ? (
            <View style={styles.scoreEditRow}>
              <Pressable
                onPress={reviewControls.decrement}
                accessibilityRole="button"
                accessibilityLabel="Decrease score"
                style={styles.scoreButton}
                hitSlop={8}
              >
                <Text style={styles.scoreButtonText}>−</Text>
              </Pressable>
              <TextInput
                style={styles.scoreInput}
                value={reviewControls.scoreInputText}
                onChangeText={reviewControls.setScore}
                keyboardType="number-pad"
                maxLength={3}
                accessibilityLabel="Score value"
                accessibilityHint="Enter a score between 0 and 100"
                accessibilityValue={{ min: 0, max: 100, now: reviewControls.scoreValue }}
              />
              <Text style={styles.scoreDivider}>/100</Text>
              <Pressable
                onPress={reviewControls.increment}
                accessibilityRole="button"
                accessibilityLabel="Increase score"
                style={styles.scoreButton}
                hitSlop={8}
              >
                <Text style={styles.scoreButtonText}>+</Text>
              </Pressable>
            </View>
          ) : (
            <Text style={styles.scoreText}>{proposed_score}</Text>
          )}
          <View style={[styles.confidenceBadge, { backgroundColor: confidenceColor }]}>
            <Text style={styles.confidenceBadgeText}>{confidenceLabel}</Text>
          </View>
          {showConfidenceNote ? (
            <Text style={styles.confidenceNote}>
              AI is less certain about this one — please review carefully
            </Text>
          ) : null}
        </View>
      </View>

      {hasReviewControls ? (
        <View style={styles.feedbackEditBlock}>
          <TextInput
            style={styles.feedbackInput}
            value={reviewControls.feedbackValue}
            onChangeText={reviewControls.setFeedback}
            multiline
            accessibilityLabel="Feedback text"
            accessibilityHint="Edit feedback for this assignment"
          />
          <Pressable
            onPress={reviewControls.undoFeedback}
            accessibilityRole="button"
            accessibilityLabel="Undo feedback to AI original"
            style={styles.undoButton}
            hitSlop={8}
          >
            <Text style={styles.undoButtonText}>Undo to AI draft</Text>
          </Pressable>
        </View>
      ) : (
        <Text style={styles.feedbackText}>{draft_feedback}</Text>
      )}

      {reviewControls != null && approvalControls != null ? (
        <View style={styles.approvalBlock}>
          {approvalControls.isApproved ? (
            <Animated.Text style={[styles.approvedText, { opacity: shouldAnimate ? approvedFadeAnim : 1 }]}>
              Approved ✓
            </Animated.Text>
          ) : (
            <Pressable
              onPress={approvalControls.approve}
              accessibilityRole="button"
              accessibilityLabel="Approve grade"
              accessibilityState={{ disabled: approvalControls.isApproving }}
              style={[styles.approveButton, approvalControls.isApproving && styles.approveButtonDisabled]}
              disabled={approvalControls.isApproving}
              hitSlop={8}
            >
              <Text style={styles.approveButtonText}>
                {approvalControls.isApproving ? "Approving..." : "Approve"}
              </Text>
            </Pressable>
          )}
          {approvalControls.approvalError ? (
            <Text style={styles.approvalErrorText}>{approvalControls.approvalError}</Text>
          ) : null}
        </View>
      ) : null}

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
  scoreEditRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  scoreButton: {
    width: 44,
    height: 44,
    borderRadius: radii.sm,
    backgroundColor: colors.surfaceSecondary,
    alignItems: "center",
    justifyContent: "center",
  },
  scoreButtonText: {
    fontSize: 22,
    fontFamily: fonts.body,
    fontWeight: fontWeights.semibold,
    color: colors.textPrimary,
    lineHeight: 26,
  },
  scoreInput: {
    fontSize: 24,
    fontFamily: fonts.heading,
    fontWeight: fontWeights.bold,
    color: colors.textPrimary,
    minWidth: 48,
    textAlign: "center",
    borderBottomWidth: 1,
    borderBottomColor: colors.borderFocus,
    paddingVertical: 2,
  },
  scoreDivider: {
    fontSize: 16,
    fontFamily: fonts.body,
    color: colors.textSecondary,
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
  confidenceNote: {
    fontSize: 12,
    fontFamily: fonts.body,
    color: colors.textSecondary,
    fontStyle: "italic",
  },
  feedbackText: {
    fontSize: 15,
    fontFamily: fonts.body,
    color: colors.textSecondary,
    lineHeight: 22,
  },
  feedbackEditBlock: {
    gap: 6,
  },
  feedbackInput: {
    fontSize: 15,
    fontFamily: fonts.body,
    color: colors.textSecondary,
    lineHeight: 22,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.sm,
    padding: 8,
    minHeight: 80,
    textAlignVertical: "top",
  },
  undoButton: {
    alignSelf: "flex-end",
    paddingVertical: 6,
    paddingHorizontal: 12,
    minHeight: 44,
    justifyContent: "center",
  },
  undoButtonText: {
    fontSize: 13,
    fontFamily: fonts.body,
    fontWeight: fontWeights.medium,
    color: colors.primary,
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
  approvalBlock: {
    gap: 8,
  },
  approveButton: {
    backgroundColor: colors.primary,
    minHeight: 44,
    borderRadius: radii.sm,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 16,
  },
  approveButtonDisabled: {
    opacity: 0.6,
  },
  approveButtonText: {
    fontSize: 16,
    fontFamily: fonts.body,
    fontWeight: fontWeights.semibold,
    color: colors.textInverse,
  },
  approvedText: {
    fontSize: 16,
    fontFamily: fonts.body,
    fontWeight: fontWeights.semibold,
    color: colors.success,
    textAlign: "center",
    paddingVertical: 8,
  },
  approvalErrorText: {
    fontSize: 13,
    fontFamily: fonts.body,
    color: colors.error,
  },
  processingHint: {
    fontSize: 13,
    fontFamily: fonts.body,
    color: colors.textSecondary,
    textAlign: "center",
    fontStyle: "italic",
  },
  failedActions: {
    flexDirection: "row",
    gap: 12,
    marginTop: 4,
  },
  retakeButton: {
    flex: 1,
    minHeight: 44,
    borderRadius: radii.sm,
    borderWidth: 1,
    borderColor: colors.primary,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 12,
  },
  retakeButtonText: {
    fontSize: 15,
    fontFamily: fonts.body,
    fontWeight: fontWeights.medium,
    color: colors.primary,
  },
  gradeManuallyButton: {
    flex: 1,
    minHeight: 44,
    borderRadius: radii.sm,
    backgroundColor: colors.primary,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 12,
  },
  gradeManuallyButtonText: {
    fontSize: 15,
    fontFamily: fonts.body,
    fontWeight: fontWeights.semibold,
    color: colors.textInverse,
  },
  manualHeading: {
    fontSize: 17,
    fontFamily: fonts.heading,
    fontWeight: fontWeights.semibold,
    color: colors.textPrimary,
    textAlign: "center",
  },
  submitButton: {
    backgroundColor: colors.primary,
    minHeight: 44,
    borderRadius: radii.sm,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 16,
  },
  submittedText: {
    fontSize: 16,
    fontFamily: fonts.body,
    fontWeight: fontWeights.semibold,
    color: colors.success,
    textAlign: "center",
    paddingVertical: 8,
  },
});
