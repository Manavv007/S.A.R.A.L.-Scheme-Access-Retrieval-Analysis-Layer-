import { NextResponse } from "next/server";

import { BACKEND_URL, backendHeaders } from "@/lib/server-config";

export const runtime = "nodejs";

// BFF proxy: forwards a dialogue turn to the FastAPI /voice/converse endpoint.
export async function POST(request: Request) {
  try {
    const body = await request.json();
    const res = await fetch(`${BACKEND_URL}/voice/converse`, {
      method: "POST",
      headers: backendHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(body),
      cache: "no-store",
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Upstream error";
    return NextResponse.json(
      { reply: "", profile: {}, phase: "greet", schemes: [], error: message },
      { status: 502 },
    );
  }
}
