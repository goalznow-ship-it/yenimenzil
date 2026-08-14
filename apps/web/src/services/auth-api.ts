/**
 * Auth API client — talks to the FastAPI auth endpoints using httpOnly
 * cookies (SameSite=Lax), so no tokens are stored in JS.
 */

export type UserRole =
  | "user"
  | "owner"
  | "agent"
  | "agency_admin"
  | "moderator"
  | "admin"
  | "super_admin";

export interface ProfileData {
  avatar_url: string | null;
  bio: string | null;
  city: string | null;
  preferred_language: string;
  member_since: string | null;
  phone_verified: boolean;
  identity_verified: boolean;
}

export interface User {
  id: string;
  email: string;
  phone: string | null;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  profile: ProfileData | null;
}

export interface RegisterInput {
  email: string;
  password: string;
  full_name: string;
  phone?: string;
}

export interface UpdateProfileInput {
  full_name?: string;
  phone?: string;
  bio?: string;
  city?: string;
  preferred_language?: string;
}

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  init: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...init.headers },
    ...init
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail =
      (body && typeof body.detail === "string" && body.detail) ||
      (body && Array.isArray(body.detail)
        ? body.detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join(", ")
        : null) ||
      "Xəta baş verdi";
    throw new ApiError(response.status, detail);
  }
  return body as T;
}

export const authApi = {
  async register(input: RegisterInput): Promise<{ user: User }> {
    return request("/auth/register", {
      method: "POST",
      body: JSON.stringify(input)
    });
  },

  async login(email: string, password: string): Promise<{ user: User }> {
    return request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    });
  },

  async logout(): Promise<void> {
    return request("/auth/logout", { method: "POST" });
  },

  async me(): Promise<User> {
    return request("/auth/me");
  },

  async updateProfile(input: UpdateProfileInput): Promise<User> {
    return request("/users/me", {
      method: "PATCH",
      body: JSON.stringify(input)
    });
  },

  async forgotPassword(email: string): Promise<void> {
    await request("/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email })
    });
  },

  async resetPassword(token: string, newPassword: string): Promise<void> {
    await request("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ token, new_password: newPassword })
    });
  },

  async verifyEmail(token: string): Promise<void> {
    await request("/auth/verify-email", {
      method: "POST",
      body: JSON.stringify({ token })
    });
  },

  ApiError
};
