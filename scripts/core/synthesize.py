from datetime import datetime, timezone
import anthropic

_SYSTEM = """\
You are a wiki editor for a CoE knowledge base. Given a source document, produce a wiki source page in this exact format:

---
type: source
title: <title extracted from the document>
description: <one-sentence summary of the document's main contribution>
sources:
  - raw/<slug>.md
created: <ISO 8601 UTC timestamp>
---

## Summary

<3-7 sentence summary of the document's key claims. Use [[wikilinks]] around every concept, \
entity (tool, framework, standard, organisation), or named technique you mention. \
Wikilinks are the edges of the knowledge graph — be liberal with them.>

Output ONLY the wiki page. No preamble, no explanation."""


def make_synthesize_fn(client: anthropic.Anthropic):
    def synthesize(content: str, slug: str) -> str:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        user_msg = f"slug: {slug}\ncreated: {now}\n\n---\n\n{content}"
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            system=_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        )
        if message.stop_reason != "end_turn":
            raise RuntimeError(
                f"Synthesis truncated (stop_reason={message.stop_reason!r}). "
                "Increase max_tokens or shorten the source document."
            )
        block = message.content[0]
        if block.type != "text":
            raise RuntimeError(
                f"Expected a text block from the API, got {block.type!r}."
            )
        return block.text

    return synthesize
