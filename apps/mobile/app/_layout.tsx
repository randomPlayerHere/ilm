import { useEffect, useRef } from "react";
import { Alert, Linking } from "react-native";
import { Slot, useRouter, useSegments } from "expo-router";
import { TamaguiProvider } from "tamagui";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { tamaguiConfig } from "@ilm/design-tokens";
import { GoogleSignin } from "@react-native-google-signin/google-signin";
import Constants from "expo-constants";
import { ReducedMotionProvider } from "../src/contexts/ReducedMotionContext";
import { AuthProvider, useAuth } from "../src/contexts/AuthContext";
import {
  acceptInviteLink,
  AlreadyLinkedError,
  InviteLinkAlreadyUsedError,
  InviteLinkExpiredError,
} from "../src/services/invite-service";
import { isOnboardingComplete } from "../src/services/onboarding-wizard-state";

// Module-level pending token (survives navigation during auth flow)
let pendingInviteToken: string | null = null;

export function getPendingInviteToken(): string | null { return pendingInviteToken; }
export function clearPendingInviteToken(): void { pendingInviteToken = null; }

function AuthGuard() {
  const { isLoading, isAuthenticated, homePath, role, token, userId } = useAuth();
  const segments = useSegments();
  const router = useRouter();
  const initialUrlHandled = useRef(false);

  function showInviteError(error: unknown) {
    if (error instanceof InviteLinkAlreadyUsedError) {
      Alert.alert("Invite already used", "This invite link has already been used.");
      return;
    }
    if (error instanceof InviteLinkExpiredError) {
      Alert.alert("Invite expired", "This invite link has expired. Ask the teacher for a new one.");
      return;
    }
    if (error instanceof AlreadyLinkedError) {
      Alert.alert("Already linked", "This parent account is already linked to this student.");
      return;
    }
    Alert.alert("Invite unavailable", "This invite link is not valid right now.");
  }

  // Deep link listener
  useEffect(() => {
    function handleUrl({ url }: { url: string }) {
      const match = url.match(/^ilm:\/\/invite\/(.+)$/);
      if (!match) return;
      const inviteToken = match[1];
      if (isAuthenticated && role === "parent" && token) {
        acceptInviteLink(token, inviteToken)
          .then(() => router.replace("/(parent)"))
          .catch((error: unknown) => {
            showInviteError(error);
            router.replace("/(parent)");
          });
      } else {
        pendingInviteToken = inviteToken;
        router.replace("/auth");
      }
    }
    const sub = Linking.addEventListener("url", handleUrl);
    // Check initial URL only once (cold start via deep link)
    if (!initialUrlHandled.current) {
      initialUrlHandled.current = true;
      Linking.getInitialURL().then((url) => { if (url) handleUrl({ url }); });
    }
    return () => sub.remove();
  }, [isAuthenticated, role, token, router]);

  // Auth guard + pending invite check
  useEffect(() => {
    if (isLoading) return;

    // Handle pending invite token (parent just signed in after tapping invite link)
    if (isAuthenticated && role === "parent" && token && pendingInviteToken) {
      const inviteToken = pendingInviteToken;
      clearPendingInviteToken();
      acceptInviteLink(token, inviteToken)
        .then(() => router.replace("/(parent)"))
        .catch((error: unknown) => {
          showInviteError(error);
          router.replace(homePath as Parameters<typeof router.replace>[0]);
        });
      return;
    }

    const inAuthGroup = segments[0] === "auth";
    const inOnboardingGroup = segments[0] === "onboarding";

    if (!isAuthenticated && !inAuthGroup) {
      router.replace("/auth");
      return;
    }

    if (isAuthenticated && inAuthGroup && homePath) {
      router.replace(homePath as Parameters<typeof router.replace>[0]);
      return;
    }

    if (isAuthenticated && !inAuthGroup && !inOnboardingGroup && homePath && userId) {
      // Only redirect if not already inside the user's home group
      const homeGroup = homePath.split("/").filter(Boolean)[0]; // e.g. "(teacher)"
      const inHomeGroup = segments[0] === homeGroup;
      if (!inHomeGroup) {
        void (async () => {
          const done = await isOnboardingComplete(userId);
          if (!done) {
            router.replace("/onboarding");
          } else {
            router.replace(homePath as Parameters<typeof router.replace>[0]);
          }
        })();
      }
    }
  }, [isAuthenticated, isLoading, role, token, segments, homePath, userId, router]);

  return <Slot />;
}

export default function RootLayout() {
  useEffect(() => {
    GoogleSignin.configure({
      webClientId: Constants.expoConfig?.extra?.googleWebClientId ?? "",
    });
  }, []);

  return (
    <TamaguiProvider config={tamaguiConfig}>
      <SafeAreaProvider>
        <ReducedMotionProvider>
          <AuthProvider>
            <AuthGuard />
          </AuthProvider>
        </ReducedMotionProvider>
      </SafeAreaProvider>
    </TamaguiProvider>
  );
}
