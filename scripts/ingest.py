"""
Ingest CLI — ingests a local markdown file into the wiki.
Usage: uv run ingest <path/to/doc.md> [<path/to/doc2.md> ...]

Copies the file to wiki/raw/<slug>.md and synthesizes a source page
at wiki/sources/<slug>.md using the Claude API.
"""
import sys
from pathlib import Path

import anthropic

from core.ingest_doc import ingest_doc
from core.synthesize import make_synthesize_fn

_WIKI_DIR = Path(__file__).parent.parent / "wiki"


def main():
    sources = sys.argv[1:]
    if not sources:
        print("Usage: uv run ingest <path/to/doc.md> [<path/to/doc2.md> ...]")
        sys.exit(1)

    client = anthropic.Anthropic()
    synthesize = make_synthesize_fn(client)

    errors = False
    for source in sources:
        doc_path = Path(source).resolve()
        if not doc_path.exists():
            print(f"[error] file not found: {doc_path}", file=sys.stderr)
            errors = True
            continue
        if doc_path.suffix != ".md":
            print(f"[error] expected a .md file: {doc_path}", file=sys.stderr)
            errors = True
            continue

        print(f"[ingest] {doc_path.name} ...", end=" ", flush=True)
        try:
            ingest_doc(doc_path, _WIKI_DIR, synthesize)
            print("done")
        except Exception as exc:
            print(f"failed\n[error] {exc}", file=sys.stderr)
            errors = True

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
