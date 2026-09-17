"""Seed concept stub pages for every topic in docs/curriculum.md.

Run once after cloning to populate wiki/concepts/ with stub nodes that
the ingest pipeline will enrich over time. Idempotent: existing pages are
never overwritten.

Usage:
    uv run python seed_curriculum.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from core.build_index import build_index
from core.wiki_repository import FilesystemWikiRepository

_REPO_ROOT = Path(__file__).parent.parent
_CURRICULUM_PATH = _REPO_ROOT / "docs" / "curriculum.md"
_WIKI_DIR = _REPO_ROOT / "wiki"

_DOMAIN_HEADING_RE = re.compile(r"^## (.+)$", re.MULTILINE)
_TOPIC_RE = re.compile(r"^- (.+)$", re.MULTILINE)


def _slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def _parse_curriculum(text: str) -> list[tuple[str, str, list[str]]]:
    """Return list of (domain_slug, domain_title, [topic_title, ...])."""
    sections: list[tuple[str, str, list[str]]] = []
    blocks = _DOMAIN_HEADING_RE.split(text)
    # blocks: [preamble, domain1, topics1, domain2, topics2, ...]
    for i in range(1, len(blocks), 2):
        domain_title = blocks[i].strip()
        topic_block = blocks[i + 1] if i + 1 < len(blocks) else ""
        topics = [m.group(1).strip() for m in _TOPIC_RE.finditer(topic_block)]
        if topics:
            sections.append((_slugify(domain_title), domain_title, topics))
    return sections


def _stub_content(title: str, domain_slug: str) -> str:
    return f"""\
---
type: concept
title: {title}
domain: {domain_slug}
description: Stub page for {title} — to be enriched by ingest.
curriculum_topic: true
---

## Overview

Stub page for **{title}**. This page will be enriched when source documents referencing this topic are ingested.
"""


def seed_curriculum(
    curriculum_path: Path = _CURRICULUM_PATH,
    wiki_dir: Path = _WIKI_DIR,
) -> int:
    """Write concept stubs for every curriculum topic that does not yet exist.

    Args:
        curriculum_path: Path to docs/curriculum.md.
        wiki_dir: Root wiki directory (contains concepts/, etc.).

    Returns:
        Number of new stubs written.
    """
    text = curriculum_path.read_text(encoding="utf-8")
    sections = _parse_curriculum(text)

    repo = FilesystemWikiRepository(wiki_dir)
    written = 0

    for domain_slug, _domain_title, topics in sections:
        for topic_title in topics:
            slug = _slugify(topic_title)
            if repo.page_exists("concepts", slug):
                continue
            repo.write_page("concepts", slug, _stub_content(topic_title, domain_slug))
            written += 1

    build_index(repo)
    return written


def main() -> None:
    n = seed_curriculum()
    print(f"[seed_curriculum] wrote {n} new concept stub(s).")


if __name__ == "__main__":
    sys.exit(main())
