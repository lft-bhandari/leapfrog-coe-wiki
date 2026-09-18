from __future__ import annotations

from unittest.mock import MagicMock, patch

from core.chat_backends import ChatFn, make_ollama_chat_fn


def test_chat_fn_type_alias_is_callable():
    fn: ChatFn = lambda system, user: "reply"
    assert fn("sys", "usr") == "reply"


def test_make_ollama_chat_fn_returns_callable():
    fn = make_ollama_chat_fn(model="llama3.2:3b", base_url="http://localhost:11434")
    assert callable(fn)


def test_make_ollama_chat_fn_posts_to_ollama():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"message": {"content": "hello"}}

    with patch("core.chat_backends.httpx.post", return_value=mock_response) as mock_post:
        fn = make_ollama_chat_fn(model="llama3.2:3b", base_url="http://localhost:11434")
        result = fn("system prompt", "user message")

    assert result == "hello"
    call_kwargs = mock_post.call_args
    payload = call_kwargs.kwargs["json"] if call_kwargs.kwargs else call_kwargs[1]["json"]
    assert payload["model"] == "llama3.2:3b"
    assert payload["messages"][0]["content"] == "system prompt"
    assert payload["messages"][1]["content"] == "user message"
