import { View, Text } from "react-native";

/** Onboarding wizard placeholder — implemented in Story 4.9 */
export default function OnboardingScreen() {
  return (
    <View style={{ flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: "#FAFAF5" }}>
      <Text style={{ fontSize: 20, fontWeight: "600", color: "#2D6A4F" }}>Welcome</Text>
      <Text style={{ fontSize: 15, color: "#6B7280", marginTop: 8 }}>Onboarding flow coming soon</Text>
    </View>
  );
}
