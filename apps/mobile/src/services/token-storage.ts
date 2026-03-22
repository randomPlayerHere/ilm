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
  accessToken: "auth_access_token",
  userRole: "auth_user_role",
  homePath: "auth_home_path",
  userEmail: "auth_user_email",
} as const;

export interface AuthData {
  token: string;
  role: string;
  homePath: string;
  email: string;
}

export async function saveAuthData(
  token: string,
  role: string,
  homePath: string,
  email: string,
): Promise<void> {
  await Promise.all([
    storage.setItemAsync(KEYS.accessToken, token),
    storage.setItemAsync(KEYS.userRole, role),
    storage.setItemAsync(KEYS.homePath, homePath),
    storage.setItemAsync(KEYS.userEmail, email),
  ]);
}

export async function getAuthData(): Promise<AuthData | null> {
  const [token, role, homePath, email] = await Promise.all([
    storage.getItemAsync(KEYS.accessToken),
    storage.getItemAsync(KEYS.userRole),
    storage.getItemAsync(KEYS.homePath),
    storage.getItemAsync(KEYS.userEmail),
  ]);

  if (!token || !role || !homePath) {
    return null;
  }

  return { token, role, homePath, email: email ?? "" };
}

export async function clearAuthData(): Promise<void> {
  await Promise.all([
    storage.deleteItemAsync(KEYS.accessToken),
    storage.deleteItemAsync(KEYS.userRole),
    storage.deleteItemAsync(KEYS.homePath),
    storage.deleteItemAsync(KEYS.userEmail),
  ]);
}
