"""
Ingest CLI — ingests local markdown files into the wiki.
Usage: uv run ingest <path/to/doc.md> [<path/to/doc2.md> ...]

Copies each file to wiki/raw/<slug>.md, synthesizes source pages, applies
the ≥2 rule to produce concept/entity pages, and rebuilds domain indexes
and the root index.
"""
import sys
from pathlib import Path

import anthropic

from core.orchestrate import run_ingest
from core.synthesize import make_source_synthesize_fn, make_term_synthesize_fn
from core.wiki_repository import FilesystemWikiRepository

# wiki/ lives at the repo root, one level above scripts/
_WIKI_DIR = Path(__file__).parent.parent / "wiki"


def main() -> None:
    """Entry point for the ingest CLI.

    Raises:
        SystemExit: On validation errors or if any doc fails to ingest.
    """
    args = sys.argv[1:]
    if not args:
        print("Usage: uv run ingest <path/to/doc.md> [<path/to/doc2.md> ...]")
        sys.exit(1)

    doc_paths: list[Path] = []
    errors = False
    for arg in args:
        doc_path = Path(arg).resolve()
        if not doc_path.exists():
            print(f"[error] file not found: {doc_path}", file=sys.stderr)
            errors = True
            continue
        if doc_path.suffix != ".md":
            print(f"[error] expected a .md file: {doc_path}", file=sys.stderr)
            errors = True
            continue
        doc_paths.append(doc_path)

    if errors:
        sys.exit(1)

    client = anthropic.Anthropic()
    repo = FilesystemWikiRepository(_WIKI_DIR)
    synthesize_source = make_source_synthesize_fn(client)
    synthesize_term = make_term_synthesize_fn(client)

    print(f"[ingest] ingesting {len(doc_paths)} doc(s) ...")
    try:
        run_ingest(doc_paths, repo, synthesize_source, synthesize_term)
        print("[ingest] done")
    except Exception as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
