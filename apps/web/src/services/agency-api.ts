/**
 * Agency tooling: team invites (API mode only).
 */
import type { UserRole } from "@/services/auth-api";
import { API_BASE_URL } from "@/services/api-base";

const API_URL = API_BASE_URL;
export const USE_DEMO_DATA =
  (process.env.NEXT_PUBLIC_USE_DEMO_DATA ?? "true") !== "false";

export interface AgencyInvite {
  id: string;
  agency_id: string;
  email: string;
  role: "agent" | "agency_admin";
  status: "pending" | "accepted" | "declined" | "expired";
  token: string;
  created_by: string | null;
  expires_at: string;
  accepted_at: string | null;
  created_at: string;
}

export interface InviteInput {
  email: string;
  role: "agent" | "agency_admin";
}

export async function listInvites(): Promise<AgencyInvite[]> {
  if (USE_DEMO_DATA) return [];
  const response = await fetch(`${API_URL}/agencies/me/invites`, {
    cache: "no-store"
  });
  if (!response.ok) {
    if (response.status === 403) return [];
    throw new Error(`API ${response.status}`);
  }
  return (await response.json()) as AgencyInvite[];
}

export async function createInvite(
  input: InviteInput
): Promise<AgencyInvite> {
  const response = await fetch(`${API_URL}/agencies/me/invites`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(
      (body as { detail?: string } | null)?.detail ?? `API ${response.status}`
    );
  }
  return (await response.json()) as AgencyInvite;
}

export async function cancelInvite(id: string): Promise<void> {
  const response = await fetch(`${API_URL}/agencies/me/invites/${id}`, {
    method: "DELETE"
  });
  if (!response.ok) throw new Error(`API ${response.status}`);
}

export function inviteRoleLabel(role: string): string {
  return role === "agency_admin" ? "Rəhbər" : "Agent";
}

export function inviteStatusLabel(status: string): string {
  switch (status) {
    case "pending":
      return "Gözləyir";
    case "accepted":
      return "Qəbul edilib";
    case "declined":
      return "İmtina edilib";
    default:
      return "Müddəti bitib";
  }
}

export function isAgencyAdmin(role: UserRole | undefined): boolean {
  return role === "agency_admin";
}