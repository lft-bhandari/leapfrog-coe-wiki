"""Seam 3 integration test: real Ollama + fixture wiki.

Requires a local Ollama instance running llama3.2:3b.
Skipped automatically when Ollama is unreachable.
"""
from __future__ import annotations

from pathlib import Path

import httpx2
import pytest

from app.services.chat_service import make_ollama_fn, navigate_and_answer
from tests.conftest import write_wiki_page


def _ollama_available() -> bool:
    try:
        r = httpx2.get("http://localhost:11434/api/tags", timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _ollama_available(),
    reason="Ollama is not running locally — skipping Seam 3 integration test",
)


@pytest.fixture()
def fixture_wiki(tmp_path: Path) -> Path:
    write_wiki_page(tmp_path, "index.md", """\
---
title: CoE Wiki
---

This wiki covers AI engineering topics.
See [[concepts/rag]] for retrieval-augmented generation.
See [[concepts/fine-tuning]] for model fine-tuning techniques.
""")
    write_wiki_page(tmp_path, "concepts/rag.md", """\
---
title: Retrieval-Augmented Generation
type: concept
---

Retrieval-Augmented Generation (RAG) is a technique that combines a retrieval system
with a language model. The retrieval system fetches relevant documents from a knowledge
base, and the language model uses them to generate accurate answers.
""")
    write_wiki_page(tmp_path, "concepts/fine-tuning.md", """\
---
title: Fine-tuning
type: concept
---

Fine-tuning is the process of training a pre-trained model on a specific dataset
to adapt it to a new task or domain.
""")
    return tmp_path


def test_integration_citations_resolve_to_real_paths(fixture_wiki: Path):
    """Verifies that every citation in the response maps to a real file in the wiki."""
    chat_fn = make_ollama_fn()
    result = navigate_and_answer("What is RAG?", [], fixture_wiki, chat_fn)

    assert isinstance(result["answer"], str)
    assert len(result["answer"]) > 0

    for citation in result["citations"]:
        page_file = fixture_wiki / f"{citation}.md"
        assert page_file.exists(), f"Citation '{citation}' does not resolve to a real wiki page"
