import type { LoginResponse, GoogleLoginRequest } from "@ilm/contracts";
import { apiRequest, ApiError } from "./api-client";

export class InvalidCredentialsError extends Error {
  name = "InvalidCredentialsError" as const;
}

export class InactiveAccountError extends Error {
  name = "InactiveAccountError" as const;
}

export class RateLimitError extends Error {
  name = "RateLimitError" as const;
}

export class NoOrgMembershipError extends Error {
  name = "NoOrgMembershipError" as const;
}

export class GoogleAuthFailedError extends Error {
  name = "GoogleAuthFailedError" as const;
}

export class PlayServicesUnavailableError extends Error {
  name = "PlayServicesUnavailableError" as const;
}

export async function loginWithGoogle(idToken: string): Promise<LoginResponse> {
  const body: GoogleLoginRequest = { id_token: idToken };
  try {
    return await apiRequest<LoginResponse>("/auth/google", {
      method: "POST",
      body,
    });
  } catch (error) {
    if (error instanceof ApiError) {
      switch (error.status) {
        case 401:
          throw new GoogleAuthFailedError("Google sign-in failed. Please try again.");
        case 403:
          throw new NoOrgMembershipError(
            "Your account is not authorized for any organization. Contact your administrator.",
          );
        case 429:
          throw new RateLimitError("Too many sign-in attempts. Please wait and try again.");
      }
    }
    throw error;
  }
}

export async function loginWithEmailPassword(
  email: string,
  password: string,
): Promise<LoginResponse> {
  try {
    return await apiRequest<LoginResponse>("/auth/login", {
      method: "POST",
      body: { email, password },
    });
  } catch (error) {
    if (error instanceof ApiError) {
      switch (error.status) {
        case 401:
          throw new InvalidCredentialsError(
            "Email or password is incorrect",
          );
        case 403:
          throw new InactiveAccountError(
            "Your account is not active. Contact your administrator.",
          );
        case 429:
          throw new RateLimitError(
            "Too many sign-in attempts. Please wait and try again.",
          );
      }
    }
    throw error;
  }
}
