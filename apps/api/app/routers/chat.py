from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated, Callable

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.services.chat_service import ChatResponse, make_ollama_fn, navigate_and_answer

router = APIRouter(prefix="/api", tags=["chat"])

# WIKI_DIR env var lets deployments point at any wiki location without code changes.
# Falls back to five levels up from this file: apps/api/app/routers/ → repo root → wiki/
_WIKI_DIR = Path(os.environ.get("WIKI_DIR", Path(__file__).parent.parent.parent.parent.parent / "wiki"))
_OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
_OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")


class MessageDict(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    question: str
    history: list[MessageDict] = []


def get_chat_fn() -> Callable[[list[dict[str, str]]], str]:
    """Dependency that builds the Ollama callable for injection."""
    return make_ollama_fn(model=_OLLAMA_MODEL, base_url=_OLLAMA_BASE_URL)


@router.post("/chat", response_model=ChatResponse)
def post_chat(
    body: ChatRequest,
    chat_fn: Annotated[Callable[[list[dict[str, str]]], str], Depends(get_chat_fn)],
) -> ChatResponse:
    """Answer a question by progressively navigating the wiki.

    The backend is stateless — history is passed by the client on each request.
    """
    history = [{"role": m.role, "content": m.content} for m in body.history]
    return navigate_and_answer(body.question, history, _WIKI_DIR, chat_fn)
