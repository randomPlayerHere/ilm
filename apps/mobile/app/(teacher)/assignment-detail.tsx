import { useCallback, useEffect, useRef, useState } from "react";
import { Image, Pressable, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { router, useLocalSearchParams } from "expo-router";
import { Text } from "tamagui";
import { colors, fonts, fontWeights, spacing } from "@ilm/design-tokens";
import type { GradeApprovalResponse } from "@ilm/contracts";
import { useAuth } from "../../src/contexts/AuthContext";
import {
  getArtifactDownloadUrl,
  getArtifactGradingJob,
  getGradeApproval,
  getGradingJob,
  listArtifacts,
} from "../../src/services/grading-service";

interface ArtifactDetail {
  artifactId: string;
  downloadUrl: string | null;
  jobId: string | null;
  grade: string | null;
  feedback: string | null;
  rubricMapping: Record<string, string> | null;
  practiceRecommendations: string[];
  approvedAt: string | null;
}

export default function AssignmentDetailScreen() {
  const { token } = useAuth();
  const { assignmentId, title, artifactId, jobId } = useLocalSearchParams<{
    assignmentId?: string;
    title?: string;
    artifactId?: string;
    jobId?: string;
  }>();

  const [detail, setDetail] = useState<ArtifactDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const isMountedRef = useRef(true);

  const fetchDetail = useCallback(async () => {
    if (!token || !assignmentId) {
      setError("Missing assignment context.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      // Resolve artifactId — use param if provided, else fetch the first artifact for the assignment
      let resolvedArtifactId = artifactId;
      if (!resolvedArtifactId) {
        const artifacts = await listArtifacts(assignmentId, token);
        if (!isMountedRef.current) return;
        if (artifacts.length === 0) {
          setError("No photos found for this assignment.");
          setLoading(false);
          return;
        }
        resolvedArtifactId = artifacts[0].artifact_id;
      }

      // Resolve jobId — use param if provided, else look up via artifact
      let resolvedJobId = jobId;
      if (!resolvedJobId) {
        const jobViaArtifact = await getArtifactGradingJob(assignmentId, resolvedArtifactId, token).catch(() => null);
        if (!isMountedRef.current) return;
        resolvedJobId = jobViaArtifact?.job_id ?? undefined;
      }

      // Fetch download URL and grading job in parallel
      const [downloadResult, jobResult] = await Promise.all([
        getArtifactDownloadUrl(assignmentId, resolvedArtifactId, token),
        resolvedJobId
          ? getGradingJob(assignmentId, resolvedJobId, token).catch(() => null)
          : Promise.resolve(null),
      ]);
      if (!isMountedRef.current) return;

      // If approved, fetch the teacher's approved score and feedback (not the AI draft)
      let approvalResult: GradeApprovalResponse | null = null;
      if (jobResult?.is_approved && resolvedJobId) {
        approvalResult = await getGradeApproval(assignmentId, resolvedJobId, token).catch(() => null);
        if (!isMountedRef.current) return;
      }

      const grade = approvalResult?.approved_score ?? jobResult?.result?.proposed_score ?? null;
      const feedback = approvalResult?.approved_feedback ?? jobResult?.result?.draft_feedback ?? null;
      const rubricMapping = jobResult?.result?.rubric_mapping ?? null;
      const practiceRecommendations =
        approvalResult?.practice_recommendations ??
        jobResult?.result?.practice_recommendations ??
        [];

      setDetail({
        artifactId: resolvedArtifactId,
        downloadUrl: downloadResult.url,
        jobId: resolvedJobId ?? null,
        grade,
        feedback,
        rubricMapping,
        practiceRecommendations,
        approvedAt: approvalResult?.approved_at ?? jobResult?.completed_at ?? null,
      });
    } catch {
      if (isMountedRef.current) setError("Failed to load assignment details.");
    } finally {
      if (isMountedRef.current) setLoading(false);
    }
  }, [token, assignmentId, artifactId, jobId]);

  useEffect(() => {
    isMountedRef.current = true;
    fetchDetail();
    return () => { isMountedRef.current = false; };
  }, [fetchDetail]);

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backButton} accessibilityRole="button" accessibilityLabel="Go back">
          <Text style={styles.backText}>‹ Back</Text>
        </Pressable>
        <Text style={styles.heading} numberOfLines={2}>{title ?? "Assignment Detail"}</Text>
      </View>

      {loading && (
        <View style={styles.center}>
          <Text style={styles.secondaryText}>Loading…</Text>
        </View>
      )}

      {!loading && error && (
        <View style={styles.center}>
          <Text style={styles.errorText}>{error}</Text>
          <Pressable onPress={fetchDetail} style={styles.retryButton}>
            <Text style={styles.retryText}>Retry</Text>
          </Pressable>
        </View>
      )}

      {!loading && !error && detail && (
        <ScrollView contentContainerStyle={styles.scrollContent}>
          {/* Photo */}
          {detail.downloadUrl ? (
            <View style={styles.photoContainer}>
              <Image
                source={{ uri: detail.downloadUrl }}
                style={styles.photo}
                resizeMode="contain"
                accessibilityLabel="Assignment photo"
              />
            </View>
          ) : (
            <View style={[styles.photoContainer, styles.photoPlaceholder]}>
              <Text style={styles.secondaryText}>Photo unavailable</Text>
            </View>
          )}

          {/* Grade */}
          <View style={styles.section}>
            <Text style={styles.sectionLabel}>Grade</Text>
            <Text style={styles.sectionValue}>{detail.grade ?? "Not yet graded"}</Text>
          </View>

          {/* Feedback */}
          {detail.feedback && (
            <View style={styles.section}>
              <Text style={styles.sectionLabel}>Feedback</Text>
              <Text style={styles.sectionBody}>{detail.feedback}</Text>
            </View>
          )}

          {/* Rubric */}
          {detail.rubricMapping && Object.keys(detail.rubricMapping).length > 0 && (
            <View style={styles.section}>
              <Text style={styles.sectionLabel}>Rubric Scores</Text>
              {Object.entries(detail.rubricMapping).map(([criterion, score]) => (
                <View key={criterion} style={styles.rubricRow}>
                  <Text style={styles.rubricCriterion}>{criterion}</Text>
                  <Text style={styles.rubricScore}>{score}</Text>
                </View>
              ))}
            </View>
          )}

          {/* Practice Recommendations */}
          {detail.practiceRecommendations.length > 0 && (
            <View style={styles.section}>
              <Text style={styles.sectionLabel}>Practice Recommendations</Text>
              {detail.practiceRecommendations.map((rec, i) => (
                <View key={i} style={styles.recRow}>
                  <Text style={styles.recBullet}>•</Text>
                  <Text style={styles.recText}>{rec}</Text>
                </View>
              ))}
            </View>
          )}
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.md,
    paddingBottom: spacing.sm,
  },
  backButton: {
    marginBottom: spacing.xs,
  },
  backText: {
    fontFamily: fonts.body,
    fontWeight: fontWeights.medium,
    color: colors.primary,
    fontSize: 16,
  },
  heading: {
    fontFamily: fonts.heading,
    fontWeight: fontWeights.bold,
    fontSize: 24,
    color: colors.textPrimary,
  },
  scrollContent: {
    padding: spacing.lg,
    paddingBottom: spacing.xl,
  },
  photoContainer: {
    width: "100%",
    aspectRatio: 4 / 3,
    backgroundColor: colors.surface,
    borderRadius: 12,
    overflow: "hidden",
    marginBottom: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
  },
  photo: {
    width: "100%",
    height: "100%",
  },
  photoPlaceholder: {
    alignItems: "center",
    justifyContent: "center",
  },
  section: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: spacing.md,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  sectionLabel: {
    fontFamily: fonts.body,
    fontWeight: fontWeights.semibold,
    fontSize: 12,
    color: colors.textSecondary,
    textTransform: "uppercase",
    letterSpacing: 0.8,
    marginBottom: spacing.xs,
  },
  sectionValue: {
    fontFamily: fonts.body,
    fontWeight: fontWeights.bold,
    fontSize: 22,
    color: colors.textPrimary,
  },
  sectionBody: {
    fontFamily: fonts.body,
    fontSize: 15,
    color: colors.textPrimary,
    lineHeight: 22,
  },
  rubricRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 4,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  rubricCriterion: {
    fontFamily: fonts.body,
    fontSize: 14,
    color: colors.textPrimary,
    flex: 1,
  },
  rubricScore: {
    fontFamily: fonts.body,
    fontWeight: fontWeights.semibold,
    fontSize: 14,
    color: colors.textPrimary,
  },
  recRow: {
    flexDirection: "row",
    marginBottom: 6,
  },
  recBullet: {
    fontFamily: fonts.body,
    fontSize: 15,
    color: colors.primary,
    marginRight: 6,
    marginTop: 2,
  },
  recText: {
    fontFamily: fonts.body,
    fontSize: 14,
    color: colors.textPrimary,
    flex: 1,
    lineHeight: 20,
  },
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: spacing.xl,
  },
  secondaryText: {
    fontFamily: fonts.body,
    fontSize: 15,
    color: colors.textSecondary,
    textAlign: "center",
  },
  errorText: {
    fontFamily: fonts.body,
    fontSize: 15,
    color: colors.error ?? colors.textSecondary,
    textAlign: "center",
    marginBottom: spacing.md,
  },
  retryButton: {
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    backgroundColor: colors.primary,
    borderRadius: 8,
  },
  retryText: {
    fontFamily: fonts.body,
    fontWeight: fontWeights.semibold,
    color: "#fff",
    fontSize: 15,
  },
});
