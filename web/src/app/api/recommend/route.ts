import { NextResponse } from "next/server";

import { BACKEND_URL, backendHeaders } from "@/lib/server-config";

export const runtime = "nodejs";
// Allow up to 60 s so Render free-tier cold-start (50-90 s) doesn't time out.
export const maxDuration = 60;

const MAX_RETRIES = 2;
const RETRY_DELAY_MS = 8000; // wait 8 s before retrying a cold-start 502

// BFF proxy: forwards the profile to the FastAPI /recommend endpoint, keeping
// the backend URL + API key server-side.
export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { recommendations: [], error: "Invalid request body" },
      { status: 400 },
    );
  }

  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      const res = await fetch(`${BACKEND_URL}/recommend`, {
        method: "POST",
        headers: backendHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify(body),
        cache: "no-store",
      });

      // Try to parse JSON; fall back to text on parse failure (e.g. HTML 502 page)
      let data: unknown;
      const contentType = res.headers.get("content-type") || "";
      if (contentType.includes("application/json")) {
        data = await res.json();
      } else {
        const text = await res.text();
        // Non-JSON body means Render is still waking up — retry if we can
        if (!res.ok && attempt < MAX_RETRIES) {
          await new Promise((r) => setTimeout(r, RETRY_DELAY_MS));
          continue;
        }
        return NextResponse.json(
          {
            recommendations: [],
            error: `Server is starting up. Please try again in a moment. (${res.status})`,
          },
          { status: 503 },
        );
      }

      return NextResponse.json(data, { status: res.status });
    } catch (err) {
      if (attempt < MAX_RETRIES) {
        await new Promise((r) => setTimeout(r, RETRY_DELAY_MS));
        continue;
      }
      const message = err instanceof Error ? err.message : "Upstream error";
      return NextResponse.json(
        { recommendations: [], error: message },
        { status: 502 },
      );
    }
  }

  // Should not reach here
  return NextResponse.json(
    { recommendations: [], error: "Max retries exceeded" },
    { status: 503 },
  );
}
