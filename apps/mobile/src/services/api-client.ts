import Constants from "expo-constants";
import { Platform } from "react-native";

// Android emulator routes to host via 10.0.2.2; iOS simulator shares host network
const DEV_FALLBACK =
  Platform.OS === "android" ? "http://10.0.2.2:8000" : "http://localhost:8000";

export const API_BASE_URL: string =
  Constants.expoConfig?.extra?.apiBaseUrl ?? DEV_FALLBACK;

export class NetworkError extends Error {
  name = "NetworkError" as const;
}

export class ApiError extends Error {
  name = "ApiError" as const;
  constructor(
    public code: string,
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

let onUnauthorizedHandler: (() => void) | null = null;

/** Register a callback invoked when an authenticated request returns 401. */
export function setUnauthorizedHandler(handler: (() => void) | null): void {
  onUnauthorizedHandler = handler;
}

type RequestOptions = {
  method?: string;
  body?: unknown;
  token?: string | null;
};

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { method = "GET", body, token } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new NetworkError("No internet connection");
  }

  if (!response.ok) {
    // Authenticated requests that return 401 mean the token has expired mid-session
    if (response.status === 401 && token && onUnauthorizedHandler) {
      onUnauthorizedHandler();
    }
    let detail = "An unexpected error occurred";
    try {
      const errorBody = await response.json();
      detail = errorBody.detail ?? errorBody.error?.message ?? detail;
    } catch {
      // non-JSON error body — use default
    }
    throw new ApiError(String(response.status), detail, response.status);
  }

  return response.json() as Promise<T>;
}
