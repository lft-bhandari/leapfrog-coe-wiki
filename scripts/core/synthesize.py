from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

import anthropic

_DOMAINS = (
    "gen-ai-fundamentals",
    "retrieval-and-knowledge",
    "agents-and-autonomy",
    "evaluation-and-quality",
    "models-capability-adaptation",
    "security-and-governance",
    "platform-and-operations",
    "classical-ml-deep-learning",
    "general",
)

_SOURCE_SYSTEM = f"""\
You are a wiki editor for a CoE knowledge base. Given a source document, produce a wiki source page in this exact format:

---
type: source
title: <title extracted from the document>
description: <one-sentence summary of the document's main contribution>
sources:
  - raw/<slug>.md
domain: <one of: {", ".join(_DOMAINS)}>
created: <ISO 8601 UTC timestamp>
---

## Summary

<3-7 sentence summary of the document's key claims. Use [[wikilinks]] around every concept, \
entity (tool, framework, standard, organisation), or named technique you mention. \
Wikilinks are the edges of the knowledge graph — be liberal with them.>

Output ONLY the wiki page. No preamble, no explanation."""

_TERM_SYSTEM = """\
You are a wiki editor for a CoE knowledge base. Given a term and the source pages that mention it, \
produce a wiki page in this exact format:

---
type: <"concept" for abstract ideas/techniques, "entity" for named tools/frameworks/organisations>
title: <the term, properly capitalised>
description: <one-sentence definition>
---

## Overview

<3-5 sentences synthesising what this term means across the sources. \
Use [[wikilinks]] to link related concepts and entities mentioned here.>

## Appears in

<bullet list of [[wikilinks]] to each source page that mentions this term>

Output ONLY the wiki page. No preamble, no explanation."""


def make_source_synthesize_fn(client: anthropic.Anthropic) -> Callable[[str, str], str]:
    """Create a synthesize function that produces source wiki pages.

    Args:
        client: Authenticated Anthropic client.

    Returns:
        A callable (content, slug) -> source page markdown.
    """
    def synthesize(content: str, slug: str) -> str:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        user_msg = f"slug: {slug}\ncreated: {now}\n\n---\n\n{content}"
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=2048,
            system=_SOURCE_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        )
        if message.stop_reason != "end_turn":
            raise RuntimeError(
                f"Synthesis truncated (stop_reason={message.stop_reason!r}). "
                "Increase max_tokens or shorten the source document."
            )
        block = message.content[0]
        # content[0] could be a ToolUseBlock or ThinkingBlock on extended models
        if block.type != "text":
            raise RuntimeError(
                f"Expected a text block from the API, got {block.type!r}."
            )
        return block.text

    return synthesize


def make_term_synthesize_fn(client: anthropic.Anthropic) -> Callable[[str, list[str]], str]:
    """Create a synthesize function that produces concept or entity wiki pages.

    The returned callable classifies the term as concept or entity in the
    frontmatter 'type' field — the orchestrator uses that to decide the target directory.

    Args:
        client: Authenticated Anthropic client.

    Returns:
        A callable (term, source_contents) -> concept/entity page markdown.
    """
    def synthesize(term: str, source_contents: list[str]) -> str:
        sources_block = "\n\n---\n\n".join(source_contents)
        user_msg = f"term: {term}\n\n===SOURCE PAGES===\n\n{sources_block}"
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=2048,
            system=_TERM_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        )
        if message.stop_reason != "end_turn":
            raise RuntimeError(
                f"Term synthesis truncated (stop_reason={message.stop_reason!r}). "
                "Increase max_tokens or reduce the number of source pages."
            )
        block = message.content[0]
        # content[0] could be a ToolUseBlock or ThinkingBlock on extended models
        if block.type != "text":
            raise RuntimeError(
                f"Expected a text block from the API, got {block.type!r}."
            )
        return block.text

    return synthesize
