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
import { usePracticeRecommendations } from "../../src/features/grading/hooks/usePracticeRecommendations";
import { useOfflineQueueProcessor } from "../../src/features/grading/hooks/useOfflineQueueProcessor";
import { onQueueJobComplete } from "../../src/services/queue-events";
import { useNetworkStatus } from "../../src/hooks/useNetworkStatus";

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
  const { status: hookStatus, result, error: hookError, photoUri, retrying, queueItemId } = useGradingJob(
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

  // Offline queue processor — manages auto-upload of queued photos on reconnect
  const { pendingCount, queueItems, retryItem } = useOfflineQueueProcessor();

  // Live connectivity state — drives the offline indicator banner
  const { isConnected } = useNetworkStatus();

  // Determine if the current queued item has permanently failed (3+ attempts)
  const currentQueueItem = queueItemId ? queueItems.find((i) => i.id === queueItemId) : null;
  const uploadPermanentlyFailed =
    currentQueueItem?.status === "failed" && (currentQueueItem?.attemptCount ?? 0) >= 3;

  // When a queued item's job is submitted successfully, navigate back to the student list.
  // The AI grading job continues on the server; results arrive via server-sent push notifications.
  // In-app polling is not resumed here because useGradingJob requires a fresh pendingCapture to
  // initialise — there is no resume-by-jobId path yet. Resuming polling from an offline upload
  // is a future enhancement; for MVP the teacher is notified via push when the result is ready.
  useEffect(() => {
    if (status !== "queued-offline") return;
    const unsubscribe = onQueueJobComplete(() => {
      router.back();
    });
    return unsubscribe;
  }, [status, router]);

  // Review controls are only active when grading is completed and result is available
  const reviewControls = useGradingReview(
    status === 'completed' && result?.result != null ? result : null,
  );

  // Practice recommendations hook — only active in completed state
  const practiceRecommendationsControls = usePracticeRecommendations(
    status === 'completed' && result?.result != null ? result : null,
  );

  // Approval controls compose on top of review controls and practice recommendations
  const approvalControls = useGradeApproval(
    status === 'completed' && result?.result != null ? result : null,
    reviewControls,
    practiceRecommendationsControls,
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
      {isConnected === false ? (
        <View style={styles.offlineIndicatorBanner}>
          <Text style={styles.offlineIndicatorText}>No internet connection</Text>
        </View>
      ) : null}
      {pendingCount > 0 ? (
        <View style={styles.pendingBanner}>
          <Text style={styles.pendingBannerText}>
            {pendingCount} {pendingCount === 1 ? "photo" : "photos"} pending upload
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
          onRetryOfflineUpload={
            status === 'queued-offline' && uploadPermanentlyFailed && queueItemId
              ? () => retryItem(queueItemId)
              : undefined
          }
          manualGradingControls={isManualGrading ? manualGradingControls : null}
          practiceRecommendationsControls={status === 'completed' ? practiceRecommendationsControls : null}
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
  offlineIndicatorBanner: {
    marginHorizontal: 20,
    marginTop: 4,
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: colors.error,
    borderRadius: 8,
    alignItems: "center",
  },
  offlineIndicatorText: {
    fontSize: 12,
    fontFamily: fonts.body,
    fontWeight: fontWeights.medium,
    color: colors.textInverse,
  },
  pendingBanner: {
    marginHorizontal: 20,
    marginTop: 4,
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: colors.surfaceSecondary,
    borderRadius: 8,
    alignItems: "center",
  },
  pendingBannerText: {
    fontSize: 12,
    fontFamily: fonts.body,
    fontWeight: fontWeights.medium,
    color: colors.confidenceMedium,
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
