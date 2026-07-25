import { NextResponse } from "next/server";

import { BACKEND_URL, backendHeaders } from "@/lib/server-config";

export const runtime = "nodejs";

// BFF proxy: forwards the recorded audio (multipart form) to the FastAPI
// /voice/stt endpoint and returns the transcript JSON.
export async function POST(request: Request) {
  try {
    const form = await request.formData();
    // Do not set Content-Type — fetch must generate the multipart boundary.
    const upstream = await fetch(`${BACKEND_URL}/voice/stt`, {
      method: "POST",
      headers: backendHeaders(),
      body: form,
      cache: "no-store",
    });
    const data = await upstream.json();
    return NextResponse.json(data, { status: upstream.status });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Upstream error";
    return NextResponse.json({ text: "", error: message }, { status: 502 });
  }
}
