type NodeType = "domain" | "concept" | "entity" | "source"

const NODE_TYPE_CLASSES: Record<NodeType, string> = {
  domain: "bg-brand-primary text-brand-white",
  concept: "bg-brand-mint text-brand-abyss",
  entity: "bg-brand-gold text-brand-abyss",
  source: "bg-brand-ivory text-brand-obsidian",
}

interface BadgeProps {
  type: NodeType
  label?: string
}

/** Label chip for wiki node types: domain, concept, entity, source. */
export function Badge({ type, label }: BadgeProps) {
  return (
    <span
      className={[
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-2xs font-normal",
        NODE_TYPE_CLASSES[type],
      ].join(" ")}
    >
      {label ?? type}
    </span>
  )
}
