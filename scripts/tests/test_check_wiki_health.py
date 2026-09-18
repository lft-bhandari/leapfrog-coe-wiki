from __future__ import annotations

import pytest
from pathlib import Path

from check_wiki_health import HealthReport, check_wiki_health


def _write_page(wiki: Path, subdir: str, slug: str, content: str) -> None:
    p = wiki / subdir / f'{slug}.md'
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding='utf-8')


_GOOD_SOURCE = """\
---
type: source
title: RAG Overview
description: A guide to retrieval-augmented generation.
domain: retrieval-and-knowledge
---

## Summary

[[Retrieval-Augmented Generation]] combines a [[vector store]] with an LLM.
"""

_GOOD_SOURCE_2 = """\
---
type: source
title: Context Engineering
description: Techniques for managing LLM context windows.
domain: agents-and-autonomy
---

## Summary

[[Retrieval-Augmented Generation]] is one approach to [[context-engineering]].
"""

_MALFORMED_SOURCE = 'This has no frontmatter at all.'


def test_healthy_wiki_passes(tmp_path):
    _write_page(tmp_path, 'sources', 'rag', _GOOD_SOURCE)
    _write_page(tmp_path, 'sources', 'ctx', _GOOD_SOURCE_2)

    report = check_wiki_health(tmp_path)

    assert report.malformed_sources == []
    assert report.sources_without_wikilinks == []
    assert len(report.qualifying_terms) >= 1  # RAG appears in both


def test_detects_malformed_source(tmp_path):
    _write_page(tmp_path, 'sources', 'bad', _MALFORMED_SOURCE)

    report = check_wiki_health(tmp_path)

    assert 'bad' in report.malformed_sources


def test_detects_source_with_no_wikilinks(tmp_path):
    no_links = '---\ntype: source\ntitle: T\n---\n\nNo links here.\n'
    _write_page(tmp_path, 'sources', 'empty', no_links)

    report = check_wiki_health(tmp_path)

    assert 'empty' in report.sources_without_wikilinks


def test_counts_qualifying_terms(tmp_path):
    _write_page(tmp_path, 'sources', 'a', _GOOD_SOURCE)
    _write_page(tmp_path, 'sources', 'b', _GOOD_SOURCE_2)

    report = check_wiki_health(tmp_path)

    # 'Retrieval-Augmented Generation' appears in both sources
    assert 'Retrieval-Augmented Generation' in report.qualifying_terms


def test_empty_wiki_passes_with_no_errors(tmp_path):
    report = check_wiki_health(tmp_path)

    assert report.malformed_sources == []
    assert report.sources_without_wikilinks == []
    assert report.qualifying_terms == {}
