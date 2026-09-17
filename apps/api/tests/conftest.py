from __future__ import annotations

from pathlib import Path


def write_wiki_page(wiki_dir: Path, rel_path: str, content: str) -> None:
    """Write a wiki page to the given directory, creating parent directories as needed."""
    p = wiki_dir / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
