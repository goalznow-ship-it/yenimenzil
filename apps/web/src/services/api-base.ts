/**
 * Resolve the FastAPI base URL.
 *
 * - Server-side (SSR) code reaches the backend through the container network
 *   via API_INTERNAL_URL (e.g. http://api:8000/api/v1).
 * - Client-side (browser) code always uses NEXT_PUBLIC_API_URL (public URL),
 *   because API_INTERNAL_URL is never inlined into client bundles.
 *
 * Non-NEXT_PUBLIC env vars are read at runtime on the server only, so this is
 * safe for isomorphic modules used by both server and client components.
 */
export const API_BASE_URL =
  process.env.API_INTERNAL_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000/api/v1";
