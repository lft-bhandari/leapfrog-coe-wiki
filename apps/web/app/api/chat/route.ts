// Proxy for the FastAPI streaming chat endpoint. The browser never calls
// FastAPI directly — Next.js is the single public surface (ADR-0005).
const FASTAPI_URL = process.env.FASTAPI_INTERNAL_URL ?? "http://localhost:8000"

export async function POST(req: Request): Promise<Response> {
  const body = await req.json()

  const upstream = await fetch(`${FASTAPI_URL}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })

  if (!upstream.ok) {
    return new Response(await upstream.text(), { status: upstream.status })
  }

  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  })
}
