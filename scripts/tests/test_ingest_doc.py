import pytest
from pathlib import Path
from core.ingest_doc import ingest_doc
from core.metadata import DocMetadata
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

_MULTI_SECTION_DOC = """\
# Context Engineering

Intro text about the doc.

## Introduction

What context engineering is.

## Retrieval Techniques

How retrieval works with [[RAG]].
"""


def _mock_synthesize(content: str, slug: str) -> str:
    return MOCK_SOURCE_PAGE


def _mock_chat_fn(system: str, user: str) -> str:
    return '{}'


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


# --- Slice 5: multi-section splitting ---

def test_ingest_doc_creates_one_source_page_per_section(tmp_path):
    doc = tmp_path / "context-engineering.md"
    doc.write_text(_MULTI_SECTION_DOC)
    repo = FilesystemWikiRepository(tmp_path)

    ingest_doc(doc, repo, _mock_synthesize, chat_fn=_mock_chat_fn)

    sources = list((tmp_path / "sources").glob("*.md"))
    slugs = {s.stem for s in sources}
    assert "context-engineering--introduction" in slugs
    assert "context-engineering--retrieval-techniques" in slugs


def test_ingest_doc_writes_raw_per_section(tmp_path):
    doc = tmp_path / "context-engineering.md"
    doc.write_text(_MULTI_SECTION_DOC)
    repo = FilesystemWikiRepository(tmp_path)

    ingest_doc(doc, repo, _mock_synthesize, chat_fn=_mock_chat_fn)

    assert (tmp_path / "raw" / "context-engineering--introduction.md").exists()
    assert (tmp_path / "raw" / "context-engineering--retrieval-techniques.md").exists()


# --- Slice 6: metadata injection ---

def test_ingest_doc_injects_metadata_into_frontmatter(tmp_path):
    doc = tmp_path / "context-engineering.md"
    doc.write_text(_MULTI_SECTION_DOC)
    repo = FilesystemWikiRepository(tmp_path)

    import json
    meta = {
        "author": ["Samir Dahal"],
        "reviewed_by": ["Muskan Bhandari"],
        "documented_date": "28th May, 2026",
        "last_updated_date": "28th May, 2026",
        "review_cycle": "Q2 2026",
    }

    def _chat_fn_with_meta(system: str, user: str) -> str:
        return json.dumps(meta)

    ingest_doc(doc, repo, _mock_synthesize, chat_fn=_chat_fn_with_meta)

    source = (tmp_path / "sources" / "context-engineering--introduction.md").read_text()
    assert "author:" in source
    assert "Samir Dahal" in source
    assert "reviewed_by:" in source
    assert "Muskan Bhandari" in source
    assert "documented_date:" in source


def test_ingest_doc_without_chat_fn_preserves_original_behaviour(tmp_path):
    """Passing no chat_fn keeps the pre-preprocessing single-page behaviour."""
    repo = FilesystemWikiRepository(tmp_path)
    ingest_doc(FIXTURE, repo, _mock_synthesize)

    source = tmp_path / "sources" / "retrieval-augmented-generation.md"
    assert source.exists()
    assert source.read_text() == MOCK_SOURCE_PAGE
