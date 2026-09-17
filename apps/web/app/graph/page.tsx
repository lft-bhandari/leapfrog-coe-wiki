"use client"

import { useCallback, useEffect, useState } from "react"
import {
  Background,
  Controls,
  type Edge,
  type Node,
  type NodeMouseHandler,
  ReactFlow,
  useEdgesState,
  useNodesState,
} from "@xyflow/react"
import "@xyflow/react/dist/style.css"
import type { CSSProperties } from "react"
import { Badge } from "@/app/components/badge"
import { Button } from "@/app/components/button"
import { Card } from "@/app/components/card"
import { LayoutShell } from "@/app/components/layout-shell"
import { SideNav } from "@/app/components/side-nav"
import { Spinner } from "@/app/components/spinner"
import { TextInput } from "@/app/components/input"

// ── Types ────────────────────────────────────────────────────────────────────

type NodeType = "domain" | "concept" | "entity" | "source"

interface WikiNode {
  id: string
  type: NodeType
  label: string
}

interface WikiEdge {
  source: string
  target: string
}

interface GraphData {
  nodes: WikiNode[]
  edges: WikiEdge[]
}

interface WikiPageData {
  path: string
  title: string
  content: string
}

// ── Visual config ─────────────────────────────────────────────────────────────

// Colors match brand tokens from globals.css. Hex values are used here because
// React Flow inline styles cannot consume Tailwind class names.
const NODE_COLORS: Record<NodeType, { bg: string; text: string; border: string }> = {
  domain:  { bg: "#038E43", text: "#FFFFFF", border: "#026832" },
  concept: { bg: "#B4FFD6", text: "#111111", border: "#00DF66" },
  entity:  { bg: "#FFD700", text: "#111111", border: "#e6c200" },
  source:  { bg: "#D9D9D9", text: "#333333", border: "#bbbbbb" },
}

const NODE_SIZES: Record<NodeType, { width: number; fontSize: number; padding: string }> = {
  domain:  { width: 140, fontSize: 13, padding: "10px 14px" },
  concept: { width: 110, fontSize: 11, padding: "6px 10px" },
  entity:  { width: 110, fontSize: 11, padding: "6px 10px" },
  source:  { width: 100, fontSize: 10, padding: "5px 8px" },
}

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Runtime guard: returns the string as NodeType if valid, else "source". */
function toNodeType(raw: string): NodeType {
  if (raw === "domain" || raw === "concept" || raw === "entity" || raw === "source") return raw
  return "source"
}

function toFlowNodes(
  wikiNodes: WikiNode[],
  dimmed: Set<string>,
  highlighted: Set<string>,
): Node[] {
  const domains = wikiNodes.filter((n) => n.type === "domain")
  const rest = wikiNodes.filter((n) => n.type !== "domain")

  const R = 340
  const positions: Record<string, { x: number; y: number }> = {}

  domains.forEach((n, i) => {
    const angle = (2 * Math.PI * i) / domains.length - Math.PI / 2
    positions[n.id] = { x: R * Math.cos(angle), y: R * Math.sin(angle) }
  })

  rest.forEach((n, i) => {
    const angle = (2 * Math.PI * i) / rest.length
    const r = R * 1.8 + (i % 3) * 80
    positions[n.id] = { x: r * Math.cos(angle), y: r * Math.sin(angle) }
  })

  return wikiNodes.map((n) => {
    const pos = positions[n.id] ?? { x: 0, y: 0 }
    const colors = NODE_COLORS[n.type]
    const sizes = NODE_SIZES[n.type]
    const isDimmed = dimmed.size > 0 && !highlighted.has(n.id)
    const isHighlighted = highlighted.has(n.id)

    const style: CSSProperties = {
      background: colors.bg,
      color: colors.text,
      border: isHighlighted
        ? `3px solid #111111`  // dark ring marks search matches
        : `2px solid ${colors.border}`,
      borderRadius: 8,
      width: sizes.width,
      fontSize: sizes.fontSize,
      padding: sizes.padding,
      fontWeight: n.type === "domain" ? 700 : 400,
      opacity: isDimmed ? 0.2 : 1,
      transition: "opacity 0.2s, border 0.2s",
      cursor: "pointer",
      textAlign: "center",
    }

    return { id: n.id, position: pos, data: { label: n.label, nodeType: n.type }, style }
  })
}

function toFlowEdges(wikiEdges: WikiEdge[], dimmed: Set<string>): Edge[] {
  return wikiEdges.map((e, i) => ({
    id: `e${i}`,
    source: e.source,
    target: e.target,
    style: {
      opacity: dimmed.size > 0 && (!dimmed.has(e.source) || !dimmed.has(e.target))
        ? 0.08
        : 0.4,
      stroke: "#333",
    },
    animated: false,
  }))
}

// ── Node panel ────────────────────────────────────────────────────────────────

function NodePanel({
  nodeId,
  nodeType,
  onClose,
}: {
  nodeId: string
  nodeType: NodeType
  onClose: () => void
}) {
  const [page, setPage] = useState<WikiPageData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    setPage(null)
    const path = nodeId.replace(/\/index$/, "")
    fetch(`/api/wiki/${path}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data: WikiPageData | null) => { setPage(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [nodeId])

  const chatPath = `/chat?topic=${encodeURIComponent(page?.title ?? nodeId)}`
  const displayLabel = nodeId.split("/").at(-1) ?? nodeId

  return (
    <div className="w-80 shrink-0 flex flex-col gap-4 border-l border-brand-ivory bg-brand-white p-5 overflow-y-auto">
      <div className="flex items-start justify-between gap-2">
        <div className="space-y-1">
          <Badge type={nodeType} />
          <h2 className="text-md font-bold text-brand-abyss leading-snug">
            {page?.title ?? displayLabel}
          </h2>
        </div>
        <button
          onClick={onClose}
          className="mt-0.5 text-brand-obsidian hover:text-brand-abyss text-lg leading-none"
          aria-label="Close panel"
        >
          ×
        </button>
      </div>

      {loading && <Spinner size="sm" label="Loading page…" />}

      {!loading && page && (
        <Card bordered>
          <p className="text-xs text-brand-obsidian leading-relaxed whitespace-pre-wrap">
            {page.content}
          </p>
        </Card>
      )}

      {!loading && !page && (
        <p className="text-xs text-brand-obsidian italic">No wiki page found for this node.</p>
      )}

      <div className="flex flex-col gap-2 mt-auto pt-4 border-t border-brand-ivory">
        {page && (
          <a href={`/wiki/${nodeId.replace(/\/index$/, "")}`}>
            <Button variant="secondary" size="sm" className="w-full">
              Read full page
            </Button>
          </a>
        )}
        <a href={chatPath}>
          <Button variant="ghost" size="sm" className="w-full">
            Chat about this →
          </Button>
        </a>
      </div>
    </div>
  )
}

// ── Main graph page ───────────────────────────────────────────────────────────

function GraphPage() {
  const [graphData, setGraphData] = useState<GraphData | null>(null)
  const [loadError, setLoadError] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [search, setSearch] = useState("")
  const [selectedNode, setSelectedNode] = useState<{ id: string; type: NodeType } | null>(null)

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])

  const loadGraph = useCallback(async () => {
    setRefreshing(true)
    try {
      // cache: "no-store" bypasses Next.js route-handler ISR so the user always
      // gets a fresh graph when they click Refresh
      const res = await fetch("/api/graph", { cache: "no-store" })
      if (!res.ok) throw new Error()
      const data: GraphData = await res.json()
      setGraphData(data)
    } catch {
      setLoadError(true)
    } finally {
      setRefreshing(false)
    }
  }, [])

  useEffect(() => { loadGraph() }, [loadGraph])

  useEffect(() => {
    if (!graphData) return

    const q = search.trim().toLowerCase()
    const highlighted = new Set<string>()
    const dimmed = new Set<string>()

    if (q) {
      graphData.nodes.forEach((n) => {
        if (n.label.toLowerCase().includes(q) || n.id.toLowerCase().includes(q)) {
          highlighted.add(n.id)
        } else {
          dimmed.add(n.id)
        }
      })
    }

    setNodes(toFlowNodes(graphData.nodes, dimmed, highlighted))
    setEdges(toFlowEdges(graphData.edges, dimmed))
  }, [graphData, search, setNodes, setEdges])

  const onNodeClick: NodeMouseHandler = useCallback((_event, node) => {
    const wikiNode = graphData?.nodes.find((n) => n.id === node.id)
    if (wikiNode) setSelectedNode({ id: wikiNode.id, type: wikiNode.type })
  }, [graphData])

  return (
    <LayoutShell
      sidebar={
        <>
          <SideNav active="graph" />
          <div className="mt-8 space-y-2">
            <p className="text-2xs font-bold text-brand-ivory uppercase tracking-wider">Legend</p>
            {(["domain", "concept", "entity", "source"] as NodeType[]).map((t) => (
              <div key={t} className="flex items-center gap-2">
                <span
                  className="h-3 w-3 rounded-sm shrink-0"
                  style={{ background: NODE_COLORS[t].bg, border: `1px solid ${NODE_COLORS[t].border}` }}
                />
                <span className="text-2xs text-brand-ivory capitalize">{t}</span>
              </div>
            ))}
          </div>
        </>
      }
    >
      <div className="flex h-full gap-0">
        <div className="flex flex-1 flex-col gap-3">
          <div className="flex items-center gap-3 shrink-0">
            <TextInput
              placeholder="Search nodes…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="max-w-xs"
            />
            <Button variant="secondary" size="sm" onClick={loadGraph} disabled={refreshing}>
              {refreshing ? <Spinner size="sm" label="Refreshing…" /> : "Refresh"}
            </Button>
            {graphData && (
              <span className="text-2xs text-brand-obsidian">
                {graphData.nodes.length} nodes · {graphData.edges.length} edges
              </span>
            )}
          </div>

          <div className="flex-1 rounded-lg border border-brand-ivory overflow-hidden">
            {loadError && (
              <div className="flex h-full items-center justify-center">
                <p className="text-sm text-brand-obsidian">Could not load graph. Is the API running?</p>
              </div>
            )}
            {!loadError && !graphData && (
              <div className="flex h-full items-center justify-center">
                <Spinner size="lg" label="Loading graph…" />
              </div>
            )}
            {!loadError && graphData && (
              <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeClick={onNodeClick}
                fitView
                fitViewOptions={{ padding: 0.15 }}
                minZoom={0.2}
                maxZoom={2}
                proOptions={{ hideAttribution: true }}
              >
                <Background color="#D9D9D9" gap={20} />
                <Controls />
              </ReactFlow>
            )}
          </div>
        </div>

        {selectedNode && (
          <NodePanel
            nodeId={selectedNode.id}
            nodeType={selectedNode.type}
            onClose={() => setSelectedNode(null)}
          />
        )}
      </div>
    </LayoutShell>
  )
}

export default GraphPage
