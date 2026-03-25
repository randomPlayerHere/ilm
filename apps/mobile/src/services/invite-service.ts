import type {
  GuardianStudentLinkResponse,
  InviteLinkResolveResponse,
  InviteLinkResponse,
} from "@ilm/contracts";

import { ApiError, apiRequest } from "./api-client";

export class InviteLinkExpiredError extends Error {
  name = "InviteLinkExpiredError" as const;
}

export class InviteLinkAlreadyUsedError extends Error {
  name = "InviteLinkAlreadyUsedError" as const;
}

export class AlreadyLinkedError extends Error {
  name = "AlreadyLinkedError" as const;
}

export async function generateInviteLink(
  token: string,
  classId: string,
  studentId: string,
): Promise<InviteLinkResponse> {
  return apiRequest<InviteLinkResponse>(
    `/onboarding/classes/${classId}/students/${studentId}/invite-link`,
    { method: "POST", token },
  );
}

export async function resolveInviteLink(
  inviteToken: string,
): Promise<InviteLinkResolveResponse> {
  // No auth token — this is a public endpoint
  return apiRequest<InviteLinkResolveResponse>(`/onboarding/invite/${inviteToken}`);
}

export async function acceptInviteLink(
  authToken: string,
  inviteToken: string,
): Promise<GuardianStudentLinkResponse> {
  try {
    return await apiRequest<GuardianStudentLinkResponse>(
      `/onboarding/invite/${inviteToken}/accept`,
      { method: "POST", token: authToken },
    );
  } catch (error) {
    if (error instanceof ApiError) {
      switch (error.status) {
        case 400: {
          try {
            const resolved = await resolveInviteLink(inviteToken);
            if (!resolved.valid && resolved.reason === "already_used") {
              throw new InviteLinkAlreadyUsedError("This invite link has already been used.");
            }
            if (!resolved.valid && resolved.reason === "expired") {
              throw new InviteLinkExpiredError("This invite link has expired.");
            }
          } catch {
            throw new InviteLinkExpiredError("This invite link is no longer valid.");
          }
          throw new InviteLinkExpiredError("This invite link is no longer valid.");
        }
        case 409:
          throw new AlreadyLinkedError("You are already linked to this student.");
      }
    }
    throw error;
  }
}
