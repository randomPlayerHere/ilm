import { Slot } from "expo-router";
import { TamaguiProvider } from "tamagui";
import { tamaguiConfig } from "@ilm/design-tokens";

export default function RootLayout() {
  return (
    <TamaguiProvider config={tamaguiConfig}>
      <Slot />
    </TamaguiProvider>
  );
}
