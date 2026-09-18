import pytest
from pathlib import Path
from core.ingest_doc import ingest_doc
from core.wiki_repository import FilesystemWikiRepository

FIXTURE = Path(__file__).parent / "fixtures" / "retrieval-augmented-generation.md"

MOCK_SOURCE_PAGE = """\
---
type: source
title: Retrieval-Augmented Generation
description: Overview of RAG, combining retrieval systems with LLMs for grounded generation.
sources:
  - raw/retrieval-augmented-generation.md
created: 2026-09-17T00:00:00Z
---

## Summary

[[Retrieval-Augmented Generation]] (RAG) combines a retriever and an LLM reader. \
The retriever uses [[vector embeddings]] to find relevant documents from a [[vector store]], \
then the [[LLM]] generates answers grounded in retrieved context.
"""


def _mock_synthesize(content: str, slug: str) -> str:
    return MOCK_SOURCE_PAGE


# --- Slice 1: raw copy ---

def test_ingest_doc_copies_raw_file(tmp_path):
    repo = FilesystemWikiRepository(tmp_path)
    ingest_doc(FIXTURE, repo, _mock_synthesize)
    raw = tmp_path / "raw" / "retrieval-augmented-generation.md"
    assert raw.exists()
    assert raw.read_text() == FIXTURE.read_text()


# --- Slice 2: source page ---

def test_ingest_doc_writes_source_page(tmp_path):
    repo = FilesystemWikiRepository(tmp_path)
    ingest_doc(FIXTURE, repo, _mock_synthesize)
    source = tmp_path / "sources" / "retrieval-augmented-generation.md"
    assert source.exists()
    assert source.read_text() == MOCK_SOURCE_PAGE


# --- Slice 3: malformed synthesis output raises ---

def test_ingest_doc_raises_on_missing_frontmatter(tmp_path):
    repo = FilesystemWikiRepository(tmp_path)

    def _plain_text_synthesize(content: str, slug: str) -> str:
        return 'This is a plain English summary with no frontmatter.'

    with pytest.raises(ValueError, match='no YAML frontmatter'):
        ingest_doc(FIXTURE, repo, _plain_text_synthesize)


# --- Slice 4: idempotent overwrite ---

def test_ingest_doc_overwrites_on_rerun(tmp_path):
    repo = FilesystemWikiRepository(tmp_path)
    ingest_doc(FIXTURE, repo, _mock_synthesize)
    raw = tmp_path / "raw" / "retrieval-augmented-generation.md"
    source = tmp_path / "sources" / "retrieval-augmented-generation.md"
    raw.write_text("old content")
    source.write_text("old content")

    ingest_doc(FIXTURE, repo, _mock_synthesize)

    assert raw.read_text() == FIXTURE.read_text()
    assert source.read_text() == MOCK_SOURCE_PAGE
