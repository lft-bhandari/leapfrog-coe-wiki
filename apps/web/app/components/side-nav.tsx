type ActiveRoute = "chat" | "graph" | "design" | null

interface SideNavProps {
  active?: ActiveRoute
}

const NAV_LINKS: { href: string; label: string; id: ActiveRoute }[] = [
  { href: "/chat", label: "Chat", id: "chat" },
  { href: "/graph", label: "Graph", id: "graph" },
  { href: "/design", label: "Design System", id: "design" },
]

/** Sidebar navigation used in LayoutShell across all app routes. */
export function SideNav({ active }: SideNavProps) {
  return (
    <div className="space-y-2">
      <p className="text-xs font-bold text-brand-emerald uppercase tracking-wider">CoE Wiki</p>
      <nav className="mt-4 space-y-1">
        {NAV_LINKS.map(({ href, label, id }) => (
          <a
            key={id}
            href={href}
            className={[
              "block rounded px-2 py-1 text-xs text-brand-ivory",
              active === id ? "bg-brand-obsidian" : "hover:bg-brand-obsidian",
            ].join(" ")}
          >
            {label}
          </a>
        ))}
      </nav>
    </div>
  )
}
