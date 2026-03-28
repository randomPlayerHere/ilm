import { Pressable, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useLocalSearchParams, useRouter } from "expo-router";
import { colors, fonts, fontWeights } from "@ilm/design-tokens";
import { GradingCard } from "../../src/features/grading/components/GradingCard";
import { useGradingJob } from "../../src/features/grading/hooks/useGradingJob";
import { useGradingReview } from "../../src/features/grading/hooks/useGradingReview";

export default function GradingScreen() {
  const router = useRouter();
  const { classId, studentId, batchIndex, batchTotal } = useLocalSearchParams<{
    classId?: string;
    studentId?: string;
    batchIndex?: string;
    batchTotal?: string;
  }>();

  // Hook must be called unconditionally — pass empty strings if params missing;
  // missingParams overrides the display status below so no bad request is acted on.
  const { status: hookStatus, result, error: hookError, photoUri } = useGradingJob(
    classId ?? '',
    studentId ?? '',
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
});
