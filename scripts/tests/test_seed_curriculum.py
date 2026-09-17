from __future__ import annotations

from pathlib import Path

from seed_curriculum import _parse_curriculum, _slugify, seed_curriculum

_MINI_CURRICULUM = """\
# Test Curriculum

---

## Retrieval and Knowledge

- Chunking Strategies
- Reranking
- GraphRAG and Structured Knowledge

## Agents and Autonomy

- The Agent Loop
- Tool Calling and Tool Design
"""


def _write_curriculum(tmp_path: Path, text: str = _MINI_CURRICULUM) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    p = tmp_path / "curriculum.md"
    p.write_text(text, encoding="utf-8")
    return p


def test_parse_curriculum_extracts_domains_and_topics():
    sections = _parse_curriculum(_MINI_CURRICULUM)

    assert len(sections) == 2
    domain_slugs = [s[0] for s in sections]
    assert "retrieval-and-knowledge" in domain_slugs
    assert "agents-and-autonomy" in domain_slugs

    topics_retrieval = next(s[2] for s in sections if s[0] == "retrieval-and-knowledge")
    assert "Chunking Strategies" in topics_retrieval
    assert "Reranking" in topics_retrieval
    assert "GraphRAG and Structured Knowledge" in topics_retrieval


def test_slugify_lowercases_and_hyphenates():
    assert _slugify("Chunking Strategies") == "chunking-strategies"
    assert _slugify("GraphRAG and Structured Knowledge") == "graphrag-and-structured-knowledge"
    assert _slugify("The Agent Loop") == "the-agent-loop"


def test_seed_curriculum_writes_stubs_for_all_topics(tmp_path):
    curriculum = _write_curriculum(tmp_path / "docs")
    wiki = tmp_path / "wiki"

    n = seed_curriculum(curriculum_path=curriculum, wiki_dir=wiki)

    # All 5 topics in the mini curriculum should have been written
    assert n == 5
    assert (wiki / "concepts" / "chunking-strategies.md").exists()
    assert (wiki / "concepts" / "reranking.md").exists()
    assert (wiki / "concepts" / "graphrag-and-structured-knowledge.md").exists()
    assert (wiki / "concepts" / "the-agent-loop.md").exists()
    assert (wiki / "concepts" / "tool-calling-and-tool-design.md").exists()


def test_seed_curriculum_stub_has_required_frontmatter(tmp_path):
    curriculum = _write_curriculum(tmp_path / "docs")
    wiki = tmp_path / "wiki"

    seed_curriculum(curriculum_path=curriculum, wiki_dir=wiki)

    content = (wiki / "concepts" / "chunking-strategies.md").read_text(encoding="utf-8")
    assert "type: concept" in content
    assert "title: Chunking Strategies" in content
    assert "domain: retrieval-and-knowledge" in content
    assert "description:" in content
    assert "curriculum_topic: true" in content


def test_seed_curriculum_is_idempotent(tmp_path):
    curriculum = _write_curriculum(tmp_path / "docs")
    wiki = tmp_path / "wiki"

    first = seed_curriculum(curriculum_path=curriculum, wiki_dir=wiki)
    second = seed_curriculum(curriculum_path=curriculum, wiki_dir=wiki)

    # Second run should write zero new pages
    assert first == 5
    assert second == 0


def test_seed_curriculum_regenerates_indexes(tmp_path):
    curriculum = _write_curriculum(tmp_path / "docs")
    wiki = tmp_path / "wiki"

    seed_curriculum(curriculum_path=curriculum, wiki_dir=wiki)

    # Root index exists after seeding (build_index was called)
    assert (wiki / "index.md").exists()
