import { useState } from "react";
import { I18nManager, Platform, Pressable, StyleSheet } from "react-native";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { useRouter } from "expo-router";
import { colors, shadows, radii } from "@ilm/design-tokens";

interface CameraFabProps {
  bottomOffset: number;
  classId?: string;
  studentId?: string;
}

export function CameraFab({ bottomOffset, classId = "cls_demo_math_1", studentId = "stu_demo_1" }: CameraFabProps) {
  const [focused, setFocused] = useState(false);
  const router = useRouter();

  return (
    <Pressable
      onPress={() => {
        if (Platform.OS !== "web") Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
        router.push({ pathname: "/(teacher)/camera", params: { classId, studentId } });
      }}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      accessibilityLabel="Open camera for grading"
      accessibilityRole="button"
      style={({ pressed }) => [
        styles.fab,
        { bottom: bottomOffset },
        pressed && styles.fabPressed,
        focused && styles.fabFocused,
      ]}
    >
      <MaterialCommunityIcons name="camera" size={24} color={colors.textInverse} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  fab: {
    position: "absolute",
    ...(I18nManager.isRTL ? { left: 24 } : { right: 24 }),
    width: 56,
    height: 56,
    borderRadius: radii.full,
    backgroundColor: colors.primary,
    alignItems: "center",
    justifyContent: "center",
    ...shadows.md,
  },
  fabPressed: {
    backgroundColor: colors.primaryDark,
  },
  fabFocused: {
    borderWidth: 3,
    borderColor: colors.textPrimary,
  },
});
