from pathlib import Path
from typing import Callable
import re


def _slugify(name: str) -> str:
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def ingest_doc(
    doc_path: Path,
    wiki_dir: Path,
    synthesize_fn: Callable[[str, str], str],
) -> None:
    slug = _slugify(doc_path.stem)
    if not slug:
        raise ValueError(f"Cannot derive a slug from filename {doc_path.name!r}")
    content = doc_path.read_text()

    raw_path = wiki_dir / "raw" / f"{slug}.md"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(content)

    source_page = synthesize_fn(content, slug)

    source_path = wiki_dir / "sources" / f"{slug}.md"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(source_page)
