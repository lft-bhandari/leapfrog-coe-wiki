from __future__ import annotations

from core.synthesize import make_source_synthesize_fn, make_term_synthesize_fn


def _capture_chat_fn():
    """Returns a chat_fn and a list that records every (system, user) call."""
    calls: list[tuple[str, str]] = []

    def fn(system: str, user: str) -> str:
        calls.append((system, user))
        return "---\ntype: source\ntitle: T\ndescription: D\n---\n## Summary\n"

    return fn, calls


def test_source_synthesize_fn_calls_chat_fn():
    chat_fn, calls = _capture_chat_fn()
    synthesize = make_source_synthesize_fn(chat_fn)
    synthesize("doc content", "my-slug")
    assert len(calls) == 1
    system, user = calls[0]
    assert "my-slug" in user
    assert len(system) > 0


def test_term_synthesize_fn_calls_chat_fn():
    chat_fn, calls = _capture_chat_fn()
    synthesize = make_term_synthesize_fn(chat_fn)
    synthesize("RAG", ["source page one", "source page two"])
    assert len(calls) == 1
    system, user = calls[0]
    assert "RAG" in user
    assert len(system) > 0
