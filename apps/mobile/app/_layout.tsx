import { Slot } from "expo-router";
import { TamaguiProvider } from "tamagui";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { tamaguiConfig } from "@ilm/design-tokens";
import { ReducedMotionProvider } from "../src/contexts/ReducedMotionContext";

export default function RootLayout() {
  return (
    <TamaguiProvider config={tamaguiConfig}>
      <SafeAreaProvider>
        <ReducedMotionProvider>
          <Slot />
        </ReducedMotionProvider>
      </SafeAreaProvider>
    </TamaguiProvider>
  );
}
