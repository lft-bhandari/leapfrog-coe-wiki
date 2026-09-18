from __future__ import annotations

from typing import Callable

import boto3
import httpx
from botocore.exceptions import BotoCoreError, ClientError

# (system_prompt, user_message) -> reply
ChatFn = Callable[[str, str], str]


def make_ollama_chat_fn(
    model: str = "llama3.2:3b",
    base_url: str = "http://localhost:11434",
) -> ChatFn:
    """Return a ChatFn that calls the Ollama /api/chat endpoint.

    Args:
        model: Ollama model name.
        base_url: Base URL of the Ollama API server.

    Returns:
        A callable (system_prompt, user_message) -> reply string.

    Raises:
        RuntimeError: If the Ollama request fails.
    """
    def _chat(system: str, user: str) -> str:
        try:
            resp = httpx.post(
                f"{base_url}/api/chat",
                json={
                    "model": model,
                    "stream": False,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
                timeout=120.0,
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"]
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc
        except (KeyError, ValueError) as exc:
            raise RuntimeError(f"Unexpected Ollama response shape: {exc}") from exc

    return _chat


def make_bedrock_chat_fn(
    model_id: str = "anthropic.claude-3-5-haiku-20241022-v1:0",
    region: str | None = None,
) -> ChatFn:
    """Return a ChatFn that calls the AWS Bedrock Converse API.

    Credentials and region are resolved from the standard AWS credential chain
    (env vars AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_SESSION_TOKEN /
    AWS_DEFAULT_REGION, ~/.aws/credentials, or an IAM role). Pass `region`
    explicitly only to override that chain.

    Args:
        model_id: Bedrock model ID (e.g. anthropic.claude-3-5-haiku-20241022-v1:0).
        region: AWS region name, or None to let boto3 resolve from its chain.

    Returns:
        A callable (system_prompt, user_message) -> reply string.

    Raises:
        RuntimeError: If the Bedrock request fails or the response is unexpected.
    """
    client = boto3.client("bedrock-runtime", region_name=region)

    def _chat(system: str, user: str) -> str:
        try:
            response = client.converse(
                modelId=model_id,
                system=[{"text": system}],
                messages=[{"role": "user", "content": [{"text": user}]}],
            )
            return response["output"]["message"]["content"][0]["text"]
        except (ClientError, BotoCoreError) as exc:
            raise RuntimeError(f"Bedrock request failed: {exc}") from exc
        except (KeyError, IndexError) as exc:
            raise RuntimeError(f"Unexpected Bedrock response shape: {exc}") from exc

    return _chat
