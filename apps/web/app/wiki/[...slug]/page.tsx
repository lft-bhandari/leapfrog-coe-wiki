import { notFound } from "next/navigation"
import { Badge } from "@/app/components/badge"
import { Card } from "@/app/components/card"
import { LayoutShell } from "@/app/components/layout-shell"

// Internal URL is used server-side; the browser never calls FastAPI directly (ADR-0005).
const FASTAPI_URL = process.env.FASTAPI_INTERNAL_URL ?? "http://localhost:8000"

interface WikiPage {
  path: string
  title: string
  content: string
}

async function fetchWikiPage(path: string): Promise<WikiPage | null> {
  try {
    const res = await fetch(`${FASTAPI_URL}/api/wiki/${path}`, {
      // Revalidate every 60 s so the reader stays reasonably fresh
      next: { revalidate: 60 },
    })
    if (res.status === 404) return null
    if (!res.ok) throw new Error(`FastAPI ${res.status}`)
    return res.json()
  } catch {
    return null
  }
}

interface PageProps {
  params: Promise<{ slug: string[] }>
}

export default async function WikiPageReader({ params }: PageProps) {
  const { slug } = await params
  const path = slug.join("/")
  const page = await fetchWikiPage(path)

  if (!page) notFound()

  const parts = page.path.split("/")
  const nodeType = parts[0] as "domain" | "concept" | "entity" | "source"

  return (
    <LayoutShell
      sidebar={
        <div className="space-y-2">
          <p className="text-xs font-bold text-brand-emerald uppercase tracking-wider">CoE Wiki</p>
          <nav className="mt-4 space-y-1">
            <a href="/chat" className="block rounded px-2 py-1 text-xs text-brand-ivory hover:bg-brand-obsidian">
              Chat
            </a>
          </nav>
        </div>
      }
    >
      <div className="max-w-3xl space-y-6">
        {/* Header */}
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <Badge type={nodeType} />
            <span className="text-2xs text-brand-obsidian font-mono">{page.path}</span>
          </div>
          <h1 className="text-2xl font-bold text-brand-abyss">{page.title}</h1>
        </div>

        {/* Content */}
        <Card bordered>
          <pre className="whitespace-pre-wrap text-sm text-brand-abyss font-sans leading-7">
            {page.content}
          </pre>
        </Card>

        <a href="/chat" className="text-xs text-brand-primary hover:underline">
          ← Back to chat
        </a>
      </div>
    </LayoutShell>
  )
}
