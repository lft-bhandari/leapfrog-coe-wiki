from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from core.chat_backends import ChatFn

_CURRICULUM_PATH = Path(__file__).parent.parent.parent / "docs" / "curriculum.md"


def _load_curriculum_topics(path: Path = _CURRICULUM_PATH) -> list[str]:
    """Extract all topic titles from docs/curriculum.md.

    Returns an empty list if the file does not exist, so the module is importable
    without the docs directory present (e.g. in isolated test environments).
    """
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    return [m.group(1).strip() for m in re.finditer(r"^- (.+)$", text, re.MULTILINE)]


_CURRICULUM_TOPICS: list[str] = _load_curriculum_topics()
_CURRICULUM_VOCAB = ", ".join(_CURRICULUM_TOPICS) if _CURRICULUM_TOPICS else "(none loaded)"

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
entities:
  - "[[NamedTool]]"
concepts:
  - "[[abstract-technique]]"
---

## Summary

<3-7 sentence summary of the document's key claims. Use [[wikilinks]] around every concept, \
entity (tool, framework, standard, organisation), or named technique you mention. \
Wikilinks are the edges of the knowledge graph — be liberal with them.>

Rules for the frontmatter arrays:
- entities: named tools, frameworks, organisations, or standards mentioned in the document. \
  Use exact proper-noun capitalisation as the wikilink target. Write `entities: []` if none apply.
- concepts: abstract techniques or ideas mentioned. \
  Prefer these canonical curriculum topic names where they apply: {_CURRICULUM_VOCAB}. \
  Use lower-case-hyphenated wikilink targets. Write `concepts: []` if none apply.

Output ONLY the wiki page. No preamble, no explanation."""

_TERM_SYSTEM = f"""\
You are a wiki editor for a CoE knowledge base. Given a term and the source pages that mention it, \
produce a wiki page in this exact format:

---
type: <"concept" for abstract ideas/techniques, "entity" for named tools/frameworks/organisations>
title: <the term, properly capitalised>
description: <one-sentence definition>
---

## Overview

<3-5 sentences synthesising what this term means across the sources. \
Use [[wikilinks]] to link related concepts and entities mentioned here. \
Prefer these canonical concept names where they apply: {_CURRICULUM_VOCAB}.>

## Appears in

<bullet list of [[wikilinks]] to each source page that mentions this term>

Output ONLY the wiki page. No preamble, no explanation."""


def make_source_synthesize_fn(chat_fn: ChatFn) -> Callable[[str, str], str]:
    """Create a synthesize function that produces source wiki pages.

    Args:
        chat_fn: Backend callable (system_prompt, user_message) -> reply.

    Returns:
        A callable (content, slug) -> source page markdown.
    """
    def synthesize(content: str, slug: str) -> str:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        user_msg = f"slug: {slug}\ncreated: {now}\n\n---\n\n{content}"
        reply = chat_fn(_SOURCE_SYSTEM, user_msg)
        # Strip any preamble the model added before the frontmatter opener.
        idx = reply.find('---')
        return reply[idx:] if idx != -1 else reply

    return synthesize


def make_term_synthesize_fn(chat_fn: ChatFn) -> Callable[[str, list[str]], str]:
    """Create a synthesize function that produces concept or entity wiki pages.

    The returned callable classifies the term as concept or entity in the
    frontmatter 'type' field — the orchestrator uses that to decide the target directory.

    Args:
        chat_fn: Backend callable (system_prompt, user_message) -> reply.

    Returns:
        A callable (term, source_contents) -> concept/entity page markdown.
    """
    def synthesize(term: str, source_contents: list[str]) -> str:
        sources_block = "\n\n---\n\n".join(source_contents)
        user_msg = f"term: {term}\n\n===SOURCE PAGES===\n\n{sources_block}"
        reply = chat_fn(_TERM_SYSTEM, user_msg)
        idx = reply.find('---')
        return reply[idx:] if idx != -1 else reply

    return synthesize
