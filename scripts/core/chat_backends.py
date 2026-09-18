from __future__ import annotations

from typing import Callable

import httpx

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
