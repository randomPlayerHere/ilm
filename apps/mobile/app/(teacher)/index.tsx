import { useCallback, useEffect, useState } from "react";
import { FlatList } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { router } from "expo-router";
import * as Haptics from "expo-haptics";
import { YStack, XStack, Text, Button, Sheet, Input, Spinner } from "tamagui";
import type { ClassResponse, ClassCreateRequest } from "@ilm/contracts";
import { colors, spacing, fontSizes, fontWeights } from "@ilm/design-tokens";
import { useAuth } from "../../src/contexts/AuthContext";
import { listClasses, createClass } from "../../src/services/onboarding-service";

export default function TeacherHome() {
  const { token } = useAuth();
  const [classes, setClasses] = useState<ClassResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [newSubject, setNewSubject] = useState("");
  const [createError, setCreateError] = useState<string | null>(null);

  const fetchClasses = useCallback(async () => {
    if (!token) return;
    try {
      setError(null);
      const result = await listClasses(token);
      setClasses(result.classes);
    } catch {
      setError("Failed to load classes. Pull to refresh.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchClasses();
  }, [fetchClasses]);

  const handleCreateClass = async () => {
    if (!token || !newName.trim() || !newSubject.trim()) return;
    setCreating(true);
    setCreateError(null);
    try {
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      const created = await createClass(token, { name: newName.trim(), subject: newSubject.trim() });
      setClasses((prev) => [created, ...prev]);
      setSheetOpen(false);
      setNewName("");
      setNewSubject("");
    } catch {
      setCreateError("Failed to create class. Please try again.");
    } finally {
      setCreating(false);
    }
  };

  const renderClass = ({ item }: { item: ClassResponse }) => (
    <XStack
      backgroundColor={colors.surface}
      borderRadius={12}
      padding={spacing.md}
      marginBottom={spacing.sm}
      borderWidth={1}
      borderColor={colors.border}
      pressStyle={{ backgroundColor: colors.surfaceSecondary }}
      onPress={() => router.push({ pathname: "/(teacher)/class/[classId]", params: { classId: item.class_id } })}
    >
      <YStack flex={1} gap={4}>
        <Text fontSize={fontSizes.lg} fontWeight={fontWeights.bold} color={colors.textPrimary}>
          {item.name}
        </Text>
        <Text fontSize={fontSizes.sm} color={colors.textTertiary}>
          {item.subject}
        </Text>
        <XStack gap={spacing.sm} marginTop={4}>
          <Text fontSize={fontSizes.sm} color={colors.textTertiary}>
            {item.student_count} {item.student_count === 1 ? "student" : "students"}
          </Text>
          <Text fontSize={fontSizes.sm} color={colors.primary} fontFamily="$mono">
            Code: {item.join_code}
          </Text>
        </XStack>
      </YStack>
    </XStack>
  );

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.background }} edges={["top"]}>
      <YStack flex={1} padding={spacing.lg} gap={spacing.lg} backgroundColor={colors.background}>
        <XStack justifyContent="space-between" alignItems="center">
          <Text fontSize={32} fontWeight="700" color={colors.textPrimary}>
            My Classes
          </Text>
          <Button
            size="$3"
            backgroundColor={colors.primary}
            color="#fff"
            onPress={() => setSheetOpen(true)}
            accessibilityLabel="Create new class"
          >
            + New Class
          </Button>
        </XStack>

        {loading ? (
          <YStack flex={1} alignItems="center" justifyContent="center">
            <Spinner size="large" color={colors.primary} />
          </YStack>
        ) : error ? (
          <YStack flex={1} alignItems="center" justifyContent="center" gap={spacing.md}>
            <Text color={colors.error ?? colors.textTertiary} textAlign="center">{error}</Text>
            <Button onPress={fetchClasses}>Retry</Button>
          </YStack>
        ) : (
          <FlatList
            data={classes}
            keyExtractor={(item) => item.class_id}
            renderItem={renderClass}
            ListEmptyComponent={
              <YStack alignItems="center" justifyContent="center" paddingTop={spacing.lg}>
                <Text color={colors.textTertiary} textAlign="center">
                  No classes yet.{"\n"}Tap "+ New Class" to create your first class.
                </Text>
              </YStack>
            }
            showsVerticalScrollIndicator={false}
          />
        )}
      </YStack>

      <Sheet
        open={sheetOpen}
        onOpenChange={setSheetOpen}
        snapPoints={[50]}
        dismissOnSnapToBottom
      >
        <Sheet.Overlay />
        <Sheet.Frame backgroundColor={colors.surface} padding={spacing.lg}>
          <Sheet.Handle />
          <YStack gap={spacing.md} paddingTop={spacing.md}>
            <Text fontSize={fontSizes.lg} fontWeight={fontWeights.bold} color={colors.textPrimary}>
              Create Class
            </Text>
            <Input
              placeholder="Class name (e.g. Math Period 3)"
              value={newName}
              onChangeText={setNewName}
              borderColor={colors.border}
              backgroundColor={colors.surface}
            />
            <Input
              placeholder="Subject (e.g. Mathematics)"
              value={newSubject}
              onChangeText={setNewSubject}
              borderColor={colors.border}
              backgroundColor={colors.surface}
            />
            {createError && (
              <Text color={colors.error ?? colors.textTertiary} fontSize={fontSizes.sm}>
                {createError}
              </Text>
            )}
            <Button
              backgroundColor={colors.primary}
              color="#fff"
              disabled={creating || !newName.trim() || !newSubject.trim()}
              onPress={handleCreateClass}
              accessibilityLabel="Create class"
            >
              {creating ? <Spinner color="#fff" /> : "Create"}
            </Button>
          </YStack>
        </Sheet.Frame>
      </Sheet>
    </SafeAreaView>
  );
}
