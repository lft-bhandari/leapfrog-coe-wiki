from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable

from core.build_index import build_index
from core.chat_backends import ChatFn
from core.ingest_doc import ingest_doc
from core.slug import slugify
from core.wiki_graph import collect_term_mentions
from core.wiki_repository import WikiRepository

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)

_DOMAINS = [
    "gen-ai-fundamentals",
    "retrieval-and-knowledge",
    "agents-and-autonomy",
    "evaluation-and-quality",
    "models-capability-adaptation",
    "security-and-governance",
    "platform-and-operations",
    "classical-ml-deep-learning",
    "general",
]


def _parse_frontmatter_field(content: str, field: str) -> str:
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return ""
    for line in match.group(1).splitlines():
        if line.startswith(f"{field}:"):
            return line[len(f"{field}:"):].strip()
    return ""


def _parse_page_type(content: str) -> str:
    return _parse_frontmatter_field(content, "type") or "concept"


def _parse_domain(content: str) -> str:
    domain = _parse_frontmatter_field(content, "domain")
    return domain if domain in _DOMAINS else "general"


def _write_term_page(
    term: str,
    source_slugs: list[str],
    repo: WikiRepository,
    synthesize_term_fn: Callable[[str, list[str]], str],
) -> None:
    """Synthesize and write a concept or entity page for a qualifying term.

    The page type (concept/entity) is determined by the 'type' field in the
    synthesized page's frontmatter, so the synthesize_fn controls classification.

    Args:
        term: The wikilink term that qualifies under the ≥2 rule.
        source_slugs: Slugs of the source pages that mention this term.
        repo: WikiRepository for reading sources and writing the term page.
        synthesize_term_fn: Callable (term, source_contents) -> page markdown.
    """
    source_contents = [repo.read_page("sources", slug) for slug in source_slugs]
    page_content = synthesize_term_fn(term, source_contents)
    page_type = _parse_page_type(page_content)
    # Map singular type name to its wiki directory; unknown types default to concepts/
    target_dir = {"concept": "concepts", "entity": "entities"}.get(page_type, "concepts")
    slug = slugify(term)
    repo.write_page(target_dir, slug, page_content)



def run_ingest(
    doc_paths: list[Path],
    repo: WikiRepository,
    synthesize_source_fn: Callable[[str, str], str],
    synthesize_term_fn: Callable[[str, list[str]], str],
    chat_fn: ChatFn | None = None,
) -> None:
    """Ingest multiple docs in parallel, apply the ≥2 rule, and rebuild all indexes.

    Args:
        doc_paths: Local markdown files to ingest.
        repo: WikiRepository for all wiki reads and writes.
        synthesize_source_fn: Callable (content, slug) -> source page markdown.
        synthesize_term_fn: Callable (term, source_contents) -> concept/entity page markdown.
        chat_fn: LLM backend for preprocessing (image stripping, metadata extraction,
            section splitting). When None, preprocessing is skipped.

    Raises:
        RuntimeError: If any source doc or term synthesis fails, with the filename included.
    """
    # Ingest all source docs in parallel — order of writes doesn't matter
    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(ingest_doc, path, repo, synthesize_source_fn, chat_fn): path
            for path in doc_paths
        }
        for future in as_completed(futures):
            path = futures[future]
            try:
                future.result()
            except Exception as exc:
                raise RuntimeError(f"Failed to ingest {path.name}: {exc}") from exc

    # Apply the ≥2 rule across the full ingested batch.
    # Wikilinks containing "/" are cross-references to existing pages, not new terms.
    term_to_sources = collect_term_mentions(repo)
    qualifying_terms = [
        term
        for term, slugs in term_to_sources.items()
        if len(slugs) >= 2 and "/" not in term
    ]

    # Synthesize concept/entity pages in parallel — each is an independent API call
    with ThreadPoolExecutor() as executor:
        term_futures = {
            executor.submit(_write_term_page, term, term_to_sources[term], repo, synthesize_term_fn): term
            for term in qualifying_terms
        }
        for future in as_completed(term_futures):
            term = term_futures[future]
            try:
                future.result()
            except Exception as exc:
                raise RuntimeError(f"Failed to synthesize term page for '{term}': {exc}") from exc

    build_index(repo)
