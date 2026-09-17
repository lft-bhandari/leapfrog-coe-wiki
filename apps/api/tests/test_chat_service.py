from __future__ import annotations

from pathlib import Path

import pytest

from app.services.chat_service import navigate_and_answer, navigate_and_answer_v2
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


# --- Slice 2: relevant page content is included in the context sent to chat_fn ---

CONCEPT_PAGE = """\
---
title: RAG
---

RAG stands for Retrieval-Augmented Generation.
"""


def test_navigate_includes_page_content_in_context(tmp_path):
    write_wiki_page(tmp_path, "index.md", ROOT_INDEX)
    write_wiki_page(tmp_path, "concepts/rag.md", CONCEPT_PAGE)

    captured: list[list[dict]] = []

    def chat_fn(messages: list[dict]) -> str:
        captured.append(messages)
        return "ANSWER: RAG stands for Retrieval-Augmented Generation.\nCITATIONS: concepts/rag"

    result = navigate_and_answer("What is RAG?", [], tmp_path, chat_fn)

    assert "Retrieval-Augmented Generation" in result["answer"]
    assert "concepts/rag" in result["citations"]
    # Keyword loading makes exactly one call
    assert len(captured) == 1
    # The rag concept page content was included in the message
    combined = " ".join(m["content"] for m in captured[0])
    assert "RAG stands for Retrieval-Augmented Generation" in combined


# --- Slice 3: empty wiki returns a graceful answer ---

def test_navigate_handles_empty_wiki(tmp_path):
    write_wiki_page(tmp_path, "index.md", ROOT_INDEX)
    # No other pages — no keyword match possible

    def chat_fn(messages: list[dict]) -> str:
        return "ANSWER: No info found.\nCITATIONS:"

    result = navigate_and_answer("Tell me about X", [], tmp_path, chat_fn)

    assert result["answer"] == "No info found."


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


# ---------------------------------------------------------------------------
# navigate_and_answer_v2 tests (LLM-guided graph traversal, WIKI_NAV=graph)
# ---------------------------------------------------------------------------

DOMAIN_INDEX = """\
# Retrieval And Knowledge

- [[sources/rag-overview]] — Overview of RAG.
- [[concepts/rag]]
"""


def _make_v2_chat_fn(responses: list[str]) -> tuple[list[list[dict]], "Callable"]:
    """Return (calls_list, chat_fn) where chat_fn returns responses in order."""
    calls: list[list[dict]] = []

    def chat_fn(messages: list[dict]) -> str:
        calls.append(messages)
        return responses[min(len(calls) - 1, len(responses) - 1)]

    return calls, chat_fn


def test_v2_traverses_index_to_domain_to_concept(tmp_path):
    write_wiki_page(tmp_path, "index.md", "# Wiki\n\n[[domains/retrieval/index]]")
    write_wiki_page(tmp_path, "domains/retrieval/index.md", "# Retrieval\n\n[[concepts/rag]]")
    write_wiki_page(tmp_path, "concepts/rag.md", "# RAG\n\nRAG is Retrieval-Augmented Generation.")

    calls, chat_fn = _make_v2_chat_fn([
        '{"action": "read", "path": "domains/retrieval/index"}',
        '{"action": "read", "path": "concepts/rag"}',
        '{"action": "answer"}',
        "ANSWER: RAG stands for Retrieval-Augmented Generation.\nCITATIONS: concepts/rag",
    ])

    result = navigate_and_answer_v2("What is RAG?", [], tmp_path, chat_fn)

    assert "Retrieval-Augmented Generation" in result["answer"]
    assert "concepts/rag" in result["citations"]


def test_v2_rejects_unlisted_path(tmp_path):
    write_wiki_page(tmp_path, "index.md", "# Wiki\n\n[[domains/retrieval/index]]")
    write_wiki_page(tmp_path, "domains/retrieval/index.md", "# Retrieval\n\n[[concepts/rag]]")
    write_wiki_page(tmp_path, "concepts/rag.md", "RAG content.")
    write_wiki_page(tmp_path, "concepts/secret.md", "Secret content.")

    calls, chat_fn = _make_v2_chat_fn([
        # LLM tries a path not in the current page's wikilinks
        '{"action": "read", "path": "concepts/secret"}',
        "ANSWER: Nothing found.\nCITATIONS:",
    ])

    result = navigate_and_answer_v2("Tell me about RAG", [], tmp_path, chat_fn)

    # secret should not appear in citations (unlisted path was rejected)
    assert "concepts/secret" not in result["citations"]


def test_v2_stops_at_max_steps(tmp_path):
    write_wiki_page(tmp_path, "index.md", "# Wiki\n\n[[concepts/loop]]")
    write_wiki_page(tmp_path, "concepts/loop.md", "[[concepts/loop]]")

    calls, chat_fn = _make_v2_chat_fn(
        ['{"action": "read", "path": "concepts/loop"}'] * 10
        + ["ANSWER: Stopped.\nCITATIONS:"]
    )

    result = navigate_and_answer_v2("Loop test", [], tmp_path, chat_fn, max_steps=3)

    # Already visited — should not loop infinitely
    assert isinstance(result["answer"], str)


def test_v2_skips_missing_page(tmp_path):
    write_wiki_page(tmp_path, "index.md", "# Wiki\n\n[[concepts/missing]]")
    # concepts/missing.md does NOT exist

    calls, chat_fn = _make_v2_chat_fn([
        '{"action": "read", "path": "concepts/missing"}',
        "ANSWER: Not found.\nCITATIONS:",
    ])

    result = navigate_and_answer_v2("What is missing?", [], tmp_path, chat_fn)

    # Gracefully handled — no crash, returned an answer
    assert isinstance(result["answer"], str)


def test_v2_forwards_history_to_final_answer_call(tmp_path):
    write_wiki_page(tmp_path, "index.md", "# Wiki")

    captured: list[list[dict]] = []

    def chat_fn(messages: list[dict]) -> str:
        captured.append(messages)
        if len(captured) == 1:
            return '{"action": "answer"}'
        return "ANSWER: Done.\nCITATIONS:"

    history = [{"role": "user", "content": "Prior question"}]
    navigate_and_answer_v2("New question", history, tmp_path, chat_fn)

    # Final answer call must contain the history
    final_call = captured[-1]
    combined = " ".join(m["content"] for m in final_call)
    assert "Prior question" in combined


# Callable type hint for the helper above
from typing import Callable  # noqa: E402
