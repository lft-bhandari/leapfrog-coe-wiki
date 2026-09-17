from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from core.wiki_repository import WikiRepository


def _slugify(name: str) -> str:
    """Convert a filename stem to a URL-safe lowercase slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower())
    return slug.strip("-")


def ingest_doc(
    doc_path: Path,
    repo: WikiRepository,
    synthesize_fn: Callable[[str, str], str],
) -> None:
    """Copy the source file to raw/ and write a synthesized source page to sources/.

    Args:
        doc_path: Path to the local markdown file to ingest.
        repo: WikiRepository used for all wiki reads and writes.
        synthesize_fn: Callable that takes (content, slug) and returns a
            wiki source page in markdown with YAML frontmatter.

    Raises:
        ValueError: If a slug cannot be derived from the filename.
    """
    slug = _slugify(doc_path.stem)
    if not slug:
        raise ValueError(f"Cannot derive a slug from filename {doc_path.name!r}")

    content = doc_path.read_text()
    repo.write_raw(slug, content)

    source_page = synthesize_fn(content, slug)
    repo.write_page("sources", slug, source_page)
