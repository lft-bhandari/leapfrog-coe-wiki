interface LayoutShellProps {
  sidebar: React.ReactNode
  children: React.ReactNode
}

/**
 * Top-level shell that places a fixed-width sidebar beside the main content area.
 * Both slots are provided by the caller so this component has no routing dependency.
 */
export function LayoutShell({ sidebar, children }: LayoutShellProps) {
  return (
    <div className="flex h-screen overflow-hidden bg-brand-white">
      <aside className="flex w-64 shrink-0 flex-col border-r border-brand-ivory bg-brand-abyss px-4 py-6">
        {sidebar}
      </aside>
      <main className="flex flex-1 flex-col overflow-y-auto p-6">{children}</main>
    </div>
  )
}
