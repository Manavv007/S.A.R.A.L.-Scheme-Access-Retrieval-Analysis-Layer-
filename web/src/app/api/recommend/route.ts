import { NextResponse } from "next/server";

import { BACKEND_URL, backendHeaders } from "@/lib/server-config";

export const runtime = "nodejs";

// BFF proxy: forwards the profile to the FastAPI /recommend endpoint, keeping
// the backend URL + API key server-side.
export async function POST(request: Request) {
  try {
    const body = await request.json();
    const res = await fetch(`${BACKEND_URL}/recommend`, {
      method: "POST",
      headers: backendHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(body),
      cache: "no-store",
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Upstream error";
    return NextResponse.json({ recommendations: [], error: message }, { status: 502 });
  }
}
