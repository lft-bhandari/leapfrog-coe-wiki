from __future__ import annotations

import re

from core.wiki_repository import WikiRepository

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

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


def _parse_scalar(content: str, field: str) -> str:
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return ""
    for line in match.group(1).splitlines():
        if line.startswith(f"{field}:"):
            return line[len(f"{field}:"):].strip()
    return ""


def _parse_domain(content: str) -> str:
    domain = _parse_scalar(content, "domain")
    return domain if domain in _DOMAINS else "general"


def _domain_title(domain: str) -> str:
    return domain.replace("-", " ").title()


def _page_description(content: str) -> str:
    """Return description frontmatter, falling back to title if absent."""
    desc = _parse_scalar(content, "description")
    return desc or _parse_scalar(content, "title")


def build_index(repo: WikiRepository) -> None:
    """Walk all page directories and write description-bearing index files.

    Domain indexes list each source page as `- [[sources/slug]] — description`.
    The root index lists each domain that has at least one source page.
    Pages without a description field fall back to their title field.

    Args:
        repo: WikiRepository for reading pages and writing index files.
    """
    domain_to_slugs: dict[str, list[str]] = {d: [] for d in _DOMAINS}
    for slug in repo.list_slugs("sources"):
        content = repo.read_page("sources", slug)
        domain = _parse_domain(content)
        domain_to_slugs[domain].append(slug)

    for domain, slugs in domain_to_slugs.items():
        if not slugs:
            continue
        lines = [f"# {_domain_title(domain)}\n"]
        for s in sorted(slugs):
            content = repo.read_page("sources", s)
            desc = _page_description(content) or s
            lines.append(f"- [[sources/{s}]] — {desc}")
        repo.write_page("domains", f"{domain}/index", "\n".join(lines) + "\n")

    lines = ["# CoE Wiki\n"]
    for domain in _DOMAINS:
        if repo.page_exists("domains", f"{domain}/index"):
            lines.append(f"- [[domains/{domain}/index]] — {_domain_title(domain)}")
    repo.write_root_index("\n".join(lines) + "\n")
