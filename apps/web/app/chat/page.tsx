"use client"

import { useRef, useState } from "react"
import { Badge } from "@/app/components/badge"
import { Button } from "@/app/components/button"
import { LayoutShell } from "@/app/components/layout-shell"
import { Spinner } from "@/app/components/spinner"
import { Textarea } from "@/app/components/input"

// SSE event shapes emitted by the backend
type SseEvent =
  | { type: "status"; message: string }
  | { type: "token"; content: string }
  | { type: "done"; citations: string[] }
  | { type: "error"; message: string }

interface Message {
  role: "user" | "assistant"
  /** Accumulated answer text; empty while loading. */
  content: string
  citations: string[]
  /** Status events received while navigating (e.g. "Reading concepts/rag…"). */
  statusLog: string[]
  loading: boolean
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [streaming, setStreaming] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  function scrollToBottom() {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const question = input.trim()
    if (!question || streaming) return
    setInput("")
    setStreaming(true)

    // Build history from prior complete messages for the backend
    const history = messages
      .filter((m) => !m.loading)
      .map((m) => ({ role: m.role, content: m.content }))

    // Append user turn and a placeholder assistant turn
    const assistantIdx = messages.length + 1
    setMessages((prev) => [
      ...prev,
      { role: "user", content: question, citations: [], statusLog: [], loading: false },
      { role: "assistant", content: "", citations: [], statusLog: [], loading: true },
    ])
    scrollToBottom()

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, history }),
      })

      if (!response.ok || !response.body) {
        throw new Error(`API error ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { value, done } = await reader.read()
        if (done) break

        const raw = decoder.decode(value, { stream: true })
        // SSE lines: "data: {...}\n\n" — split on double newline
        for (const block of raw.split("\n\n")) {
          const line = block.trim()
          if (!line.startsWith("data: ")) continue
          const event: SseEvent = JSON.parse(line.slice(6))

          setMessages((prev) => {
            const next = [...prev]
            const msg = { ...next[assistantIdx] }

            if (event.type === "status") {
              msg.statusLog = [...msg.statusLog, event.message]
            } else if (event.type === "token") {
              msg.content += event.content
            } else if (event.type === "done") {
              msg.citations = event.citations
              msg.loading = false
            } else if (event.type === "error") {
              msg.content = event.message
              msg.loading = false
            }

            next[assistantIdx] = msg
            return next
          })
          scrollToBottom()
        }
      }
    } catch (err) {
      setMessages((prev) => {
        const next = [...prev]
        next[assistantIdx] = {
          ...next[assistantIdx],
          content: "Something went wrong. Please try again.",
          loading: false,
        }
        return next
      })
    } finally {
      setStreaming(false)
    }
  }

  return (
    <LayoutShell
      sidebar={
        <div className="space-y-2">
          <p className="text-xs font-bold text-brand-emerald uppercase tracking-wider">CoE Wiki</p>
          <nav className="mt-4 space-y-1">
            <a
              href="/chat"
              className="block rounded px-2 py-1 text-xs text-brand-ivory bg-brand-obsidian"
            >
              Chat
            </a>
            <a
              href="/design"
              className="block rounded px-2 py-1 text-xs text-brand-ivory hover:bg-brand-obsidian"
            >
              Design System
            </a>
          </nav>
        </div>
      }
    >
      <div className="flex h-full flex-col">
        {/* Message list */}
        <div className="flex-1 overflow-y-auto space-y-6 pb-4">
          {messages.length === 0 && (
            <div className="flex h-full items-center justify-center">
              <p className="text-sm text-brand-obsidian">
                Ask anything — I&apos;ll navigate the wiki to find an answer.
              </p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-2xl space-y-2 ${msg.role === "user" ? "items-end" : "items-start"} flex flex-col`}>
                {/* Status log (navigation progress) */}
                {msg.statusLog.length > 0 && (
                  <div className="space-y-0.5">
                    {msg.statusLog.map((s, j) => (
                      <p key={j} className="text-2xs text-brand-obsidian italic">
                        {s}
                      </p>
                    ))}
                  </div>
                )}

                {/* Bubble */}
                <div
                  className={[
                    "rounded-lg px-4 py-3 text-sm",
                    msg.role === "user"
                      ? "bg-brand-primary text-brand-white"
                      : "bg-brand-ivory text-brand-abyss ring-1 ring-brand-ivory",
                  ].join(" ")}
                >
                  {msg.loading && !msg.content ? (
                    <Spinner size="sm" label="Thinking…" />
                  ) : (
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  )}
                </div>

                {/* Citations */}
                {msg.citations.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {msg.citations.map((path) => {
                      const parts = path.split("/")
                      const type = parts[0] as "domain" | "concept" | "entity" | "source"
                      return (
                        <a key={path} href={`/wiki/${path}`}>
                          <Badge type={type} label={parts.slice(1).join("/")} />
                        </a>
                      )
                    })}
                  </div>
                )}
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        {/* Input form */}
        <form onSubmit={handleSubmit} className="border-t border-brand-ivory pt-4">
          <div className="flex gap-3 items-end">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question about our AI engineering practices…"
              rows={2}
              className="flex-1"
              // Submit on Enter (without Shift)
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault()
                  handleSubmit(e as unknown as React.FormEvent)
                }
              }}
              disabled={streaming}
            />
            <Button type="submit" disabled={streaming || !input.trim()} size="md">
              {streaming ? <Spinner size="sm" label="Sending…" /> : "Send"}
            </Button>
          </div>
        </form>
      </div>
    </LayoutShell>
  )
}
