from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from core.chat_backends import make_bedrock_chat_fn


def _mock_converse_response(text: str) -> dict:
    return {
        "output": {
            "message": {
                "content": [{"text": text}]
            }
        }
    }


def test_make_bedrock_chat_fn_returns_callable():
    fn = make_bedrock_chat_fn(model_id="anthropic.claude-3-haiku-20240307-v1:0", region="us-east-1")
    assert callable(fn)


def test_make_bedrock_chat_fn_calls_converse():
    mock_client = MagicMock()
    mock_client.converse.return_value = _mock_converse_response("Bedrock says hello")

    with patch("core.chat_backends.boto3.client", return_value=mock_client):
        fn = make_bedrock_chat_fn(model_id="anthropic.claude-3-haiku-20240307-v1:0", region="us-east-1")

    result = fn("system prompt", "user message")

    assert result == "Bedrock says hello"
    call_kwargs = mock_client.converse.call_args.kwargs
    assert call_kwargs["modelId"] == "anthropic.claude-3-haiku-20240307-v1:0"
    assert call_kwargs["system"] == [{"text": "system prompt"}]
    assert call_kwargs["messages"][0]["role"] == "user"
    assert call_kwargs["messages"][0]["content"][0]["text"] == "user message"


def test_make_bedrock_chat_fn_wraps_client_error():
    from botocore.exceptions import ClientError

    mock_client = MagicMock()
    mock_client.converse.side_effect = ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "denied"}}, "Converse"
    )

    with patch("core.chat_backends.boto3.client", return_value=mock_client):
        fn = make_bedrock_chat_fn(model_id="anthropic.claude-3-haiku-20240307-v1:0", region="us-east-1")

    with pytest.raises(RuntimeError, match="Bedrock request failed"):
        fn("sys", "usr")


@pytest.mark.skipif(
    not os.environ.get("AWS_REGION"),
    reason="AWS_REGION not set — skipping live Bedrock integration test",
)
def test_bedrock_integration_live():
    model_id = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
    region = os.environ["AWS_REGION"]
    fn = make_bedrock_chat_fn(model_id=model_id, region=region)
    reply = fn("You are a test assistant.", "Reply with the single word: pong")
    assert reply.strip(), "Expected non-empty reply from Bedrock"
