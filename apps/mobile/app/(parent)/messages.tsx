import { YStack, Text } from "tamagui";
import { SafeAreaView } from "react-native-safe-area-context";
import { SkeletonLoader } from "@ilm/ui";
import { colors } from "@ilm/design-tokens";
import { useReducedMotionContext } from "../../src/contexts/ReducedMotionContext";

export default function ParentMessages() {
  const reducedMotion = useReducedMotionContext();
  const skeletonAnimation = reducedMotion ? null : undefined;

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.background }} edges={["top"]}>
      <YStack flex={1} padding="$lg" gap="$lg" backgroundColor={colors.background}>
        <Text fontSize={32} fontWeight="700" color="$textPrimary">Messages</Text>
        <SkeletonLoader variant="card" animation={skeletonAnimation} />
        <SkeletonLoader variant="card" animation={skeletonAnimation} />
        <SkeletonLoader variant="line" animation={skeletonAnimation} />
      </YStack>
    </SafeAreaView>
  );
}
