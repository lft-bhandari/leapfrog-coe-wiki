from __future__ import annotations

import asyncio
import json
import os
import re
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Callable, TypedDict

import httpx2

_ANSWER_RE = re.compile(r"^ANSWER:\s*(.+?)(?=\nCITATIONS:|$)", re.MULTILINE | re.DOTALL)
_CITATIONS_RE = re.compile(r"^CITATIONS:\s*(.*)$", re.MULTILINE)

_SYSTEM_PROMPT = """\
You are a wiki assistant for a company knowledge base. You will be given the full \
contents of relevant wiki pages as context. Answer the user's question using ONLY \
the provided wiki content.

You MUST respond in this exact format:
ANSWER: <your detailed answer based on the wiki content>
CITATIONS: <comma-separated page paths from the context that you used>

Rules:
- Use only information from the wiki pages provided. Do not invent information.
- If the wiki has no relevant content, say so in ANSWER and leave CITATIONS blank.
- Always include ANSWER: and CITATIONS: labels exactly as shown."""


class ChatResponse(TypedDict):
    answer: str
    citations: list[str]


def _sse(event: dict) -> str:
    """Format a dict as a Server-Sent Event line."""
    return f"data: {json.dumps(event)}\n\n"


def _resolve_citations(
    pages_read: list[str],
    llm_reply: str,
    wiki_dir: Path,
) -> list[str]:
    """Merge navigation trail with validated LLM-declared citations."""
    citations_match = _CITATIONS_RE.search(llm_reply)
    raw = citations_match.group(1).strip() if citations_match else ""
    llm_citations = [c.strip() for c in raw.split(",") if c.strip()]
    # Hallucinated paths that don't exist on disk are dropped
    valid = [c for c in llm_citations if (wiki_dir / f"{c}.md").exists()]
    return list(dict.fromkeys(pages_read + valid))


def _load_wiki_context(wiki_dir: Path, question: str, max_pages: int = 6) -> tuple[str, list[str]]:
    """Load wiki pages most relevant to the question as a flat context block.

    Scores pages by keyword overlap with the question, returns the top-N as a
    combined context string and the list of their relative paths.

    Args:
        wiki_dir: Root wiki directory.
        question: The user's question (used for relevance scoring).
        max_pages: Maximum number of pages to include.

    Returns:
        Tuple of (context_string, list_of_page_paths).
    """
    keywords = set(re.sub(r"[^\w\s]", "", question.lower()).split()) - {
        "what", "is", "are", "how", "why", "does", "the", "a", "an", "tell", "me", "about",
    }

    candidates: list[tuple[int, str, str]] = []
    for md_file in wiki_dir.rglob("*.md"):
        rel = md_file.relative_to(wiki_dir).with_suffix("").as_posix()
        # Skip raw/ (unprocessed sources) and the root index
        if rel.startswith("raw/") or rel == "index":
            continue
        content = md_file.read_text(encoding="utf-8")
        text_lower = content.lower()
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            candidates.append((score, rel, content))

    candidates.sort(key=lambda x: x[0], reverse=True)
    top = candidates[:max_pages]

    if not top:
        # Fall back: include all source pages if no keyword match
        for md_file in (wiki_dir / "sources").glob("*.md"):
            rel = md_file.relative_to(wiki_dir).with_suffix("").as_posix()
            content = md_file.read_text(encoding="utf-8")
            top.append((0, rel, content))
        top = top[:max_pages]

    parts = [f"=== {rel} ===\n{content}" for _, rel, content in top]
    paths = [rel for _, rel, _ in top]
    return "\n\n".join(parts), paths


_WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")

_NAV_SYSTEM = """\
You are navigating a wiki to answer a question. At each step you see the question, \
a list of pages you can read next, and a summary of pages already read.

Respond with exactly one JSON object — no other text:
{"action": "read", "path": "<one path from the available list>"}
or
{"action": "answer"}

Choose "read" to open a page from the provided list. \
Choose "answer" when you have enough context to answer, or if no listed page looks relevant. \
You cannot invent paths — only choose from the provided list."""


def _extract_wikilinks(content: str) -> list[str]:
    """Return all wikilink targets in content order (deduped, preserving first occurrence)."""
    seen: dict[str, None] = {}
    for m in _WIKILINK_RE.finditer(content):
        seen.setdefault(m.group(1), None)
    return list(seen)


def navigate_and_answer_v2(
    question: str,
    history: list[dict[str, str]],
    wiki_dir: Path,
    chat_fn: Callable[[list[dict[str, str]]], str],
    max_steps: int = 8,
) -> ChatResponse:
    """LLM-guided hop-by-hop wiki traversal starting from wiki/index.md.

    Each iteration the LLM chooses one wikilink from the current page to follow,
    or signals it is ready to answer. The LLM cannot invent paths — it may only
    select from the links present in the current page. Circular wikilinks are
    skipped, missing pages are skipped gracefully.

    Args:
        question: The user's question.
        history: Prior conversation turns.
        wiki_dir: Root wiki directory containing index.md and page subdirs.
        chat_fn: Callable for both navigation decisions and the final answer.
        max_steps: Maximum hops before forcing the answer phase.

    Returns:
        ChatResponse with 'answer' text and 'citations' list of verified page paths.
    """
    index_path = wiki_dir / "index.md"
    current_content = index_path.read_text(encoding="utf-8") if index_path.exists() else ""

    visited: set[str] = {"index"}
    pages_read: list[str] = []
    page_contexts: list[str] = [f"=== index ===\n{current_content}"]

    for _ in range(max_steps):
        available = [
            p for p in _extract_wikilinks(current_content)
            if p not in visited and (wiki_dir / f"{p}.md").exists()
        ]

        nav_messages: list[dict[str, str]] = [{"role": "system", "content": _NAV_SYSTEM}]
        nav_messages.append({
            "role": "user",
            "content": (
                f"Question: {question}\n\n"
                f"Available paths:\n"
                + ("\n".join(f"- {p}" for p in available) or "(none)")
                + f"\n\nPages read so far: "
                + (", ".join(pages_read) or "(none)")
            ),
        })

        try:
            raw = chat_fn(nav_messages)
            decision = json.loads(raw.strip())
        except (json.JSONDecodeError, ValueError):
            break

        if decision.get("action") == "answer":
            break

        if decision.get("action") == "read":
            chosen = str(decision.get("path", "")).strip().removesuffix(".md")
            if chosen not in available:
                # Bad LLM pick — continue so next iteration can recover
                continue
            current_content = (wiki_dir / f"{chosen}.md").read_text(encoding="utf-8")
            visited.add(chosen)
            pages_read.append(chosen)
            page_contexts.append(f"=== {chosen} ===\n{current_content}")
        else:
            break

    # Final answer: pass accumulated context to the standard answer prompt
    context = "\n\n".join(page_contexts)
    user_content = f"Question: {question}\n\nWiki pages:\n\n{context}"
    messages: list[dict[str, str]] = [{"role": "system", "content": _SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_content})

    reply = chat_fn(messages)
    answer_match = _ANSWER_RE.search(reply)
    answer = answer_match.group(1).strip() if answer_match else reply.strip()
    citations = _resolve_citations(pages_read, reply, wiki_dir)
    return ChatResponse(answer=answer, citations=citations)


def navigate_and_answer(
    question: str,
    history: list[dict[str, str]],
    wiki_dir: Path,
    chat_fn: Callable[[list[dict[str, str]]], str],
    max_steps: int = 10,
) -> ChatResponse:
    """Answer a question using pre-loaded wiki context.

    Loads the most relevant wiki pages by keyword match and sends them as
    context to the LLM in a single call, rather than navigating hop-by-hop.

    Args:
        question: The user's question.
        history: Prior conversation turns (OpenAI-style message dicts).
        wiki_dir: Root wiki directory containing index.md and page subdirs.
        chat_fn: Callable that takes a message list and returns the LLM reply.
        max_steps: Unused; kept for API compatibility.

    Returns:
        ChatResponse with 'answer' text and 'citations' list of verified page paths.
    """
    if os.environ.get("WIKI_NAV") == "graph":
        return navigate_and_answer_v2(question, history, wiki_dir, chat_fn, max_steps)

    context, pages_loaded = _load_wiki_context(wiki_dir, question)
    user_content = f"Question: {question}\n\nWiki pages:\n\n{context}"

    messages: list[dict[str, str]] = [{"role": "system", "content": _SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_content})

    reply = chat_fn(messages)

    answer_match = _ANSWER_RE.search(reply)
    answer = answer_match.group(1).strip() if answer_match else reply.strip()
    citations = _resolve_citations(pages_loaded, reply, wiki_dir)
    return ChatResponse(answer=answer, citations=citations)


async def stream_navigate_and_answer(
    question: str,
    history: list[dict[str, str]],
    wiki_dir: Path,
    chat_fn: Callable[[list[dict[str, str]]], str],
    model: str = "llama3.2:3b",
    base_url: str = "http://localhost:11434",
    max_steps: int = 10,
) -> AsyncGenerator[str, None]:
    """Async generator that yields SSE events for a wiki-context-grounded answer.

    Loads relevant wiki pages by keyword match, streams the answer token by token,
    and ends with a citations event.

    Args:
        question: The user's question.
        history: Prior conversation turns.
        wiki_dir: Root wiki directory.
        chat_fn: Unused; kept for API compatibility.
        model: Ollama model name for streaming.
        base_url: Ollama API base URL.
        max_steps: Unused; kept for API compatibility.

    Yields:
        SSE-formatted strings: status, token, done, or error event lines.
    """
    if os.environ.get("WIKI_NAV") == "graph":
        async for event in stream_navigate_and_answer_v2(
            question, history, wiki_dir, chat_fn, model, base_url, max_steps
        ):
            yield event
        return

    yield _sse({"type": "status", "message": "Searching wiki…"})

    context, pages_loaded = _load_wiki_context(wiki_dir, question)
    for path in pages_loaded:
        yield _sse({"type": "status", "message": f"Reading {path}…"})

    user_content = f"Question: {question}\n\nWiki pages:\n\n{context}"
    messages: list[dict[str, str]] = [{"role": "system", "content": _SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_content})

    collected_tokens: list[str] = []
    try:
        streamed_tokens = await asyncio.get_running_loop().run_in_executor(
            None,
            lambda: _stream_ollama_tokens(messages, model, base_url),
        )
        for token in streamed_tokens:
            collected_tokens.append(token)
            yield _sse({"type": "token", "content": token})
            await asyncio.sleep(0)
    except Exception as exc:
        yield _sse({"type": "error", "message": f"Streaming failed: {exc}"})
        return

    full_reply = "".join(collected_tokens)
    citations = _resolve_citations(pages_loaded, full_reply, wiki_dir)
    yield _sse({"type": "done", "citations": citations})


async def stream_navigate_and_answer_v2(
    question: str,
    history: list[dict[str, str]],
    wiki_dir: Path,
    chat_fn: Callable[[list[dict[str, str]]], str],
    model: str = "llama3.2:3b",
    base_url: str = "http://localhost:11434",
    max_steps: int = 8,
) -> AsyncGenerator[str, None]:
    """Async generator for LLM-guided graph traversal, yielding SSE events.

    Mirrors navigate_and_answer_v2 but emits status events for each hop and
    streams the final answer token by token via Ollama.
    """
    yield _sse({"type": "status", "message": "Reading index…"})

    index_path = wiki_dir / "index.md"
    current_content = index_path.read_text(encoding="utf-8") if index_path.exists() else ""

    visited: set[str] = {"index"}
    pages_read: list[str] = []
    page_contexts: list[str] = [f"=== index ===\n{current_content}"]

    loop = asyncio.get_running_loop()

    for _ in range(max_steps):
        available = [
            p for p in _extract_wikilinks(current_content)
            if p not in visited and (wiki_dir / f"{p}.md").exists()
        ]

        nav_messages: list[dict[str, str]] = [{"role": "system", "content": _NAV_SYSTEM}]
        nav_messages.append({
            "role": "user",
            "content": (
                f"Question: {question}\n\n"
                f"Available paths:\n"
                + ("\n".join(f"- {p}" for p in available) or "(none)")
                + f"\n\nPages read so far: "
                + (", ".join(pages_read) or "(none)")
            ),
        })

        try:
            raw = await loop.run_in_executor(
                None, lambda msgs=nav_messages: chat_fn(msgs)
            )
            decision = json.loads(raw.strip())
        except Exception:
            # JSON parse error or HTTP failure from chat_fn — stop navigation
            break

        if decision.get("action") == "answer":
            break

        if decision.get("action") == "read":
            chosen = str(decision.get("path", "")).strip().removesuffix(".md")
            if chosen not in available:
                continue
            current_content = (wiki_dir / f"{chosen}.md").read_text(encoding="utf-8")
            visited.add(chosen)
            pages_read.append(chosen)
            page_contexts.append(f"=== {chosen} ===\n{current_content}")
            yield _sse({"type": "status", "message": f"Reading {chosen}…"})
        else:
            break

    context = "\n\n".join(page_contexts)
    user_content = f"Question: {question}\n\nWiki pages:\n\n{context}"
    messages: list[dict[str, str]] = [{"role": "system", "content": _SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_content})

    collected_tokens: list[str] = []
    try:
        streamed_tokens = await loop.run_in_executor(
            None,
            lambda: _stream_ollama_tokens(messages, model, base_url),
        )
        for token in streamed_tokens:
            collected_tokens.append(token)
            yield _sse({"type": "token", "content": token})
            await asyncio.sleep(0)
    except Exception as exc:
        yield _sse({"type": "error", "message": f"Streaming failed: {exc}"})
        return

    full_reply = "".join(collected_tokens)
    citations = _resolve_citations(pages_read, full_reply, wiki_dir)
    yield _sse({"type": "done", "citations": citations})


def _stream_ollama_tokens(
    messages: list[dict[str, str]],
    model: str,
    base_url: str,
) -> list[str]:
    """Collect streaming tokens from Ollama synchronously (called via executor).

    Returns a list of token strings from the streaming response.
    """
    tokens: list[str] = []
    with httpx2.stream(
        "POST",
        f"{base_url}/api/chat",
        json={"model": model, "messages": messages, "stream": True},
        timeout=120.0,
    ) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line:
                continue
            data = json.loads(line)
            token = data.get("message", {}).get("content", "")
            if token:
                tokens.append(token)
            if data.get("done"):
                break
    return tokens


def make_ollama_fn(
    model: str = "llama3.2:3b",
    base_url: str = "http://localhost:11434",
) -> Callable[[list[dict[str, str]]], str]:
    """Factory that returns a chat callable backed by a local Ollama instance.

    Args:
        model: Ollama model name to use.
        base_url: Base URL of the Ollama API server.

    Returns:
        A callable that accepts a message list and returns the LLM reply string.

    Raises:
        httpx2.HTTPStatusError: If the Ollama API returns a non-2xx status.
    """
    def _chat(messages: list[dict[str, str]]) -> str:
        response = httpx2.post(
            f"{base_url}/api/chat",
            json={"model": model, "messages": messages, "stream": False},
            timeout=120.0,
        )
        response.raise_for_status()
        return response.json()["message"]["content"]

    return _chat
