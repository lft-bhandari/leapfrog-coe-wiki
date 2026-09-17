import { FASTAPI_URL } from "@/lib/config"

// Proxy for the FastAPI graph endpoint. The browser never calls FastAPI directly (ADR-0005).
export async function GET(): Promise<Response> {
  const upstream = await fetch(`${FASTAPI_URL}/api/graph`, {
    // Short cache: graph changes when new docs are ingested
    next: { revalidate: 30 },
  })

  if (!upstream.ok) {
    return new Response(await upstream.text(), { status: upstream.status })
  }

  const data = await upstream.json()
  return Response.json(data)
}
