/**
 * Stub for @react-native-google-signin/google-signin.
 * Used in Expo Go (via metro.config.js alias) since the real native module
 * is not available without a custom dev build.
 */

export const statusCodes = {
  SIGN_IN_CANCELLED: "SIGN_IN_CANCELLED",
  IN_PROGRESS: "IN_PROGRESS",
  PLAY_SERVICES_NOT_AVAILABLE: "PLAY_SERVICES_NOT_AVAILABLE",
  SIGN_IN_REQUIRED: "SIGN_IN_REQUIRED",
};

export const GoogleSignin = {
  configure: () => {},
  hasPlayServices: async () => true,
  signIn: async () => {
    throw new Error("Google Sign-In is not available in Expo Go. Use email/password login.");
  },
};

export function isSuccessResponse(_response: unknown): boolean {
  return false;
}

export function isErrorWithCode(_error: unknown): _error is { code: string } {
  return (
    typeof _error === "object" &&
    _error !== null &&
    "code" in (_error as object)
  );
}
