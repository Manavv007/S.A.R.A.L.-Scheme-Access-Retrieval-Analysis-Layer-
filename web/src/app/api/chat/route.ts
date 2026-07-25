import { BACKEND_URL, backendHeaders } from "@/lib/server-config";

export const runtime = "nodejs";

// BFF proxy for streaming chat. Forwards the request to the FastAPI
// /chat/stream endpoint and pipes the token stream straight back to the
// client, so the assistant's reply renders token-by-token.
export async function POST(request: Request) {
  const body = await request.json();

  try {
    const upstream = await fetch(`${BACKEND_URL}/chat/stream`, {
      method: "POST",
      headers: backendHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(body),
      cache: "no-store",
    });

    if (!upstream.ok || !upstream.body) {
      const text = await upstream.text().catch(() => "Upstream error");
      return new Response(text || "Upstream error", { status: upstream.status || 502 });
    }

    return new Response(upstream.body, {
      status: 200,
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Cache-Control": "no-cache, no-transform",
        "X-Accel-Buffering": "no",
      },
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Connection error";
    return new Response(message, { status: 502 });
  }
}
