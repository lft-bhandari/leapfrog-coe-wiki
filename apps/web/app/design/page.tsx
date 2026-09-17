import { Badge } from "@/app/components/badge"
import { Button } from "@/app/components/button"
import { Card } from "@/app/components/card"
import { TextInput, Textarea } from "@/app/components/input"
import { LayoutShell } from "@/app/components/layout-shell"
import { Spinner } from "@/app/components/spinner"

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-4">
      <h2 className="text-md font-bold text-brand-obsidian border-b border-brand-ivory pb-2">
        {title}
      </h2>
      {children}
    </section>
  )
}

function DesignContent() {
  return (
    <div className="max-w-3xl space-y-12 py-4">
      <div>
        <h1 className="text-3xl font-black text-brand-abyss">Design System</h1>
        <p className="mt-2 text-sm text-brand-obsidian">
          Leapfrog CoE Wiki — brand tokens and base components.
        </p>
      </div>

      {/* Color palette */}
      <Section title="Color Tokens">
        <div className="flex flex-wrap gap-3">
          {[
            { name: "brand-primary", bg: "bg-brand-primary", text: "text-brand-white", label: "#038E43" },
            { name: "brand-abyss", bg: "bg-brand-abyss", text: "text-brand-white", label: "#111111" },
            { name: "brand-obsidian", bg: "bg-brand-obsidian", text: "text-brand-white", label: "#333333" },
            { name: "brand-ivory", bg: "bg-brand-ivory", text: "text-brand-abyss", label: "#D9D9D9" },
            { name: "brand-emerald", bg: "bg-brand-emerald", text: "text-brand-abyss", label: "#00DF66" },
            { name: "brand-mint", bg: "bg-brand-mint", text: "text-brand-abyss", label: "#B4FFD6" },
            { name: "brand-gold", bg: "bg-brand-gold", text: "text-brand-abyss", label: "#FFD700" },
          ].map((swatch) => (
            <div
              key={swatch.name}
              className={`${swatch.bg} ${swatch.text} flex flex-col items-start rounded-md p-3 w-36`}
            >
              <span className="text-xs font-bold">{swatch.name}</span>
              <span className="text-2xs opacity-80">{swatch.label}</span>
            </div>
          ))}
        </div>
      </Section>

      {/* Typography */}
      <Section title="Typography Scale">
        <div className="space-y-2">
          {[
            { cls: "text-3xl font-black", label: "36px / Black" },
            { cls: "text-2xl font-bold", label: "32px / Bold" },
            { cls: "text-xl font-bold", label: "24px / Bold" },
            { cls: "text-lg font-normal", label: "20px / Normal" },
            { cls: "text-md font-normal", label: "18px / Normal" },
            { cls: "text-sm font-normal", label: "16px / Normal" },
            { cls: "text-xs font-normal", label: "14px / Normal" },
            { cls: "text-2xs font-light", label: "12px / Light" },
          ].map((row) => (
            <p key={row.cls} className={`${row.cls} text-brand-abyss`}>
              {row.label} — The quick brown fox
            </p>
          ))}
        </div>
      </Section>

      {/* Buttons */}
      <Section title="Button">
        <div className="flex flex-wrap gap-3">
          <Button variant="primary">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="primary" size="sm">Small</Button>
          <Button variant="primary" size="lg">Large</Button>
          <Button variant="primary" disabled>Disabled</Button>
        </div>
      </Section>

      {/* Inputs */}
      <Section title="Input & Textarea">
        <div className="space-y-3 max-w-sm">
          <TextInput placeholder="Type something…" />
          <Textarea placeholder="Multi-line input…" rows={3} />
        </div>
      </Section>

      {/* Card */}
      <Section title="Card">
        <div className="grid grid-cols-2 gap-4">
          <Card>
            <p className="text-sm font-bold text-brand-abyss">Default card</p>
            <p className="mt-1 text-xs text-brand-obsidian">Shadow only, no border ring.</p>
          </Card>
          <Card bordered>
            <p className="text-sm font-bold text-brand-abyss">Bordered card</p>
            <p className="mt-1 text-xs text-brand-obsidian">Extra 1px ring for white backgrounds.</p>
          </Card>
        </div>
      </Section>

      {/* Badges */}
      <Section title="Badge — Node Types">
        <div className="flex flex-wrap gap-3">
          <Badge type="domain" />
          <Badge type="concept" />
          <Badge type="entity" />
          <Badge type="source" />
          <Badge type="domain" label="Gen-AI Fundamentals" />
          <Badge type="concept" label="RAG" />
        </div>
      </Section>

      {/* Spinner */}
      <Section title="Spinner">
        <div className="flex items-center gap-6">
          <Spinner size="sm" label="Small spinner" />
          <Spinner size="md" label="Medium spinner" />
          <Spinner size="lg" label="Large spinner" />
        </div>
      </Section>
    </div>
  )
}

export default function DesignPage() {
  return (
    <LayoutShell
      sidebar={
        <div className="space-y-2">
          <p className="text-xs font-bold text-brand-emerald uppercase tracking-wider">CoE Wiki</p>
          <nav className="mt-4 space-y-1">
            <a href="/design" className="block rounded px-2 py-1 text-xs text-brand-ivory hover:bg-brand-obsidian">
              Design System
            </a>
          </nav>
        </div>
      }
    >
      <DesignContent />
    </LayoutShell>
  )
}
