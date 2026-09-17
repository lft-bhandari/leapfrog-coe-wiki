from __future__ import annotations

from pathlib import Path

import pytest

from app.services.chat_service import navigate_and_answer
from tests.conftest import write_wiki_page


ROOT_INDEX = """\
---
title: CoE Wiki
---

Welcome to the CoE Wiki. See [[concepts/rag]] for details.
"""


# --- Slice 1: immediate answer (no READ steps) ---

def test_navigate_answers_immediately_when_llm_does_not_navigate(tmp_path):
    write_wiki_page(tmp_path, "index.md", ROOT_INDEX)

    def chat_fn(messages: list[dict]) -> str:
        return "ANSWER: Paris is the capital.\nCITATIONS:"

    result = navigate_and_answer("What is the capital?", [], tmp_path, chat_fn)

    assert result["answer"] == "Paris is the capital."
    assert result["citations"] == []


# --- Slice 2: one READ then ANSWER ---

CONCEPT_PAGE = """\
---
title: RAG
---

RAG stands for Retrieval-Augmented Generation.
"""


def test_navigate_follows_one_read_step(tmp_path):
    write_wiki_page(tmp_path, "index.md", ROOT_INDEX)
    write_wiki_page(tmp_path, "concepts/rag.md", CONCEPT_PAGE)

    calls: list[list[dict]] = []

    def chat_fn(messages: list[dict]) -> str:
        calls.append(messages)
        if len(calls) == 1:
            return "READ: concepts/rag"
        return "ANSWER: RAG stands for Retrieval-Augmented Generation.\nCITATIONS: concepts/rag"

    result = navigate_and_answer("What is RAG?", [], tmp_path, chat_fn)

    assert "Retrieval-Augmented Generation" in result["answer"]
    assert "concepts/rag" in result["citations"]
    assert len(calls) == 2


# --- Slice 3: READ for a non-existent page does not crash ---

def test_navigate_skips_missing_page_gracefully(tmp_path):
    write_wiki_page(tmp_path, "index.md", ROOT_INDEX)

    call_count = 0

    def chat_fn(messages: list[dict]) -> str:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return "READ: concepts/nonexistent"
        return "ANSWER: No info found.\nCITATIONS:"

    result = navigate_and_answer("Tell me about X", [], tmp_path, chat_fn)

    assert result["answer"] == "No info found."
    assert call_count == 2


# --- Slice 4: history is forwarded to chat_fn ---

def test_navigate_includes_history_in_messages(tmp_path):
    write_wiki_page(tmp_path, "index.md", ROOT_INDEX)

    captured: list[list[dict]] = []

    def chat_fn(messages: list[dict]) -> str:
        captured.append(messages)
        return "ANSWER: Done.\nCITATIONS:"

    history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
    ]
    navigate_and_answer("New question", history, tmp_path, chat_fn)

    first_call_messages = captured[0]
    roles_seen = [m["role"] for m in first_call_messages]
    assert "user" in roles_seen
    assert "assistant" in roles_seen
    combined = " ".join(m["content"] for m in first_call_messages)
    assert "Hello" in combined
    assert "Hi" in combined


# --- Slice 5: max_steps cap stops infinite navigation ---

def test_navigate_stops_after_max_steps(tmp_path):
    write_wiki_page(tmp_path, "index.md", ROOT_INDEX)
    write_wiki_page(tmp_path, "concepts/rag.md", CONCEPT_PAGE)

    def chat_fn(messages: list[dict]) -> str:
        # Always responds with READ to trigger infinite loop
        return "READ: concepts/rag"

    result = navigate_and_answer("Loop forever", [], tmp_path, chat_fn, max_steps=3)

    assert isinstance(result["answer"], str)
    assert isinstance(result["citations"], list)


# --- Slice 6: hallucinated LLM citations are filtered out ---

def test_navigate_drops_hallucinated_citations(tmp_path):
    write_wiki_page(tmp_path, "index.md", ROOT_INDEX)
    write_wiki_page(tmp_path, "concepts/rag.md", CONCEPT_PAGE)

    def chat_fn(messages: list[dict]) -> str:
        # LLM declares a citation that does not exist on disk
        return "ANSWER: Some answer.\nCITATIONS: concepts/rag, concepts/hallucinated-page"

    result = navigate_and_answer("What is RAG?", [], tmp_path, chat_fn)

    assert "concepts/hallucinated-page" not in result["citations"]
    # Real citation that exists on disk is kept
    assert "concepts/rag" in result["citations"]


# --- Slice 7: no relevant content → explicit "not found" message ---

def test_navigate_returns_explicit_message_when_wiki_has_no_content(tmp_path):
    write_wiki_page(tmp_path, "index.md", ROOT_INDEX)

    def chat_fn(messages: list[dict]) -> str:
        return "ANSWER: The wiki does not contain information about this topic.\nCITATIONS:"

    result = navigate_and_answer("Tell me about quantum physics", [], tmp_path, chat_fn)

    assert "does not contain" in result["answer"].lower() or "no" in result["answer"].lower()
    assert result["citations"] == []
