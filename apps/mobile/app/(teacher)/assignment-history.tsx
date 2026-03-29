import { useCallback, useState } from "react";
import { FlatList, Pressable, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { router, useFocusEffect, useLocalSearchParams } from "expo-router";
import { Text } from "tamagui";
import { colors, fonts, fontWeights, spacing } from "@ilm/design-tokens";
import type { AssignmentSummaryResponse } from "@ilm/contracts";
import { useAuth } from "../../src/contexts/AuthContext";
import { listAssignments } from "../../src/services/grading-service";

export default function AssignmentHistoryScreen() {
  const { token } = useAuth();
  const { classId } = useLocalSearchParams<{ classId?: string }>();
  const [assignments, setAssignments] = useState<AssignmentSummaryResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAssignments = useCallback(async () => {
    if (!token || !classId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await listAssignments(classId, token);
      setAssignments(result.assignments);
    } catch {
      setError("Failed to load assignments. Pull to refresh.");
    } finally {
      setLoading(false);
    }
  }, [token, classId]);

  useFocusEffect(
    useCallback(() => {
      fetchAssignments();
    }, [fetchAssignments]),
  );

  const handleSelect = (assignment: AssignmentSummaryResponse) => {
    router.push({
      pathname: "/(teacher)/assignment-detail",
      params: { assignmentId: assignment.assignment_id, title: assignment.title },
    });
  };

  const renderItem = ({ item }: { item: AssignmentSummaryResponse }) => (
    <Pressable
      style={styles.card}
      onPress={() => handleSelect(item)}
      accessibilityRole="button"
      accessibilityLabel={`View ${item.title}`}
    >
      <View style={styles.cardContent}>
        <Text style={styles.title} numberOfLines={1}>{item.title}</Text>
        <Text style={styles.meta}>
          {new Date(item.created_at).toLocaleDateString()} · {item.artifact_count} photo
          {item.artifact_count !== 1 ? "s" : ""}
        </Text>
      </View>
      <Text style={styles.chevron}>›</Text>
    </Pressable>
  );

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backButton} accessibilityRole="button" accessibilityLabel="Go back">
          <Text style={styles.backText}>‹ Back</Text>
        </Pressable>
        <Text style={styles.heading}>Assignment History</Text>
      </View>

      {loading && (
        <View style={styles.center}>
          <Text style={styles.emptyText}>Loading…</Text>
        </View>
      )}

      {!loading && error && (
        <View style={styles.center}>
          <Text style={styles.errorText}>{error}</Text>
          <Pressable onPress={fetchAssignments} style={styles.retryButton}>
            <Text style={styles.retryText}>Retry</Text>
          </Pressable>
        </View>
      )}

      {!loading && !error && assignments.length === 0 && (
        <View style={styles.center}>
          <Text style={styles.emptyText}>No assignments yet.</Text>
        </View>
      )}

      {!loading && !error && assignments.length > 0 && (
        <FlatList
          data={assignments}
          keyExtractor={(item) => item.assignment_id}
          renderItem={renderItem}
          contentContainerStyle={styles.list}
        />
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
    fontSize: 28,
    color: colors.textPrimary,
  },
  list: {
    padding: spacing.lg,
    gap: spacing.sm,
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: spacing.md,
    marginBottom: spacing.sm,
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
    borderColor: colors.border,
  },
  cardContent: {
    flex: 1,
  },
  title: {
    fontFamily: fonts.body,
    fontWeight: fontWeights.semibold,
    fontSize: 16,
    color: colors.textPrimary,
    marginBottom: 4,
  },
  meta: {
    fontFamily: fonts.body,
    fontSize: 13,
    color: colors.textSecondary,
  },
  chevron: {
    fontSize: 22,
    color: colors.textSecondary,
    marginLeft: spacing.sm,
  },
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: spacing.xl,
  },
  emptyText: {
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
