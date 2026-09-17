import { FASTAPI_URL } from "@/lib/config"

// Proxy for the FastAPI wiki page endpoint. The browser never calls FastAPI directly (ADR-0005).
export async function GET(
  _req: Request,
  { params }: { params: Promise<{ path: string[] }> },
): Promise<Response> {
  const { path } = await params
  const pagePath = path.join("/")

  const upstream = await fetch(`${FASTAPI_URL}/api/wiki/${pagePath}`, {
    next: { revalidate: 60 },
  })

  if (!upstream.ok) {
    return new Response(await upstream.text(), { status: upstream.status })
  }

  const data = await upstream.json()
  return Response.json(data)
}
