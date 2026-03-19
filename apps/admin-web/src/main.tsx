import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { TamaguiProvider } from "tamagui";
import { tamaguiConfig } from "@ilm/design-tokens";
import { App } from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <TamaguiProvider config={tamaguiConfig}>
      <App />
    </TamaguiProvider>
  </StrictMode>
);
