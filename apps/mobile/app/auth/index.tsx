import { useState } from "react";
import { SafeAreaView } from "react-native-safe-area-context";
import { YStack, XStack, Text, Input, Button, Spinner } from "tamagui";
import { colors, fontSizes, fontWeights, spacing } from "@ilm/design-tokens";
import { useAuth } from "../../src/contexts/AuthContext";
import { NetworkError } from "../../src/services/api-client";
import {
  InvalidCredentialsError,
  InactiveAccountError,
  RateLimitError,
  NoOrgMembershipError,
  GoogleAuthFailedError,
  PlayServicesUnavailableError,
} from "../../src/services/auth-service";

export default function SignInScreen() {
  const { signIn, signInWithGoogle, sessionExpired, lastEmail } = useAuth();

  const [email, setEmail] = useState(lastEmail ?? "");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(
    sessionExpired ? "Your session has expired. Please sign in again." : null,
  );
  const [isNetworkError, setIsNetworkError] = useState(false);
  const [networkErrorSource, setNetworkErrorSource] = useState<"email" | "google" | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);

  const isBusy = isSubmitting || isGoogleLoading;

  async function handleSignIn() {
    if (!email.trim() || !password.trim()) {
      setError("Please enter your email and password.");
      return;
    }

    setError(null);
    setIsNetworkError(false);
    setNetworkErrorSource(null);
    setIsSubmitting(true);

    try {
      await signIn(email.trim(), password);
      // Navigation handled by AuthGuard in _layout.tsx
    } catch (err) {
      if (err instanceof NetworkError) {
        setError("Couldn't sign in. Check your connection and try again.");
        setIsNetworkError(true);
        setNetworkErrorSource("email");
      } else if (err instanceof InvalidCredentialsError) {
        setError("Email or password is incorrect.");
      } else if (err instanceof InactiveAccountError) {
        setError("Your account is not active. Contact your administrator.");
      } else if (err instanceof RateLimitError) {
        setError("Too many sign-in attempts. Please wait and try again.");
      } else {
        console.error("[SignIn] Unexpected error:", err);
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleGoogleSignIn() {
    setError(null);
    setIsNetworkError(false);
    setNetworkErrorSource(null);
    setIsGoogleLoading(true);

    try {
      await signInWithGoogle();
      // If signInWithGoogle returns without throwing, either:
      // - Authentication succeeded → AuthGuard in _layout.tsx handles navigation
      // - User cancelled → signInWithGoogle returns cleanly (no error, AC #3)
    } catch (err) {
      if (err instanceof NetworkError) {
        setError("Couldn't sign in. Check your connection and try again.");
        setIsNetworkError(true);
        setNetworkErrorSource("google");
      } else if (err instanceof NoOrgMembershipError) {
        setError("Your account is not authorized for any organization. Contact your administrator.");
      } else if (err instanceof GoogleAuthFailedError) {
        setError("Google sign-in failed. Please try again.");
      } else if (err instanceof PlayServicesUnavailableError) {
        setError("Google Play Services is not available. Please use email/password sign-in.");
      } else if (err instanceof RateLimitError) {
        setError("Too many sign-in attempts. Please wait and try again.");
      } else {
        console.error("[GoogleSignIn] Unexpected error:", err);
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setIsGoogleLoading(false);
    }
  }

  return (
    <SafeAreaView
      style={{ flex: 1, backgroundColor: colors.background }}
      edges={["top", "bottom"]}
    >
      <YStack
        flex={1}
        justifyContent="center"
        paddingHorizontal={spacing["2xl"]}
        gap={spacing["2xl"]}
        backgroundColor={colors.background}
      >
        {/* Header */}
        <YStack alignItems="center" gap={spacing.sm}>
          <Text
            fontSize={fontSizes["2xl"]}
            fontWeight={fontWeights.semibold}
            color={colors.primary}
          >
            Teacher OS
          </Text>
          <Text fontSize={fontSizes.md} color={colors.textSecondary}>
            Sign in to continue
          </Text>
        </YStack>

        {/* Form */}
        <YStack gap={spacing.md}>
          <Input
            value={email}
            onChangeText={setEmail}
            placeholder="Email address"
            placeholderTextColor={colors.textTertiary}
            keyboardType="email-address"
            autoCapitalize="none"
            autoComplete="email"
            editable={!isBusy}
            backgroundColor={colors.surfaceSecondary}
            borderColor={colors.border}
            borderWidth={1}
            borderRadius={8}
            fontSize={fontSizes.md}
            color={colors.textPrimary}
            height={48}
            paddingHorizontal={spacing.md}
          />

          <Input
            value={password}
            onChangeText={setPassword}
            placeholder="Password"
            placeholderTextColor={colors.textTertiary}
            secureTextEntry
            autoComplete="password"
            editable={!isBusy}
            backgroundColor={colors.surfaceSecondary}
            borderColor={colors.border}
            borderWidth={1}
            borderRadius={8}
            fontSize={fontSizes.md}
            color={colors.textPrimary}
            height={48}
            paddingHorizontal={spacing.md}
            onSubmitEditing={handleSignIn}
          />

          {/* Error message */}
          {error && (
            <YStack
              backgroundColor={colors.errorLight + "1A"}
              borderRadius={8}
              padding={spacing.md}
              gap={spacing.sm}
            >
              <Text fontSize={fontSizes.sm} color={colors.error}>
                {error}
              </Text>
              {isNetworkError && (
                <Button
                  onPress={networkErrorSource === "google" ? handleGoogleSignIn : handleSignIn}
                  disabled={isBusy}
                  backgroundColor="transparent"
                  borderWidth={1}
                  borderColor={colors.error}
                  borderRadius={8}
                  height={36}
                  alignSelf="flex-start"
                  paddingHorizontal={spacing.md}
                >
                  <Button.Text color={colors.error} fontSize={fontSizes.sm}>
                    Try Again
                  </Button.Text>
                </Button>
              )}
            </YStack>
          )}

          {/* Sign In button */}
          <Button
            onPress={handleSignIn}
            disabled={isBusy}
            backgroundColor={isSubmitting ? colors.primaryLight : colors.primary}
            pressStyle={{ backgroundColor: colors.primaryDark, scale: 0.97 }}
            borderRadius={8}
            height={48}
            marginTop={spacing.sm}
          >
            {isSubmitting ? (
              <Button.Text color={colors.textInverse} fontSize={fontSizes.md} fontWeight={fontWeights.semibold}>
                <Spinner size="small" color={colors.textInverse} /> Signing in...
              </Button.Text>
            ) : (
              <Button.Text color={colors.textInverse} fontSize={fontSizes.md} fontWeight={fontWeights.semibold}>
                Sign In
              </Button.Text>
            )}
          </Button>

          {/* Divider */}
          <XStack alignItems="center" gap={spacing.md} marginTop={spacing.sm}>
            <YStack flex={1} height={1} backgroundColor={colors.border} />
            <Text fontSize={fontSizes.sm} color={colors.textTertiary}>
              or
            </Text>
            <YStack flex={1} height={1} backgroundColor={colors.border} />
          </XStack>

          {/* Google Sign-In button */}
          <Button
            onPress={handleGoogleSignIn}
            disabled={isBusy}
            backgroundColor={colors.surface}
            borderWidth={1}
            borderColor={colors.border}
            pressStyle={{ backgroundColor: colors.surfaceSecondary, scale: 0.97 }}
            borderRadius={8}
            height={48}
          >
            {isGoogleLoading ? (
              <Button.Text color={colors.textPrimary} fontSize={fontSizes.md}>
                <Spinner size="small" color={colors.textPrimary} /> Signing in with Google...
              </Button.Text>
            ) : (
              <Button.Text color={colors.textPrimary} fontSize={fontSizes.md} fontWeight={fontWeights.medium}>
                Sign in with Google
              </Button.Text>
            )}
          </Button>
        </YStack>
      </YStack>
    </SafeAreaView>
  );
}
