import { YStack, Text, Button } from "tamagui";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { SkeletonLoader } from "@ilm/ui";
import { colors } from "@ilm/design-tokens";
import { useReducedMotionContext } from "../../src/contexts/ReducedMotionContext";

export default function StudentGrowth() {
  const reducedMotion = useReducedMotionContext();
  const router = useRouter();
  const skeletonAnimation = reducedMotion ? null : undefined;

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.background }} edges={["top"]}>
      <YStack flex={1} padding="$lg" gap="$lg" backgroundColor={colors.background}>
        <Text fontSize={32} fontWeight="700" color="$textPrimary">Growth</Text>
        <SkeletonLoader variant="card" animation={skeletonAnimation} />
        <SkeletonLoader variant="card" animation={skeletonAnimation} />
        <SkeletonLoader variant="line" animation={skeletonAnimation} />
        <Button
          variant="outlined"
          onPress={() => router.push("/(student)/join")}
          borderColor={colors.border}
        >
          Join a Class
        </Button>
      </YStack>
    </SafeAreaView>
  );
}
