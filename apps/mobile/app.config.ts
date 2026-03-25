import { ConfigContext, ExpoConfig } from "expo/config";

export default ({ config }: ConfigContext): ExpoConfig => ({
  ...config,
  name: "Teacher OS",
  slug: "teacher-os",
  version: "0.1.0",
  orientation: "portrait",
  icon: "./assets/icon.png",
  userInterfaceStyle: "light",
  newArchEnabled: true,
  splash: {
    image: "./assets/splash-icon.png",
    resizeMode: "contain",
    backgroundColor: "#FAFAF5",
  },
  ios: {
    supportsTablet: true,
    bundleIdentifier: "com.ilm.teacheros",
  },
  android: {
    adaptiveIcon: {
      foregroundImage: "./assets/adaptive-icon.png",
      backgroundColor: "#FAFAF5",
    },
    package: "com.ilm.teacheros",
    intentFilters: [
      {
        action: "VIEW",
        autoVerify: true,
        data: [{ scheme: "ilm", host: "invite" }],
        category: ["BROWSABLE", "DEFAULT"],
      },
    ],
  },
  web: {
    bundler: "metro",
    output: "static",
    favicon: "./assets/favicon.png",
  },
  plugins: [
    "expo-dev-client",
    "expo-router",
    "expo-font",
    "expo-secure-store",
    "@react-native-google-signin/google-signin",
  ],
  scheme: "ilm",
  extra: {
    // Set EXPO_PUBLIC_API_URL in .env.local for physical devices or non-localhost targets.
    // Omit it for emulator/simulator — api-client.ts will use the correct platform fallback.
    apiBaseUrl: process.env.EXPO_PUBLIC_API_URL,
    googleWebClientId:
      "596169360316-octgu7hunj5lptdhgjncioapmnf0o8gd.apps.googleusercontent.com",
  },
});
