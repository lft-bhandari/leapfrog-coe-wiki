from __future__ import annotations

import re
from pathlib import Path
from typing import TypedDict

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
_WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")

_DOMAIN_SLUGS = [
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

# Maps wiki subdirectory name to the node type string used in the API response
_DIR_TO_TYPE = {
    "sources": "source",
    "concepts": "concept",
    "entities": "entity",
    "domains": "domain",
}


class Node(TypedDict):
    id: str
    type: str
    label: str


class Edge(TypedDict):
    source: str
    target: str


class GraphData(TypedDict):
    nodes: list[Node]
    edges: list[Edge]


def _parse_frontmatter_field(content: str, field: str) -> str:
    """Extract a scalar value from YAML frontmatter without a full YAML parser.

    Only handles simple key: value pairs — sufficient for our controlled frontmatter format.
    """
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return ""
    for line in match.group(1).splitlines():
        if line.startswith(f"{field}:"):
            return line[len(f"{field}:"):].strip()
    return ""


def _extract_wikilinks(content: str) -> list[str]:
    """Return all wikilink targets from a markdown page body (after the frontmatter)."""
    # Strip frontmatter before extracting to avoid links in description fields
    body = _FRONTMATTER_RE.sub("", content, count=1)
    return _WIKILINK_RE.findall(body)


def _slugify(name: str) -> str:
    """Convert a term to a URL-safe lowercase slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower())
    return slug.strip("-")


def _resolve_wikilink(link: str, known_ids: set[str]) -> str | None:
    """Resolve a wikilink target to a known node ID, or return None if unresolvable.

    Path-style links (containing "/") are used as-is. Bare-term links are
    tried against concepts/ and entities/ directories.
    """
    if "/" in link:
        # Path-style cross-reference — strip .md extension if present
        node_id = link.removesuffix(".md")
        return node_id if node_id in known_ids else None

    slug = _slugify(link)
    for prefix in ("concepts", "entities"):
        candidate = f"{prefix}/{slug}"
        if candidate in known_ids:
            return candidate
    return None


def build_graph(wiki_dir: Path) -> GraphData:
    """Build a knowledge graph from the wiki directory.

    Scans all wiki pages, creates one node per page, and creates edges for
    each [[wikilink]] that resolves to a known node. Domain nodes are always
    included even if their index page does not yet exist on disk.

    Args:
        wiki_dir: Root directory of the wiki (contains sources/, concepts/, etc.).

    Returns:
        GraphData dict with 'nodes' and 'edges' lists ready for React Flow.
    """
    nodes: list[Node] = []
    seen_ids: set[str] = set()

    # Always include all domain nodes so the hub structure is visible from day one.
    # Also read their file content so wikilinks inside domain pages produce edges.
    page_contents: dict[str, str] = {}
    for domain in _DOMAIN_SLUGS:
        node_id = f"domains/{domain}/index"
        label = domain.replace("-", " ").title()
        nodes.append(Node(id=node_id, type="domain", label=label))
        seen_ids.add(node_id)
        index_file = wiki_dir / "domains" / domain / "index.md"
        if index_file.exists():
            page_contents[node_id] = index_file.read_text(encoding="utf-8")

    # Scan all other wiki page types
    for dir_name, node_type in _DIR_TO_TYPE.items():
        if dir_name == "domains":
            # Domain nodes already seeded above; skip this directory here
            continue
        page_dir = wiki_dir / dir_name
        if not page_dir.exists():
            continue
        md_files = list(page_dir.glob("*.md"))

        for md_file in md_files:
            rel = md_file.relative_to(wiki_dir)
            node_id = str(rel.with_suffix(""))
            if node_id in seen_ids:
                continue
            content = md_file.read_text(encoding="utf-8")
            title = _parse_frontmatter_field(content, "title") or md_file.stem
            nodes.append(Node(id=node_id, type=node_type, label=title))
            seen_ids.add(node_id)
            page_contents[node_id] = content

    # Build edges from wikilinks in page bodies
    edges: list[Edge] = []
    seen_edges: set[tuple[str, str]] = set()
    for source_id, content in page_contents.items():
        for link in _extract_wikilinks(content):
            target_id = _resolve_wikilink(link, seen_ids)
            if target_id and target_id != source_id:
                pair = (source_id, target_id)
                if pair not in seen_edges:
                    edges.append(Edge(source=source_id, target=target_id))
                    seen_edges.add(pair)

    return GraphData(nodes=nodes, edges=edges)
