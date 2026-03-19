import { Tabs } from "expo-router";
import { colors, layout } from "@ilm/design-tokens";

/**
 * Student tab layout — 4 tabs.
 */
export default function StudentLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textSecondary,
        tabBarStyle: { height: layout.tabBarHeight },
        headerShown: false,
      }}
    >
      <Tabs.Screen name="index" options={{ title: "Growth" }} />
      <Tabs.Screen name="progress" options={{ title: "Progress" }} />
      <Tabs.Screen name="tips" options={{ title: "Tips" }} />
      <Tabs.Screen name="settings" options={{ title: "Settings" }} />
    </Tabs>
  );
}
