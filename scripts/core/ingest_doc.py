from __future__ import annotations

from pathlib import Path
from typing import Callable

from core.slug import slugify
from core.wiki_repository import WikiRepository


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
    slug = slugify(doc_path.stem)
    if not slug:
        raise ValueError(f"Cannot derive a slug from filename {doc_path.name!r}")

    content = doc_path.read_text()
    source_page = synthesize_fn(content, slug)
    # Validate before any writes so a bad synthesis never leaves an orphaned raw file.
    if not source_page.startswith('---'):
        raise ValueError(
            f'Synthesis for {slug!r} returned no YAML frontmatter. '
            'Check SYNTHESIS_BACKEND / OLLAMA_MODEL and retry.'
        )
    repo.write_raw(slug, content)
    repo.write_page('sources', slug, source_page)
