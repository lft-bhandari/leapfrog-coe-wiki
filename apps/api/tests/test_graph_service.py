from pathlib import Path
from app.services.graph_service import build_graph

# --- Helpers ---

def write_page(wiki_dir: Path, rel_path: str, content: str) -> None:
    p = wiki_dir / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)


# --- Slice 1: domain nodes always present ---

def test_build_graph_always_includes_all_domain_nodes(tmp_path):
    graph = build_graph(tmp_path)
    domain_node_ids = {n["id"] for n in graph["nodes"] if n["type"] == "domain"}
    expected = {
        "domains/gen-ai-fundamentals/index",
        "domains/retrieval-and-knowledge/index",
        "domains/agents-and-autonomy/index",
        "domains/evaluation-and-quality/index",
        "domains/models-capability-adaptation/index",
        "domains/security-and-governance/index",
        "domains/platform-and-operations/index",
        "domains/classical-ml-deep-learning/index",
        "domains/general/index",
    }
    assert expected == domain_node_ids


# --- Slice 2: nodes from wiki pages ---

SOURCE_PAGE = """\
---
type: source
title: Retrieval-Augmented Generation
domain: retrieval-and-knowledge
---

[[vector embeddings]] power [[RAG]].
"""

CONCEPT_PAGE = """\
---
type: concept
title: Vector Embeddings
---

[[vector embeddings]] are dense representations.
"""

def test_build_graph_creates_node_for_each_wiki_page(tmp_path):
    write_page(tmp_path, "sources/rag.md", SOURCE_PAGE)
    write_page(tmp_path, "concepts/vector-embeddings.md", CONCEPT_PAGE)

    graph = build_graph(tmp_path)
    node_ids = {n["id"] for n in graph["nodes"]}

    assert "sources/rag" in node_ids
    assert "concepts/vector-embeddings" in node_ids


def test_build_graph_node_label_comes_from_frontmatter_title(tmp_path):
    write_page(tmp_path, "sources/rag.md", SOURCE_PAGE)

    graph = build_graph(tmp_path)
    node = next(n for n in graph["nodes"] if n["id"] == "sources/rag")

    assert node["label"] == "Retrieval-Augmented Generation"
    assert node["type"] == "source"


# --- Slice 3: edges from wikilinks ---

def test_build_graph_creates_edge_for_resolved_wikilink(tmp_path):
    write_page(tmp_path, "sources/rag.md", SOURCE_PAGE)
    write_page(tmp_path, "concepts/vector-embeddings.md", CONCEPT_PAGE)

    graph = build_graph(tmp_path)
    edges = {(e["source"], e["target"]) for e in graph["edges"]}

    # source page mentions [[vector embeddings]] → resolves to concepts/vector-embeddings
    assert ("sources/rag", "concepts/vector-embeddings") in edges


def test_build_graph_does_not_create_edge_for_unresolved_wikilink(tmp_path):
    # [[RAG]] in SOURCE_PAGE has no matching concept/entity page
    write_page(tmp_path, "sources/rag.md", SOURCE_PAGE)

    graph = build_graph(tmp_path)
    target_ids = {e["target"] for e in graph["edges"]}

    assert "concepts/rag" not in target_ids
    assert "entities/rag" not in target_ids
