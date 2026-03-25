import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useMemo,
  type ReactNode,
} from "react";
import type { UserRole } from "@ilm/contracts";
import { GoogleSignin, isSuccessResponse, isErrorWithCode, statusCodes } from "@react-native-google-signin/google-signin";
import { saveAuthData, getAuthData, clearAuthData } from "../services/token-storage";
import { loginWithEmailPassword, loginWithGoogle, PlayServicesUnavailableError } from "../services/auth-service";
import { setUnauthorizedHandler } from "../services/api-client";

function decodeJwtPayload(token: string): { exp: number; sub: string; role: string; org_id: string } {
  // JWT uses base64url encoding — convert to standard base64 before calling atob
  const base64url = token.split(".")[1];
  const base64 = base64url.replace(/-/g, "+").replace(/_/g, "/");
  const padded = base64.padEnd(base64.length + (4 - (base64.length % 4)) % 4, "=");
  const json = atob(padded);
  return JSON.parse(json);
}

function isTokenExpired(token: string): boolean {
  try {
    const { exp } = decodeJwtPayload(token);
    return Date.now() >= exp * 1000;
  } catch {
    return true;
  }
}

interface AuthState {
  isLoading: boolean;
  isAuthenticated: boolean;
  token: string | null;
  role: UserRole | null;
  homePath: string | null;
  sessionExpired: boolean;
  lastEmail: string | null;
  userId: string | null;
  orgId: string | null;
}

interface AuthContextValue extends AuthState {
  signIn: (email: string, password: string) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  signOut: (options?: { sessionExpired?: boolean }) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    isLoading: true,
    isAuthenticated: false,
    token: null,
    role: null,
    homePath: null,
    sessionExpired: false,
    lastEmail: null,
    userId: null,
    orgId: null,
  });

  // On mount, check for stored token
  useEffect(() => {
    (async () => {
      try {
        const data = await getAuthData();
        if (data && !isTokenExpired(data.token)) {
          const { sub: userId, org_id: orgId } = decodeJwtPayload(data.token);
          setState({
            isLoading: false,
            isAuthenticated: true,
            token: data.token,
            role: data.role as UserRole,
            homePath: data.homePath,
            sessionExpired: false,
            lastEmail: data.email,
            userId,
            orgId,
          });
          return;
        }
        // Token expired or missing — clear and show sign-in
        if (data) {
          await clearAuthData();
        }
      } catch {
        // SecureStore error — proceed to sign-in
      }
      setState((prev) => ({ ...prev, isLoading: false }));
    })();
  }, []);

  const signIn = useCallback(async (email: string, password: string) => {
    const response = await loginWithEmailPassword(email, password);
    await saveAuthData(response.access_token, response.role, response.home_path, email);
    const { sub: userId, org_id: orgId } = decodeJwtPayload(response.access_token);
    setState({
      isLoading: false,
      isAuthenticated: true,
      token: response.access_token,
      role: response.role,
      homePath: response.home_path,
      sessionExpired: false,
      lastEmail: email,
      userId,
      orgId,
    });
  }, []);

  const signInWithGoogle = useCallback(async () => {
    try {
      await GoogleSignin.hasPlayServices({ showPlayServicesUpdateDialog: true });
    } catch (err) {
      if (isErrorWithCode(err) && err.code === statusCodes.PLAY_SERVICES_NOT_AVAILABLE) {
        throw new PlayServicesUnavailableError(
          "Google Play Services is not available on this device.",
        );
      }
      throw err;
    }
    const response = await GoogleSignin.signIn();
    if (!isSuccessResponse(response)) {
      // User cancelled the flow — return cleanly without throwing
      return;
    }
    const idToken = response.data.idToken;
    if (!idToken) {
      throw new Error("No ID token returned from Google. Ensure webClientId is configured.");
    }
    const loginResponse = await loginWithGoogle(idToken);
    await saveAuthData(
      loginResponse.access_token,
      loginResponse.role,
      loginResponse.home_path,
      response.data.user.email,
    );
    const { sub: userId, org_id: orgId } = decodeJwtPayload(loginResponse.access_token);
    setState({
      isLoading: false,
      isAuthenticated: true,
      token: loginResponse.access_token,
      role: loginResponse.role as UserRole,
      homePath: loginResponse.home_path,
      sessionExpired: false,
      lastEmail: response.data.user.email,
      userId,
      orgId,
    });
  }, []);

  const signOut = useCallback(async (options?: { sessionExpired?: boolean }) => {
    const currentEmail = state.lastEmail;
    await clearAuthData();
    setState({
      isLoading: false,
      isAuthenticated: false,
      token: null,
      role: null,
      homePath: null,
      sessionExpired: options?.sessionExpired ?? false,
      lastEmail: currentEmail,
      userId: null,
      orgId: null,
    });
  }, [state.lastEmail]);

  // Wire api-client's 401 interceptor to trigger session-expired sign-out
  useEffect(() => {
    setUnauthorizedHandler(() => signOut({ sessionExpired: true }));
    return () => setUnauthorizedHandler(null);
  }, [signOut]);

  const value = useMemo<AuthContextValue>(
    () => ({ ...state, signIn, signInWithGoogle, signOut }),
    [state, signIn, signInWithGoogle, signOut],
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
