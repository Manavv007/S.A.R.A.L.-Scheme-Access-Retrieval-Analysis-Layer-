import { BACKEND_URL, backendHeaders } from "@/lib/server-config";

export const runtime = "nodejs";

// BFF proxy: forwards text to the FastAPI /voice/tts endpoint and streams the
// MP3 audio straight back to the client.
export async function POST(request: Request) {
  try {
    const body = await request.json();
    const upstream = await fetch(`${BACKEND_URL}/voice/tts`, {
      method: "POST",
      headers: backendHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(body),
      cache: "no-store",
    });

    if (!upstream.ok) {
      const text = await upstream.text().catch(() => "TTS error");
      return new Response(text || "TTS error", { status: upstream.status || 502 });
    }

    const audio = await upstream.arrayBuffer();
    return new Response(audio, {
      status: 200,
      headers: { "Content-Type": "audio/mpeg", "Cache-Control": "no-store" },
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Upstream error";
    return new Response(message, { status: 502 });
  }
}
