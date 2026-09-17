from __future__ import annotations

import asyncio
import json
import re
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Callable, TypedDict

import httpx2

_READ_RE = re.compile(r"^READ:\s*(.+)$", re.MULTILINE)
_ANSWER_RE = re.compile(r"^ANSWER:\s*(.+?)(?=\nCITATIONS:|$)", re.MULTILINE | re.DOTALL)
_CITATIONS_RE = re.compile(r"^CITATIONS:\s*(.*)$", re.MULTILINE)

_SYSTEM_PROMPT = """\
You are a wiki navigator for a company knowledge base. Answer the user's question \
by progressively reading wiki pages.

To read a page, respond ONLY with (one page at a time):
READ: <page-path>

For example: READ: concepts/rag

When you have enough information to answer, respond with:
ANSWER: <your answer>
CITATIONS: <comma-separated page paths you read, or leave blank if none>

Never invent information not in the wiki. If the wiki has no relevant content, \
say so explicitly in your ANSWER."""


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


def navigate_and_answer(
    question: str,
    history: list[dict[str, str]],
    wiki_dir: Path,
    chat_fn: Callable[[list[dict[str, str]]], str],
    max_steps: int = 10,
) -> ChatResponse:
    """Navigate the wiki progressively to answer a question.

    Starts at wiki/index.md and follows LLM-requested page reads until the
    LLM produces a final ANSWER, or max_steps is reached.

    Args:
        question: The user's question.
        history: Prior conversation turns (OpenAI-style message dicts).
        wiki_dir: Root wiki directory containing index.md and page subdirs.
        chat_fn: Callable that takes a message list and returns the LLM reply.
        max_steps: Maximum READ hops before forcing a stop.

    Returns:
        ChatResponse with 'answer' text and 'citations' list of verified page paths.
    """
    index_path = wiki_dir / "index.md"
    index_content = index_path.read_text(encoding="utf-8") if index_path.exists() else "(no index)"

    pages_read: list[str] = []
    # Accumulate page contents fetched during navigation for context
    page_context = f"Root wiki index:\n{index_content}"

    messages: list[dict[str, str]] = [{"role": "system", "content": _SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": f"Question: {question}\n\n{page_context}"})

    for _ in range(max_steps):
        reply = chat_fn(messages)

        read_match = _READ_RE.search(reply)
        if read_match:
            page_path = read_match.group(1).strip().removesuffix(".md")
            page_file = wiki_dir / f"{page_path}.md"
            if page_file.exists():
                content = page_file.read_text(encoding="utf-8")
                pages_read.append(page_path)
                page_context = f"Page {page_path}:\n{content}"
            else:
                # Inform the LLM the page doesn't exist so it can try another route
                page_context = f"Page {page_path}: (not found)"
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content": page_context})
            continue

        answer_match = _ANSWER_RE.search(reply)
        if answer_match:
            answer = answer_match.group(1).strip()
            citations = _resolve_citations(pages_read, reply, wiki_dir)
            return ChatResponse(answer=answer, citations=citations)

        # Unrecognised reply format — treat as final answer
        return ChatResponse(answer=reply.strip(), citations=pages_read)

    return ChatResponse(
        answer="I was unable to find a definitive answer in the wiki after navigating several pages.",
        citations=pages_read,
    )


async def stream_navigate_and_answer(
    question: str,
    history: list[dict[str, str]],
    wiki_dir: Path,
    chat_fn: Callable[[list[dict[str, str]]], str],
    model: str = "llama3.2:3b",
    base_url: str = "http://localhost:11434",
    max_steps: int = 10,
) -> AsyncGenerator[str, None]:
    """Async generator that yields SSE events for progressive wiki navigation.

    Yields status events while navigating, then streams the final answer word by word,
    and ends with a citations event. Designed for use with FastAPI StreamingResponse.

    Args:
        question: The user's question.
        history: Prior conversation turns.
        wiki_dir: Root wiki directory.
        chat_fn: Callable for navigation-step LLM calls (non-streaming).
        model: Ollama model name for the streaming final-answer call.
        base_url: Ollama API base URL.
        max_steps: Maximum READ hops.

    Yields:
        SSE-formatted strings: status, token, done, or error event lines.
    """
    index_path = wiki_dir / "index.md"
    index_content = index_path.read_text(encoding="utf-8") if index_path.exists() else "(no index)"

    pages_read: list[str] = []
    page_context = f"Root wiki index:\n{index_content}"

    messages: list[dict[str, str]] = [{"role": "system", "content": _SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": f"Question: {question}\n\n{page_context}"})

    final_reply: str | None = None

    for _ in range(max_steps):
        reply = chat_fn(messages)

        read_match = _READ_RE.search(reply)
        if read_match:
            page_path = read_match.group(1).strip().removesuffix(".md")
            page_file = wiki_dir / f"{page_path}.md"
            yield _sse({"type": "status", "message": f"Reading {page_path}…"})
            if page_file.exists():
                content = page_file.read_text(encoding="utf-8")
                pages_read.append(page_path)
                page_context = f"Page {page_path}:\n{content}"
            else:
                page_context = f"Page {page_path}: (not found)"
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content": page_context})
            continue

        final_reply = reply
        break

    if final_reply is None:
        final_reply = (
            "ANSWER: I was unable to find a definitive answer in the wiki.\nCITATIONS:"
        )

    answer_match = _ANSWER_RE.search(final_reply)
    answer_text = answer_match.group(1).strip() if answer_match else final_reply.strip()

    # Stream the answer word by word via Ollama streaming for natural token pacing
    try:
        answer_messages = messages + [
            {"role": "assistant", "content": final_reply},
            {"role": "user", "content": "Now write out the answer clearly for the user."},
        ]
        # Use run_in_executor to avoid blocking the event loop during the HTTP stream
        streamed_answer = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: _stream_ollama_tokens(answer_messages, model, base_url),
        )
        for token in streamed_answer:
            yield _sse({"type": "token", "content": token})
            await asyncio.sleep(0)  # yield control between tokens
    except Exception:
        # Fall back to word-by-word reveal of the already-complete answer text
        for word in answer_text.split():
            yield _sse({"type": "token", "content": word + " "})
            await asyncio.sleep(0.02)

    citations = _resolve_citations(pages_read, final_reply, wiki_dir)
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
            if data.get("done"):
                break
            token = data.get("message", {}).get("content", "")
            if token:
                tokens.append(token)
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
