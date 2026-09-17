from core.wiki_graph import collect_term_mentions, extract_wikilinks
from core.wiki_repository import FilesystemWikiRepository

# --- Slice 1: wikilink extraction ---

def test_extract_wikilinks_finds_all_terms():
    content = "[[RAG]] combines [[vector embeddings]] with an [[LLM]]."
    assert extract_wikilinks(content) == {"RAG", "vector embeddings", "LLM"}


def test_extract_wikilinks_returns_empty_set_for_plain_text():
    assert extract_wikilinks("No wikilinks here.") == set()


def test_extract_wikilinks_deduplicates_repeated_terms():
    content = "[[RAG]] is useful. [[RAG]] is also called [[RAG]]."
    assert extract_wikilinks(content) == {"RAG"}


# --- Slice 2: term mention collection across source pages ---

SOURCE_A = """\
---
type: source
title: RAG
domain: retrieval-and-knowledge
---

[[vector embeddings]] and [[LLM]] are used in [[RAG]].
"""

SOURCE_B = """\
---
type: source
title: Vector Databases
domain: retrieval-and-knowledge
---

[[vector embeddings]] power [[vector stores]] for semantic search.
"""


def test_collect_term_mentions_maps_terms_to_source_slugs(tmp_path):
    repo = FilesystemWikiRepository(tmp_path)
    repo.write_page("sources", "rag", SOURCE_A)
    repo.write_page("sources", "vector-databases", SOURCE_B)

    mentions = collect_term_mentions(repo)

    # "vector embeddings" appears in both sources
    assert set(mentions["vector embeddings"]) == {"rag", "vector-databases"}


def test_collect_term_mentions_single_source_term_has_one_entry(tmp_path):
    repo = FilesystemWikiRepository(tmp_path)
    repo.write_page("sources", "rag", SOURCE_A)
    repo.write_page("sources", "vector-databases", SOURCE_B)

    mentions = collect_term_mentions(repo)

    # "RAG" only appears in source A
    assert mentions["RAG"] == ["rag"]


def test_collect_term_mentions_empty_repo_returns_empty(tmp_path):
    repo = FilesystemWikiRepository(tmp_path)
    assert collect_term_mentions(repo) == {}
