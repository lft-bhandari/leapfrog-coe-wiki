from pathlib import Path
from core.orchestrate import run_ingest
from core.wiki_repository import FilesystemWikiRepository

FIXTURE_RAG = Path(__file__).parent / "fixtures" / "retrieval-augmented-generation.md"
FIXTURE_VECDB = Path(__file__).parent / "fixtures" / "vector-databases.md"

# Source synthesis returns a page that mentions shared and unique wikilinks.
# RAG doc mentions: [[vector embeddings]], [[LLM]], [[Retrieval-Augmented Generation]]
# VecDB doc mentions: [[vector embeddings]], [[vector stores]], [[LLMs]]
# Shared: [[vector embeddings]] → qualifies for concept page
# Unique: [[LLM]], [[Retrieval-Augmented Generation]], [[vector stores]], [[LLMs]] → no page

def _mock_source_rag(content: str, slug: str) -> str:
    return f"""\
---
type: source
title: Retrieval-Augmented Generation
description: Overview of RAG.
sources:
  - raw/{slug}.md
domain: retrieval-and-knowledge
created: 2026-09-17T00:00:00Z
---

[[Retrieval-Augmented Generation]] combines [[vector embeddings]] with an [[LLM]].
"""

def _mock_source_vecdb(content: str, slug: str) -> str:
    return f"""\
---
type: source
title: Vector Databases
description: Overview of vector databases.
sources:
  - raw/{slug}.md
domain: retrieval-and-knowledge
created: 2026-09-17T00:00:00Z
---

[[vector embeddings]] power [[vector stores]] for semantic search with [[LLMs]].
"""

def _mock_term_page(term: str, source_contents: list[str]) -> str:
    return f"""\
---
type: concept
title: {term}
description: Synthesized concept page for {term}.
---

[[{term}]] appears across multiple sources.
"""


# --- Slice 3a: ≥2 rule — concept page created for shared term ---

def test_run_ingest_creates_concept_page_for_shared_term(tmp_path):
    repo = FilesystemWikiRepository(tmp_path)

    def synthesize_source(content, slug):
        # discriminate by slug, not content — VecDB fixture also mentions "Retrieval"
        if slug == "retrieval-augmented-generation":
            return _mock_source_rag(content, slug)
        return _mock_source_vecdb(content, slug)

    run_ingest([FIXTURE_RAG, FIXTURE_VECDB], repo, synthesize_source, _mock_term_page)

    # "vector embeddings" appears in both source pages → concept page must exist
    assert repo.page_exists("concepts", "vector-embeddings")


# --- Slice 3b: ≥2 rule — no page for terms in only one source ---

def test_run_ingest_does_not_create_page_for_single_source_term(tmp_path):
    repo = FilesystemWikiRepository(tmp_path)

    def synthesize_source(content, slug):
        if slug == "retrieval-augmented-generation":
            return _mock_source_rag(content, slug)
        return _mock_source_vecdb(content, slug)

    run_ingest([FIXTURE_RAG, FIXTURE_VECDB], repo, synthesize_source, _mock_term_page)

    # "Retrieval-Augmented Generation" only in RAG doc → no concept page
    assert not repo.page_exists("concepts", "retrieval-augmented-generation")
    assert not repo.page_exists("entities", "retrieval-augmented-generation")


# --- Slice 3c: entity pages use type field from synthesized page ---

def _mock_entity_page(term: str, source_contents: list[str]) -> str:
    return f"""\
---
type: entity
title: {term}
description: Synthesized entity page for {term}.
---

[[{term}]] is a named tool or framework.
"""

def _mock_source_with_entity(content: str, slug: str) -> str:
    return f"""\
---
type: source
title: Doc {slug}
description: A doc.
sources:
  - raw/{slug}.md
domain: general
created: 2026-09-17T00:00:00Z
---

We use [[FAISS]] for vector search and [[FAISS]] is fast.
"""

def test_run_ingest_writes_entity_page_to_entities_directory(tmp_path):
    repo = FilesystemWikiRepository(tmp_path)
    # Two docs both mention [[FAISS]] → entity page should be created
    # (type: entity in frontmatter → goes to entities/)
    fixture_a = FIXTURE_RAG
    fixture_b = FIXTURE_VECDB

    def synthesize_source(content, slug):
        return _mock_source_with_entity(content, slug)

    run_ingest([fixture_a, fixture_b], repo, synthesize_source, _mock_entity_page)

    assert repo.page_exists("entities", "faiss")


# --- Slice 4: domain indexes rebuilt ---

def test_run_ingest_writes_domain_index(tmp_path):
    repo = FilesystemWikiRepository(tmp_path)

    def synthesize_source(content, slug):
        if slug == "retrieval-augmented-generation":
            return _mock_source_rag(content, slug)
        return _mock_source_vecdb(content, slug)

    run_ingest([FIXTURE_RAG, FIXTURE_VECDB], repo, synthesize_source, _mock_term_page)

    # domain index lives at wiki/domains/retrieval-and-knowledge/index.md
    assert repo.page_exists("domains", "retrieval-and-knowledge/index")


# --- Slice 5: root index rebuilt ---

def test_run_ingest_writes_root_index(tmp_path):
    repo = FilesystemWikiRepository(tmp_path)

    def synthesize_source(content, slug):
        if slug == "retrieval-augmented-generation":
            return _mock_source_rag(content, slug)
        return _mock_source_vecdb(content, slug)

    run_ingest([FIXTURE_RAG, FIXTURE_VECDB], repo, synthesize_source, _mock_term_page)

    assert repo.root_index_exists()


# --- Slice 6 (#13): concept/entity pages include description field ---

def test_run_ingest_concept_page_contains_description(tmp_path):
    repo = FilesystemWikiRepository(tmp_path)

    def synthesize_source(content, slug):
        if slug == "retrieval-augmented-generation":
            return _mock_source_rag(content, slug)
        return _mock_source_vecdb(content, slug)

    run_ingest([FIXTURE_RAG, FIXTURE_VECDB], repo, synthesize_source, _mock_term_page)

    # vector-embeddings is the shared term → concept page
    content = repo.read_page("concepts", "vector-embeddings")
    # description field must be present and non-empty
    assert "description:" in content
    desc_line = next(line for line in content.splitlines() if line.startswith("description:"))
    assert desc_line.split(":", 1)[1].strip()


# --- Slice 7 (#14): source pages include entities and concepts arrays ---

def _mock_source_with_arrays(content: str, slug: str) -> str:
    return f"""\
---
type: source
title: Doc {slug}
description: A document about vector search.
sources:
  - raw/{slug}.md
domain: retrieval-and-knowledge
created: 2026-09-17T00:00:00Z
entities:
  - "[[FAISS]]"
concepts:
  - "[[vector-search]]"
---

We use [[FAISS]] and [[vector-search]] techniques.
"""

def test_run_ingest_source_page_contains_entities_and_concepts_arrays(tmp_path):
    repo = FilesystemWikiRepository(tmp_path)

    run_ingest(
        [FIXTURE_RAG, FIXTURE_VECDB],
        repo,
        _mock_source_with_arrays,
        _mock_term_page,
    )

    rag_content = repo.read_page("sources", "retrieval-augmented-generation")
    assert "entities:" in rag_content
    assert "concepts:" in rag_content


# --- Slice 8 (#15): domain index uses description bullets ---

def _mock_source_with_desc(content: str, slug: str) -> str:
    return f"""\
---
type: source
title: My Source {slug}
description: A detailed look at {slug}.
sources:
  - raw/{slug}.md
domain: retrieval-and-knowledge
created: 2026-09-17T00:00:00Z
entities: []
concepts: []
---

Content here.
"""

def test_run_ingest_domain_index_contains_description_bullets(tmp_path):
    repo = FilesystemWikiRepository(tmp_path)

    run_ingest(
        [FIXTURE_RAG, FIXTURE_VECDB],
        repo,
        _mock_source_with_desc,
        _mock_term_page,
    )

    index_content = repo.read_page("domains", "retrieval-and-knowledge/index")
    # Must use description-bullet format
    assert " — " in index_content
    assert "[[sources/" in index_content
    # Description text from the mock
    assert "A detailed look at" in index_content


def test_run_ingest_domain_index_falls_back_to_title_when_no_description(tmp_path):
    repo = FilesystemWikiRepository(tmp_path)

    def no_desc_source(content: str, slug: str) -> str:
        return f"""\
---
type: source
title: Titled Source {slug}
sources:
  - raw/{slug}.md
domain: retrieval-and-knowledge
created: 2026-09-17T00:00:00Z
---

Content.
"""

    run_ingest([FIXTURE_RAG, FIXTURE_VECDB], repo, no_desc_source, _mock_term_page)

    index_content = repo.read_page("domains", "retrieval-and-knowledge/index")
    # Falls back to title, not empty dash
    assert "Titled Source" in index_content
