// Server-only: base URL of the FastAPI backend. Never exposed to the client.
export const BACKEND_URL = (
  process.env.BACKEND_URL || "http://localhost:8000/api/v1"
).replace(/\/$/, "");
