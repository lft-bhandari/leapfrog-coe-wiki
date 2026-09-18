from __future__ import annotations

from pathlib import Path
from typing import Callable

from core.chat_backends import ChatFn
from core.metadata import DocMetadata, extract_metadata
from core.preprocess import split_sections, strip_images
from core.slug import slugify
from core.wiki_repository import WikiRepository


def _inject_metadata_fields(page: str, meta: DocMetadata) -> str:
    """Insert DocMetadata fields into the YAML frontmatter of a wiki page."""
    close_idx = page.index('\n---\n', 3)

    def _yaml_list(key: str, values: list[str]) -> str:
        items = '\n'.join(f'  - "{v}"' for v in values)
        return f'{key}:\n{items}'

    lines = [
        _yaml_list('author', meta.author),
        _yaml_list('reviewed_by', meta.reviewed_by),
        f'documented_date: "{meta.documented_date}"',
        f'last_updated_date: "{meta.last_updated_date}"',
        f'review_cycle: "{meta.review_cycle}"',
    ]
    insertion = '\n'.join(lines)
    return page[:close_idx] + '\n' + insertion + page[close_idx:]


def ingest_doc(
    doc_path: Path,
    repo: WikiRepository,
    synthesize_fn: Callable[[str, str], str],
    chat_fn: ChatFn | None = None,
) -> None:
    """Copy source sections to raw/ and write synthesized source pages to sources/.

    When chat_fn is provided, the document is preprocessed: images are stripped,
    metadata is extracted from the header, and large docs are split by section.
    Each section becomes its own source page. Without chat_fn, the document is
    ingested as a single page (legacy behaviour).

    Args:
        doc_path: Path to the local markdown file to ingest.
        repo: WikiRepository used for all wiki reads and writes.
        synthesize_fn: Callable (content, slug) -> source page markdown with YAML frontmatter.
        chat_fn: LLM backend for metadata extraction and preprocessing. When None,
            preprocessing is skipped.

    Raises:
        ValueError: If a slug cannot be derived from the filename, or if any
            section synthesis returns no YAML frontmatter.
    """
    doc_slug = slugify(doc_path.stem)
    if not doc_slug:
        raise ValueError(f"Cannot derive a slug from filename {doc_path.name!r}")

    raw_content = doc_path.read_text()

    if chat_fn is not None:
        cleaned = strip_images(raw_content)
        meta = extract_metadata(cleaned, chat_fn)
        sections = split_sections(cleaned, doc_slug)
    else:
        sections = [(doc_slug, raw_content)]
        meta = None

    for section_slug, section_content in sections:
        source_page = synthesize_fn(section_content, section_slug)
        # Validate before any writes so a bad synthesis never leaves an orphaned raw file.
        if not source_page.startswith('---'):
            raise ValueError(
                f'Synthesis for {section_slug!r} returned no YAML frontmatter. '
                'Check SYNTHESIS_BACKEND / OLLAMA_MODEL and retry.'
            )
        if meta is not None:
            source_page = _inject_metadata_fields(source_page, meta)
        repo.write_raw(section_slug, section_content)
        repo.write_page('sources', section_slug, source_page)
