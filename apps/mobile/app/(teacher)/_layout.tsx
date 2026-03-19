import { Tabs } from "expo-router";
import { colors, layout } from "@ilm/design-tokens";

/**
 * Teacher tab layout — 5 tabs + camera FAB (FAB added in Story 4.4).
 * Tab bar: 56px height + safe area, primary active icon, text-secondary inactive, caption labels.
 */
export default function TeacherLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textSecondary,
        tabBarStyle: { height: layout.tabBarHeight },
        headerShown: false,
      }}
    >
      <Tabs.Screen name="index" options={{ title: "Home" }} />
      <Tabs.Screen name="grade" options={{ title: "Grade" }} />
      <Tabs.Screen name="plan" options={{ title: "Plan" }} />
      <Tabs.Screen name="messages" options={{ title: "Messages" }} />
      <Tabs.Screen name="settings" options={{ title: "More" }} />
    </Tabs>
  );
}
