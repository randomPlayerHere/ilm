import { useState } from "react";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { YStack, Text, Button, Input, Spinner } from "tamagui";
import { colors, spacing, fontSizes } from "@ilm/design-tokens";
import { useAuth } from "../../src/contexts/AuthContext";
import {
  joinClassByCode,
  InvalidJoinCodeError,
  AlreadyEnrolledError,
} from "../../src/services/onboarding-service";

export default function JoinClassScreen() {
  const { token } = useAuth();
  const router = useRouter();
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleJoin = async () => {
    if (!token || !code.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await joinClassByCode(token, code);
      router.replace("/(student)");
    } catch (err) {
      if (err instanceof InvalidJoinCodeError) {
        setError("Invalid or expired join code. Check with your teacher.");
      } else if (err instanceof AlreadyEnrolledError) {
        setError("You are already enrolled in this class.");
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.background }} edges={["top"]}>
      <YStack flex={1} padding={spacing.lg} gap={spacing.lg} backgroundColor={colors.background}>
        <Text fontSize={fontSizes.xl} fontWeight="700" color="$textPrimary">
          Join a Class
        </Text>
        <Text fontSize={fontSizes.md} color="$textSecondary">
          Enter the join code from your teacher
        </Text>
        <Input
          placeholder="e.g. A3BX9K"
          value={code}
          onChangeText={(text) => setCode(text.toUpperCase().trim())}
          autoCapitalize="characters"
          maxLength={6}
          fontSize={fontSizes.lg}
          letterSpacing={4}
          textAlign="center"
          borderColor={colors.border}
        />
        {error && (
          <Text color="$red10" fontSize={fontSizes.sm}>
            {error}
          </Text>
        )}
        <Button
          onPress={handleJoin}
          disabled={loading || !code.trim()}
          backgroundColor={colors.primary}
          icon={loading ? <Spinner /> : undefined}
          color="#fff"
        >
          {loading ? "Joining..." : "Join Class"}
        </Button>
        <Button variant="outlined" borderColor={colors.border} onPress={() => router.back()}>
          Cancel
        </Button>
      </YStack>
    </SafeAreaView>
  );
}
