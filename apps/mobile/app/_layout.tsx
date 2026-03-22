import { useEffect } from "react";
import { Slot, useRouter, useSegments } from "expo-router";
import { TamaguiProvider } from "tamagui";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { tamaguiConfig } from "@ilm/design-tokens";
import { GoogleSignin } from "@react-native-google-signin/google-signin";
import Constants from "expo-constants";
import { ReducedMotionProvider } from "../src/contexts/ReducedMotionContext";
import { AuthProvider, useAuth } from "../src/contexts/AuthContext";

function AuthGuard() {
  const { isLoading, isAuthenticated, homePath } = useAuth();
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;

    const inAuthGroup = segments[0] === "auth";

    if (!isAuthenticated && !inAuthGroup) {
      router.replace("/auth");
    } else if (isAuthenticated && inAuthGroup && homePath) {
      router.replace(homePath as Parameters<typeof router.replace>[0]);
    }
  }, [isAuthenticated, isLoading, segments, homePath, router]);

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
