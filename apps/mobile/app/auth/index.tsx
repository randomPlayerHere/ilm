import { View, Text } from "react-native";
import { colors, fontSizes, fontWeights, spacing } from "@ilm/design-tokens";

/** Auth screen placeholder — implemented in Stories 4.5/4.6 */
export default function AuthScreen() {
  return (
    <View style={{ flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: colors.background }}>
      <Text style={{ fontSize: fontSizes["2xl"], fontWeight: fontWeights.semibold, color: colors.primary }}>Teacher OS</Text>
      <Text style={{ fontSize: fontSizes.md, color: colors.textSecondary, marginTop: spacing.sm }}>Sign in to continue</Text>
    </View>
  );
}
