import { Platform } from "react-native";
import * as SecureStore from "expo-secure-store";

// expo-secure-store uses native APIs that don't exist on web — use localStorage instead
const storage =
  Platform.OS === "web"
    ? {
        setItemAsync: async (key: string, value: string) => { localStorage.setItem(key, value); },
        getItemAsync: async (key: string) => localStorage.getItem(key),
        deleteItemAsync: async (key: string) => { localStorage.removeItem(key); },
      }
    : SecureStore;

const KEYS = {
  onboardingDone: (userId: string) => `ilm_onboarding_done_${userId}`,
  notifPref: (userId: string) => `ilm_notif_pref_${userId}`,
} as const;

export async function isOnboardingComplete(userId: string): Promise<boolean> {
  const val = await storage.getItemAsync(KEYS.onboardingDone(userId));
  return val === "true";
}

export async function markOnboardingComplete(userId: string): Promise<void> {
  await storage.setItemAsync(KEYS.onboardingDone(userId), "true");
}

export async function getNotifPref(userId: string): Promise<boolean> {
  const val = await storage.getItemAsync(KEYS.notifPref(userId));
  return val !== "false"; // default ON
}

export async function setNotifPref(userId: string, enabled: boolean): Promise<void> {
  await storage.setItemAsync(KEYS.notifPref(userId), String(enabled));
}
