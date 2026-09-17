from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.chat import get_chat_fn
from tests.conftest import write_wiki_page

ROOT_INDEX = """\
---
title: CoE Wiki
---

Welcome. See [[concepts/rag]] for more.
"""

CONCEPT_PAGE = """\
---
title: RAG
---

RAG stands for Retrieval-Augmented Generation.
"""


@pytest.fixture()
def fixture_wiki(tmp_path: Path) -> Path:
    write_wiki_page(tmp_path, "index.md", ROOT_INDEX)
    write_wiki_page(tmp_path, "concepts/rag.md", CONCEPT_PAGE)
    return tmp_path


def make_client(fixture_wiki: Path, chat_fn_responses: list[str]) -> TestClient:
    """Build a TestClient with Ollama overridden to return scripted replies."""
    responses = iter(chat_fn_responses)

    def fake_chat_fn(_messages: list[dict]) -> str:
        return next(responses)

    # Override the Ollama dependency at the FastAPI level — correct seam (external boundary)
    app.dependency_overrides[get_chat_fn] = lambda: fake_chat_fn
    import os
    import app.routers.chat as chat_router
    # Point the router at the fixture wiki so endpoint tests use known content
    original = chat_router._WIKI_DIR
    chat_router._WIKI_DIR = fixture_wiki
    client = TestClient(app)
    chat_router._WIKI_DIR = original
    app.dependency_overrides.clear()
    return client


def test_post_chat_returns_200_with_answer_and_citations(fixture_wiki: Path):
    responses = iter(["ANSWER: RAG is a technique.\nCITATIONS: concepts/rag"])

    def fake_chat_fn(_messages: list[dict]) -> str:
        return next(responses)

    import app.routers.chat as chat_router
    original_wiki = chat_router._WIKI_DIR
    chat_router._WIKI_DIR = fixture_wiki
    app.dependency_overrides[get_chat_fn] = lambda: fake_chat_fn

    try:
        client = TestClient(app)
        response = client.post("/api/chat", json={"question": "What is RAG?"})
    finally:
        chat_router._WIKI_DIR = original_wiki
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "citations" in data


def test_post_chat_passes_history_to_ollama_fn(fixture_wiki: Path):
    """History should appear in the messages sent to the underlying chat callable."""
    captured: list[list[dict]] = []

    def fake_chat_fn(messages: list[dict]) -> str:
        captured.append(messages)
        return "ANSWER: Done.\nCITATIONS:"

    import app.routers.chat as chat_router
    original_wiki = chat_router._WIKI_DIR
    chat_router._WIKI_DIR = fixture_wiki
    app.dependency_overrides[get_chat_fn] = lambda: fake_chat_fn

    try:
        client = TestClient(app)
        client.post(
            "/api/chat",
            json={
                "question": "Follow-up",
                "history": [
                    {"role": "user", "content": "Prior question"},
                    {"role": "assistant", "content": "Prior answer"},
                ],
            },
        )
    finally:
        chat_router._WIKI_DIR = original_wiki
        app.dependency_overrides.clear()

    assert len(captured) == 1
    combined = " ".join(m["content"] for m in captured[0])
    assert "Prior question" in combined
    assert "Prior answer" in combined


def test_post_chat_empty_history_is_valid(fixture_wiki: Path):
    def fake_chat_fn(_messages: list[dict]) -> str:
        return "ANSWER: Fine.\nCITATIONS:"

    import app.routers.chat as chat_router
    original_wiki = chat_router._WIKI_DIR
    chat_router._WIKI_DIR = fixture_wiki
    app.dependency_overrides[get_chat_fn] = lambda: fake_chat_fn

    try:
        client = TestClient(app)
        response = client.post("/api/chat", json={"question": "Hello?"})
    finally:
        chat_router._WIKI_DIR = original_wiki
        app.dependency_overrides.clear()

    assert response.status_code == 200
