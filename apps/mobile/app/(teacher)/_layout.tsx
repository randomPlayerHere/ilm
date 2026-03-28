import { View, Platform } from "react-native";
import { Tabs } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import * as Haptics from "expo-haptics";
import { colors, layout, shadows, fonts, fontWeights } from "@ilm/design-tokens";
import { getTabBarIcon } from "../../src/navigation/tab-icons";
import { CameraFab } from "../../src/components/CameraFab";
import { useReducedMotionContext } from "../../src/contexts/ReducedMotionContext";

export default function TeacherLayout() {
  const insets = useSafeAreaInsets();
  const reducedMotion = useReducedMotionContext();

  return (
    <View style={{ flex: 1, backgroundColor: colors.background }}>
      <Tabs
        screenOptions={{
          animation: reducedMotion ? "none" : "fade",
          tabBarActiveTintColor: colors.primary,
          tabBarInactiveTintColor: colors.textSecondary,
          tabBarStyle: {
            height: layout.tabBarHeight + insets.bottom,
            paddingBottom: insets.bottom,
            backgroundColor: colors.surface,
            borderTopWidth: 1,
            borderTopColor: colors.border,
            ...shadows.md,
          },
          tabBarLabelStyle: {
            fontSize: 12,
            fontFamily: fonts.body,
            fontWeight: fontWeights.medium,
          },
          headerShown: false,
        }}
        screenListeners={{
          tabPress: () => { if (Platform.OS !== "web") Haptics.selectionAsync(); },
        }}
      >
        <Tabs.Screen
          name="index"
          options={{ title: "Home", tabBarAccessibilityLabel: "Home tab", tabBarIcon: getTabBarIcon("teacher", "index") }}
        />
        <Tabs.Screen
          name="grade"
          options={{ title: "Grade", tabBarAccessibilityLabel: "Grade tab", tabBarIcon: getTabBarIcon("teacher", "grade") }}
        />
        <Tabs.Screen
          name="plan"
          options={{ title: "Plan", tabBarAccessibilityLabel: "Plan tab", tabBarIcon: getTabBarIcon("teacher", "plan") }}
        />
        <Tabs.Screen
          name="messages"
          options={{ title: "Messages", tabBarAccessibilityLabel: "Messages tab", tabBarIcon: getTabBarIcon("teacher", "messages") }}
        />
        <Tabs.Screen
          name="settings"
          options={{ title: "More", tabBarAccessibilityLabel: "More tab", tabBarIcon: getTabBarIcon("teacher", "settings") }}
        />
        <Tabs.Screen
          name="class"
          options={{ href: null }}
        />
        <Tabs.Screen
          name="camera"
          options={{ href: null }}
        />
        <Tabs.Screen
          name="grading"
          options={{ href: null }}
        />
      </Tabs>
      <CameraFab bottomOffset={layout.tabBarHeight + insets.bottom + 24} />
    </View>
  );
}
