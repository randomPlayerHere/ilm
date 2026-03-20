import { Tabs } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import * as Haptics from "expo-haptics";
import { colors, layout, shadows, fonts, fontWeights } from "@ilm/design-tokens";
import { getTabBarIcon } from "../../src/navigation/tab-icons";
import { useReducedMotionContext } from "../../src/contexts/ReducedMotionContext";

export default function ParentLayout() {
  const insets = useSafeAreaInsets();
  const reducedMotion = useReducedMotionContext();

  return (
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
        tabPress: () => Haptics.selectionAsync(),
      }}
    >
      <Tabs.Screen
        name="index"
        options={{ title: "Dashboard", tabBarAccessibilityLabel: "Dashboard tab", tabBarIcon: getTabBarIcon("parent", "index") }}
      />
      <Tabs.Screen
        name="progress"
        options={{ title: "Progress", tabBarAccessibilityLabel: "Progress tab", tabBarIcon: getTabBarIcon("parent", "progress") }}
      />
      <Tabs.Screen
        name="messages"
        options={{ title: "Messages", tabBarAccessibilityLabel: "Messages tab", tabBarIcon: getTabBarIcon("parent", "messages") }}
      />
      <Tabs.Screen
        name="settings"
        options={{ title: "Settings", tabBarAccessibilityLabel: "Settings tab", tabBarIcon: getTabBarIcon("parent", "settings") }}
      />
    </Tabs>
  );
}
