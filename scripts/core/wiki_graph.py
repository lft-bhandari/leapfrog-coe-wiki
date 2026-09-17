from __future__ import annotations

import re
from collections import defaultdict

from core.wiki_repository import WikiRepository


def extract_wikilinks(content: str) -> set[str]:
    """Extract bare-term wikilink targets from a markdown string.

    Path-style wikilinks (e.g. [[sources/rag]] or [[domains/x/index]]) are
    excluded — they are cross-references to existing pages, not new term candidates.
    Term matching is case-sensitive: [[LLM]] and [[llm]] are treated as distinct
    terms, matching the CONTEXT.md vocabulary where exact capitalisation matters.

    Args:
        content: Markdown text that may contain [[wikilink]] syntax.

    Returns:
        Set of bare wikilink target strings (no "/" in the target).
    """
    all_links = re.findall(r"\[\[([^\]]+)\]\]", content)
    # Exclude path-style cross-references to avoid spurious concept page creation
    return {link for link in all_links if "/" not in link}


def collect_term_mentions(repo: WikiRepository) -> dict[str, list[str]]:
    """Scan all source pages and map each wikilink term to the slugs that mention it.

    Args:
        repo: WikiRepository to read source pages from.

    Returns:
        Dict mapping term string to sorted list of source slugs that mention it.
        Terms that appear in zero sources are not included.
    """
    slugs = repo.list_slugs("sources")
    term_to_slugs: dict[str, list[str]] = defaultdict(list)

    for slug in sorted(slugs):
        content = repo.read_page("sources", slug)
        for term in extract_wikilinks(content):
            term_to_slugs[term].append(slug)

    return dict(term_to_slugs)
