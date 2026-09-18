from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from ingest import _make_chat_fn


def test_defaults_to_ollama(monkeypatch):
    monkeypatch.delenv("SYNTHESIS_BACKEND", raising=False)
    with patch("ingest.make_ollama_chat_fn") as mock_ollama:
        mock_ollama.return_value = MagicMock()
        _make_chat_fn()
        mock_ollama.assert_called_once()


def test_explicit_ollama(monkeypatch):
    monkeypatch.setenv("SYNTHESIS_BACKEND", "ollama")
    with patch("ingest.make_ollama_chat_fn") as mock_ollama:
        mock_ollama.return_value = MagicMock()
        _make_chat_fn()
        mock_ollama.assert_called_once()


def test_selects_bedrock_with_region(monkeypatch):
    monkeypatch.setenv("SYNTHESIS_BACKEND", "bedrock")
    monkeypatch.setenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
    monkeypatch.setenv("AWS_REGION", "eu-west-1")
    with patch("ingest.make_bedrock_chat_fn") as mock_bedrock:
        mock_bedrock.return_value = MagicMock()
        _make_chat_fn()
        mock_bedrock.assert_called_once_with(
            model_id="anthropic.claude-3-haiku-20240307-v1:0",
            region="eu-west-1",
        )


def test_selects_bedrock_without_region_lets_boto3_resolve(monkeypatch):
    monkeypatch.setenv("SYNTHESIS_BACKEND", "bedrock")
    monkeypatch.delenv("AWS_REGION", raising=False)
    with patch("ingest.make_bedrock_chat_fn") as mock_bedrock:
        mock_bedrock.return_value = MagicMock()
        _make_chat_fn()
        mock_bedrock.assert_called_once_with(
            model_id=mock_bedrock.call_args.kwargs["model_id"],
            region=None,
        )


def test_unknown_backend_raises(monkeypatch):
    monkeypatch.setenv("SYNTHESIS_BACKEND", "gpt5000")
    with pytest.raises(ValueError, match="Unknown SYNTHESIS_BACKEND"):
        _make_chat_fn()
