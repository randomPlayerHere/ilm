import { useEffect } from "react";
import { View, Text, Pressable, StyleSheet, Linking } from "react-native";
import { useRouter, useLocalSearchParams } from "expo-router";
import { useCameraPermissions } from "expo-camera";
import { SafeAreaView } from "react-native-safe-area-context";
import { colors, fonts, fontWeights } from "@ilm/design-tokens";
import { CameraCapture, CaptureResult } from "../../src/features/grading/components/CameraCapture";

export default function CameraScreen() {
  const router = useRouter();
  const [permission, requestPermission] = useCameraPermissions();
  const { classId = "cls_demo_math_1", studentId = "stu_demo_1", assignmentId = "" } =
    useLocalSearchParams<{ classId?: string; studentId?: string; assignmentId?: string }>();

  // Request permission on mount — permission is null while the OS dialog is pending
  useEffect(() => {
    requestPermission();
  }, []);

  function handleCaptureAccepted(_result: CaptureResult) {
    router.replace({
      pathname: "/(teacher)/grading",
      params: { classId, studentId, ...(assignmentId ? { assignmentId } : {}) },
    });
  }

  function handleDismiss() {
    router.back();
  }

  // null = permission dialog pending (loading state)
  if (!permission) {
    return <View style={styles.loading} />;
  }

  if (!permission.granted) {
    return (
      <SafeAreaView style={styles.denied}>
        <Text style={styles.deniedTitle}>Camera access required</Text>
        <Text style={styles.deniedBody}>
          Teacher OS needs camera access to photograph student assignments.
        </Text>
        <Pressable
          onPress={() => Linking.openSettings()}
          accessibilityRole="button"
          style={styles.settingsButton}
        >
          <Text style={styles.settingsButtonText}>Open Settings</Text>
        </Pressable>
        <Pressable
          onPress={handleDismiss}
          accessibilityRole="button"
          style={styles.cancelButton}
        >
          <Text style={styles.cancelButtonText}>Cancel</Text>
        </Pressable>
      </SafeAreaView>
    );
  }

  return (
    <CameraCapture
      onCaptureAccepted={handleCaptureAccepted}
      onDismiss={handleDismiss}
    />
  );
}

const styles = StyleSheet.create({
  loading: { flex: 1, backgroundColor: colors.textPrimary },
  denied: {
    flex: 1,
    backgroundColor: colors.background,
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
    gap: 16,
  },
  deniedTitle: {
    fontSize: 20,
    fontFamily: fonts.heading,
    fontWeight: fontWeights.bold,
    color: colors.textPrimary,
    textAlign: "center",
  },
  deniedBody: {
    fontSize: 15,
    fontFamily: fonts.body,
    color: colors.textSecondary,
    textAlign: "center",
  },
  settingsButton: {
    backgroundColor: colors.primary,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    minWidth: 160,
    alignItems: "center",
  },
  settingsButtonText: {
    color: colors.textInverse,
    fontSize: 15,
    fontFamily: fonts.body,
    fontWeight: fontWeights.semibold,
  },
  cancelButton: { padding: 12 },
  cancelButtonText: {
    color: colors.textSecondary,
    fontSize: 15,
    fontFamily: fonts.body,
  },
});
