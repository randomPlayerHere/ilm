import { useCallback, useEffect, useState } from "react";
import { FlatList, Alert } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useLocalSearchParams, router } from "expo-router";
import * as DocumentPicker from "expo-document-picker";
import * as Haptics from "expo-haptics";
import { YStack, XStack, Text, Button, Sheet, Input, Spinner } from "tamagui";
import type { StudentResponse, CsvImportResponse } from "@ilm/contracts";
import { colors, spacing, fontSizes, fontWeights } from "@ilm/design-tokens";
import { useAuth } from "../../../src/contexts/AuthContext";
import {
  getRoster,
  addStudent,
  removeStudent,
  importStudentsCsv,
} from "../../../src/services/onboarding-service";

export default function ClassRosterScreen() {
  const { classId, className } = useLocalSearchParams<{ classId: string; className?: string }>();
  const { token } = useAuth();

  const [students, setStudents] = useState<StudentResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Add student sheet
  const [addSheetOpen, setAddSheetOpen] = useState(false);
  const [addName, setAddName] = useState("");
  const [addGrade, setAddGrade] = useState("");
  const [adding, setAdding] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);

  // CSV import state
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<CsvImportResponse | null>(null);
  const [importSheetOpen, setImportSheetOpen] = useState(false);

  const fetchRoster = useCallback(async () => {
    if (!token || !classId) return;
    try {
      setError(null);
      const result = await getRoster(token, classId);
      setStudents(result.students);
    } catch {
      setError("Failed to load roster. Tap to retry.");
    } finally {
      setLoading(false);
    }
  }, [token, classId]);

  useEffect(() => {
    fetchRoster();
  }, [fetchRoster]);

  const handleAddStudent = async () => {
    if (!token || !classId || !addName.trim() || !addGrade.trim()) return;
    setAdding(true);
    setAddError(null);
    try {
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      const student = await addStudent(token, classId, {
        name: addName.trim(),
        grade_level: addGrade.trim(),
      });
      setStudents((prev) => [...prev, student]);
      setAddSheetOpen(false);
      setAddName("");
      setAddGrade("");
    } catch {
      setAddError("Failed to add student. Please try again.");
    } finally {
      setAdding(false);
    }
  };

  const handleRemoveStudent = (studentId: string, studentName: string) => {
    Alert.alert(
      "Remove Student",
      `Remove ${studentName} from this class?`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Remove",
          style: "destructive",
          onPress: async () => {
            if (!token || !classId) return;
            try {
              await removeStudent(token, classId, studentId);
              setStudents((prev) => prev.filter((s) => s.student_id !== studentId));
            } catch {
              Alert.alert("Error", "Failed to remove student. Please try again.");
            }
          },
        },
      ],
    );
  };

  const handleImportCsv = async () => {
    if (!token || !classId) return;
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ["text/csv", "text/comma-separated-values"],
        copyToCacheDirectory: true,
      });
      if (result.canceled) return;
      const file = result.assets[0];
      setImporting(true);
      const importRes = await importStudentsCsv(token, classId, file.uri, file.name);
      setImportResult(importRes);
      setImportSheetOpen(true);
      // Refresh roster to show newly imported students
      await fetchRoster();
    } catch {
      Alert.alert("Import Failed", "Could not import CSV. Please check the file format.");
    } finally {
      setImporting(false);
    }
  };

  const renderStudent = ({ item }: { item: StudentResponse }) => (
    <XStack
      alignItems="center"
      paddingVertical={spacing.sm}
      paddingHorizontal={spacing.md}
      borderBottomWidth={1}
      borderBottomColor={colors.border}
      backgroundColor={colors.surface}
    >
      <YStack flex={1}>
        <Text fontSize={fontSizes.md} color={colors.textPrimary} fontWeight={fontWeights.medium}>
          {item.name}
        </Text>
        <Text fontSize={fontSizes.sm} color={colors.textTertiary}>
          {item.grade_level}
        </Text>
      </YStack>
      <Button
        size="$2"
        backgroundColor="transparent"
        color={colors.error}
        onPress={() => handleRemoveStudent(item.student_id, item.name)}
        accessibilityLabel={`Remove ${item.name}`}
      >
        Remove
      </Button>
    </XStack>
  );

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.background }} edges={["top"]}>
      <YStack flex={1} backgroundColor={colors.background}>
        {/* Header */}
        <XStack
          alignItems="center"
          paddingHorizontal={spacing.lg}
          paddingVertical={spacing.md}
          borderBottomWidth={1}
          borderBottomColor={colors.border}
        >
          <Button
            size="$3"
            backgroundColor="transparent"
            onPress={() => router.back()}
            accessibilityLabel="Go back"
            marginRight={spacing.sm}
          >
            ← Back
          </Button>
          <Text flex={1} fontSize={fontSizes.xl} fontWeight={fontWeights.bold} color={colors.textPrimary}>
            {className ?? "Class Roster"}
          </Text>
        </XStack>

        {/* Action buttons */}
        <XStack
          padding={spacing.lg}
          gap={spacing.sm}
          borderBottomWidth={1}
          borderBottomColor={colors.border}
        >
          <Button
            flex={1}
            size="$3"
            backgroundColor={colors.primary}
            color="#fff"
            onPress={() => setAddSheetOpen(true)}
            accessibilityLabel="Add student manually"
          >
            Add Student
          </Button>
          <Button
            flex={1}
            size="$3"
            backgroundColor={colors.surfaceSecondary}
            color={colors.textPrimary}
            borderWidth={1}
            borderColor={colors.border}
            onPress={handleImportCsv}
            disabled={importing}
            accessibilityLabel="Import students from CSV"
          >
            {importing ? <Spinner size="small" color={colors.primary} /> : "Import CSV"}
          </Button>
        </XStack>

        {/* Roster list */}
        {loading ? (
          <YStack flex={1} alignItems="center" justifyContent="center">
            <Spinner size="large" color={colors.primary} />
          </YStack>
        ) : error ? (
          <YStack flex={1} alignItems="center" justifyContent="center" gap={spacing.md} padding={spacing.lg}>
            <Text color={colors.error} textAlign="center">{error}</Text>
            <Button onPress={fetchRoster}>Retry</Button>
          </YStack>
        ) : (
          <FlatList
            data={students}
            keyExtractor={(item) => item.student_id}
            renderItem={renderStudent}
            ListEmptyComponent={
              <YStack alignItems="center" justifyContent="center" paddingTop={spacing["2xl"]} paddingHorizontal={spacing.lg}>
                <Text color={colors.textTertiary} textAlign="center">
                  No students yet.{"\n"}Add your first student above.
                </Text>
              </YStack>
            }
            showsVerticalScrollIndicator={false}
          />
        )}
      </YStack>

      {/* Add Student Sheet */}
      <Sheet
        open={addSheetOpen}
        onOpenChange={setAddSheetOpen}
        snapPoints={[45]}
        dismissOnSnapToBottom
      >
        <Sheet.Overlay />
        <Sheet.Frame backgroundColor={colors.surface} padding={spacing.lg}>
          <Sheet.Handle />
          <YStack gap={spacing.md} paddingTop={spacing.md}>
            <Text fontSize={fontSizes.lg} fontWeight={fontWeights.bold} color={colors.textPrimary}>
              Add Student
            </Text>
            <Input
              placeholder="Student name (e.g. Jane Smith)"
              value={addName}
              onChangeText={setAddName}
              borderColor={colors.border}
              backgroundColor={colors.surface}
            />
            <Input
              placeholder="Grade level (e.g. Grade 5)"
              value={addGrade}
              onChangeText={setAddGrade}
              borderColor={colors.border}
              backgroundColor={colors.surface}
            />
            {addError && (
              <Text color={colors.error} fontSize={fontSizes.sm}>
                {addError}
              </Text>
            )}
            <Button
              backgroundColor={colors.primary}
              color="#fff"
              disabled={adding || !addName.trim() || !addGrade.trim()}
              onPress={handleAddStudent}
              accessibilityLabel="Confirm add student"
            >
              {adding ? <Spinner color="#fff" /> : "Add Student"}
            </Button>
          </YStack>
        </Sheet.Frame>
      </Sheet>

      {/* CSV Import Result Sheet */}
      <Sheet
        open={importSheetOpen}
        onOpenChange={setImportSheetOpen}
        snapPoints={[55]}
        dismissOnSnapToBottom
      >
        <Sheet.Overlay />
        <Sheet.Frame backgroundColor={colors.surface} padding={spacing.lg}>
          <Sheet.Handle />
          {importResult && (
            <YStack gap={spacing.md} paddingTop={spacing.md}>
              <Text fontSize={fontSizes.lg} fontWeight={fontWeights.bold} color={colors.textPrimary}>
                Import Summary
              </Text>
              <Text color={colors.success ?? colors.primary} fontSize={fontSizes.md}>
                ✅ {importResult.successful} student{importResult.successful !== 1 ? "s" : ""} imported successfully
              </Text>
              {importResult.failed > 0 && (
                <YStack gap={spacing.xs}>
                  <Text color={colors.error} fontSize={fontSizes.md}>
                    ⚠️ {importResult.failed} row{importResult.failed !== 1 ? "s" : ""} had errors:
                  </Text>
                  {importResult.results
                    .filter((r) => !r.success)
                    .map((r) => (
                      <Text key={r.row} fontSize={fontSizes.sm} color={colors.textTertiary}>
                        {"  "}Row {r.row}: {r.error}
                      </Text>
                    ))}
                </YStack>
              )}
              <Button
                backgroundColor={colors.primary}
                color="#fff"
                onPress={() => setImportSheetOpen(false)}
              >
                Done
              </Button>
            </YStack>
          )}
        </Sheet.Frame>
      </Sheet>
    </SafeAreaView>
  );
}
