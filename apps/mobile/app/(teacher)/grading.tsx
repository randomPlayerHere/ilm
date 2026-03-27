import { useEffect, useRef, useState } from "react";
import { Platform, Pressable, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useLocalSearchParams, useRouter } from "expo-router";
import * as Haptics from "expo-haptics";
import { colors, fonts, fontWeights } from "@ilm/design-tokens";
import { GradingCard } from "../../src/features/grading/components/GradingCard";
import { useGradingJob } from "../../src/features/grading/hooks/useGradingJob";
import { useGradingReview } from "../../src/features/grading/hooks/useGradingReview";
import { useGradeApproval } from "../../src/features/grading/hooks/useGradeApproval";
import { useManualGrading } from "../../src/features/grading/hooks/useManualGrading";

export default function GradingScreen() {
  const router = useRouter();
  const { classId, studentId, batchIndex, batchTotal, assignmentId } = useLocalSearchParams<{
    classId?: string;
    studentId?: string;
    batchIndex?: string;
    batchTotal?: string;
    assignmentId?: string;
  }>();

  const startedAtRef = useRef(Date.now());

  // Hook must be called unconditionally — pass empty strings if params missing;
  // missingParams overrides the display status below so no bad request is acted on.
  const { status: hookStatus, result, error: hookError, photoUri, retrying } = useGradingJob(
    classId ?? '',
    studentId ?? '',
    assignmentId,
  );

  const missingParams = !classId || !studentId;
  const status = missingParams
    ? ('failed' as const)
    : hookStatus === 'idle'
      ? ('uploading' as const)
      : hookStatus;
  const error = missingParams ? 'Missing assignment context — please try again.' : hookError;

  // Review controls are only active when grading is completed and result is available
  const reviewControls = useGradingReview(
    status === 'completed' && result?.result != null ? result : null,
  );

  // Approval controls compose on top of review controls
  const approvalControls = useGradeApproval(
    status === 'completed' && result?.result != null ? result : null,
    reviewControls,
  );

  // Processing hint for retry indicator
  const processingHint = status === 'processing' && retrying ? 'Still processing...' : null;

  // Manual grading hook — only active when failed and result is available
  const manualGradingControls = useManualGrading(
    status === 'failed' && result != null ? result : null,
  );

  const [isManualGrading, setIsManualGrading] = useState(false);

  // Reset isManualGrading when job changes (e.g. after retake)
  useEffect(() => {
    setIsManualGrading(false);
  }, [result?.job_id]);

  function handleGradeManually() {
    setIsManualGrading(true);
  }

  function handleRetakePhoto() {
    router.replace({
      pathname: '/(teacher)/camera',
      params: { classId: classId ?? '', studentId: studentId ?? '', assignmentId: result?.assignment_id ?? '' },
    });
  }

  const [batchComplete, setBatchComplete] = useState(false);
  const [approvedScores, setApprovedScores] = useState<number[]>([]);

  // Keep a ref of the latest score so the approval effect never reads a stale value.
  // Updated unconditionally every render (no useEffect needed — synchronous assignment).
  const scoreValueRef = useRef(reviewControls?.scoreValue ?? 0);
  scoreValueRef.current = reviewControls?.scoreValue ?? 0;

  // Track previous isApproved to detect false→true transitions only
  const prevIsApprovedRef = useRef(false);
  useEffect(() => {
    prevIsApprovedRef.current = result?.is_approved ?? false;
  }, [result?.job_id]); // reset baseline when a new job loads

  useEffect(() => {
    const isNowApproved = approvalControls?.isApproved ?? false;
    if (!isNowApproved || prevIsApprovedRef.current) return; // only fire on false→true
    prevIsApprovedRef.current = true;

    if (Platform.OS !== "web") {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    }

    // scoreValueRef.current always reflects the latest reviewControls.scoreValue
    setApprovedScores((prev) => [...prev, scoreValueRef.current]);

    const parsedIndex = parseInt(batchIndex ?? '', 10);
    const parsedTotal = parseInt(batchTotal ?? '', 10);

    if (
      batchTotal !== undefined &&
      !isNaN(parsedIndex) &&
      !isNaN(parsedTotal) &&
      parsedTotal > 0 &&
      parsedIndex >= parsedTotal
    ) {
      setBatchComplete(true);
    } else {
      const timer = setTimeout(() => {
        router.back();
      }, 600);
      return () => clearTimeout(timer);
    }
  // Intentional dep array: effect must only fire on isApproved transitions.
  // Excluded stable values: batchIndex/batchTotal are URL params (constant for screen lifetime);
  // router is a stable ref from useRouter; scoreValue is read via scoreValueRef (no stale risk).
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [approvalControls?.isApproved]);

  if (batchComplete) {
    const parsedTotalForDisplay = parseInt(batchTotal ?? '', 10);
    const totalApproved = !isNaN(parsedTotalForDisplay) && parsedTotalForDisplay > 0
      ? parsedTotalForDisplay
      : approvedScores.length;
    const averageScore = approvedScores.length > 0
      ? Math.round(approvedScores.reduce((sum, s) => sum + s, 0) / approvedScores.length)
      : 0;
    const elapsedMinutes = Math.round((Date.now() - startedAtRef.current) / 60000);

    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.celebrationContent}>
          <Text style={styles.celebrationHeading}>All caught up! 🎉</Text>
          <Text style={styles.celebrationStat}>{totalApproved} grades approved</Text>
          <Text style={styles.celebrationStat}>Average: {averageScore}/100</Text>
          <Text style={styles.celebrationStat}>Time: {elapsedMinutes}m</Text>
          <Pressable
            onPress={() => router.back()}
            accessibilityRole="button"
            style={styles.doneButton}
          >
            <Text style={styles.doneButtonText}>Done</Text>
          </Pressable>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {batchTotal && batchIndex ? (
        <View style={styles.batchHeader}>
          <Text style={styles.batchText}>
            {batchIndex} of {batchTotal} graded
          </Text>
        </View>
      ) : null}

      <View style={styles.content}>
        <GradingCard
          status={status}
          result={result}
          photoUri={photoUri}
          error={error}
          reviewControls={reviewControls}
          approvalControls={approvalControls}
          processingHint={processingHint}
          onRetakePhoto={status === 'failed' && !isManualGrading ? handleRetakePhoto : undefined}
          onGradeManually={status === 'failed' && !isManualGrading ? handleGradeManually : undefined}
          manualGradingControls={isManualGrading ? manualGradingControls : null}
        />
      </View>

      <View style={styles.footer}>
        <Pressable
          onPress={() => router.back()}
          accessibilityRole="button"
          style={styles.doneButton}
        >
          <Text style={styles.doneButtonText}>Done</Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  batchHeader: {
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 4,
    alignItems: "center",
  },
  batchText: {
    fontSize: 13,
    fontFamily: fonts.body,
    fontWeight: fontWeights.medium,
    color: colors.textSecondary,
  },
  content: {
    flex: 1,
    padding: 20,
  },
  footer: {
    padding: 20,
    paddingBottom: 8,
  },
  doneButton: {
    backgroundColor: colors.primary,
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: "center",
  },
  doneButtonText: {
    color: colors.textInverse,
    fontSize: 16,
    fontFamily: fonts.body,
    fontWeight: fontWeights.semibold,
  },
  celebrationContent: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 32,
    gap: 16,
  },
  celebrationHeading: {
    fontSize: 28,
    fontFamily: fonts.heading,
    fontWeight: fontWeights.bold,
    color: colors.gold,
    textAlign: "center",
  },
  celebrationStat: {
    fontSize: 16,
    fontFamily: fonts.body,
    color: colors.textPrimary,
    textAlign: "center",
  },
});
