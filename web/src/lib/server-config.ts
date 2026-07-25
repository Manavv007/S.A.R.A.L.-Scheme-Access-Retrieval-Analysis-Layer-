// Server-only: base URL of the FastAPI backend. Never exposed to the client.
export const BACKEND_URL = (
  process.env.BACKEND_URL || "http://localhost:8000/api/v1"
).replace(/\/$/, "");

/**
 * Headers for server-side calls to FastAPI.
 * When SARAL_API_KEY is set (web/.env.local), every BFF proxy must forward it
 * as X-API-Key so protected backend routes accept the request.
 */
export function backendHeaders(
  extra: Record<string, string> = {},
): Record<string, string> {
  const headers: Record<string, string> = { ...extra };
  const key = process.env.SARAL_API_KEY;
  if (key) headers["X-API-Key"] = key;
  return headers;
}
