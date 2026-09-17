import { Button } from "@/app/components/button"

export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-brand-white">
      <div className="space-y-4 text-center">
        <h1 className="text-3xl font-black text-brand-abyss">CoE Wiki</h1>
        <p className="text-sm text-brand-obsidian">Leapfrog Centre of Excellence knowledge base</p>
        <div className="flex justify-center gap-3">
          <a href="/design">
            <Button variant="secondary" size="sm">Design System</Button>
          </a>
        </div>
      </div>
    </div>
  )
}
