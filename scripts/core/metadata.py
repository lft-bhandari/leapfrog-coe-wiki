from __future__ import annotations

import json
import re

from pydantic import BaseModel, Field

from core import logger
from core.chat_backends import ChatFn

# Only the top of the document contains the metadata header
_HEADER_CHARS = 3_000

_JSON_FENCE_RE = re.compile(r'```(?:json)?\s*([\s\S]*?)```')

_EXTRACTION_SYSTEM = """\
Extract document metadata from the provided text and return ONLY a JSON object with these keys:
- author: list of strings (from "Prepared by" field)
- reviewed_by: list of strings (from "Reviewed By" field)
- documented_date: string (from "Documented Date" field)
- last_updated_date: string (from "Last Updated Date" field)
- review_cycle: string (from "Review Cycle" field)

If a field is absent or unclear, omit it from the JSON. Return ONLY the JSON object, no explanation."""


class DocMetadata(BaseModel):
    """Structured metadata extracted from a CoE document header."""

    author: list[str] = Field(default_factory=lambda: ['Unknown'])
    reviewed_by: list[str] = Field(default_factory=lambda: ['Unknown'])
    documented_date: str = 'Unknown'
    last_updated_date: str = 'Unknown'
    review_cycle: str = 'Unknown'

    def is_all_unknown(self) -> bool:
        return (
            self.author == ['Unknown']
            and self.reviewed_by == ['Unknown']
            and self.documented_date == 'Unknown'
            and self.last_updated_date == 'Unknown'
            and self.review_cycle == 'Unknown'
        )


def _parse_json(raw: str) -> dict:
    fence_match = _JSON_FENCE_RE.search(raw)
    text = fence_match.group(1) if fence_match else raw
    try:
        parsed = json.loads(text.strip())
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def extract_metadata(
    content: str,
    chat_fn: ChatFn,
    is_drive_doc: bool = False,
) -> DocMetadata:
    """Extract CoE document metadata from the top of a markdown document.

    Sends only the first _HEADER_CHARS characters to the LLM to minimise
    token usage — the metadata header is always at the top of CoE docs.

    Args:
        content: Full document markdown text.
        chat_fn: LLM backend callable (system_prompt, user_message) -> reply.
        is_drive_doc: When True, emits a [warn] if all fields remain Unknown
            (signals the document may not follow the CoE template).

    Returns:
        DocMetadata with extracted fields; missing fields default to 'Unknown'.
    """
    snippet = content[:_HEADER_CHARS]
    raw = chat_fn(_EXTRACTION_SYSTEM, snippet)
    data = _parse_json(raw)

    try:
        meta = DocMetadata.model_validate(data)
    except Exception:
        meta = DocMetadata()

    if is_drive_doc and meta.is_all_unknown():
        logger.warn('no metadata header found in Drive doc — CoE template may not be present')

    return meta
