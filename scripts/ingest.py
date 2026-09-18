"""
Ingest CLI — ingests local markdown files or Google Docs into the wiki.
Usage: uv run ingest <path/to/doc.md|google-doc-url> [...]

For Google Doc URLs, authenticates via OAuth on first run (opens browser)
and caches the token at ~/.config/coe-wiki/token.json. Subsequent runs are
silent. Requires credentials.json in the scripts/ directory.
"""
import os
import sys
import tempfile
from contextlib import ExitStack
from pathlib import Path

from core.chat_backends import make_ollama_chat_fn
from core.drive import build_drive_service, extract_file_id, fetch_doc_as_markdown, is_drive_url
from core.orchestrate import run_ingest
from core.slug import slugify
from core.synthesize import make_source_synthesize_fn, make_term_synthesize_fn
from core.wiki_repository import FilesystemWikiRepository

# wiki/ lives at the repo root, one level above scripts/
_WIKI_DIR = Path(__file__).parent.parent / "wiki"
_CREDENTIALS = Path(__file__).parent / "credentials.json"
_TOKEN_CACHE = Path.home() / ".config" / "coe-wiki" / "token.json"


def _resolve_doc_paths(
    args: list[str], tmp_dir: Path | None
) -> list[Path]:
    """Resolve CLI arguments to local markdown file paths.

    Local paths are validated directly. Google Doc URLs are fetched and
    written into tmp_dir (which the caller owns and must clean up).

    Args:
        args: Raw CLI arguments (local paths or Google Doc URLs).
        tmp_dir: Directory for Drive-fetched files, or None if no Drive URLs expected.

    Returns:
        List of resolved Path objects pointing to markdown files.

    Raises:
        SystemExit: On validation errors (missing file, wrong extension,
            missing credentials, Drive API errors).
    """
    drive_urls: list[str] = []
    errors = False
    doc_paths: list[Path] = []

    for arg in args:
        if is_drive_url(arg):
            drive_urls.append(arg)
        else:
            p = Path(arg).resolve()
            if not p.exists():
                print(f"[error] file not found: {p}", file=sys.stderr)
                errors = True
            elif p.suffix != ".md":
                print(f"[error] expected a .md file: {p}", file=sys.stderr)
                errors = True
            else:
                doc_paths.append(p)

    if errors:
        sys.exit(1)

    if drive_urls:
        if not _CREDENTIALS.exists():
            print(
                f"[error] Google Drive credentials not found at {_CREDENTIALS}.\n"
                "Download credentials.json from Google Cloud Console and place it in scripts/.",
                file=sys.stderr,
            )
            sys.exit(1)

        print("[drive] authenticating with Google Drive ...")
        try:
            service = build_drive_service(_CREDENTIALS, _TOKEN_CACHE)
        except Exception as exc:
            print(f"[error] Google Drive authentication failed: {exc}", file=sys.stderr)
            sys.exit(1)

        assert tmp_dir is not None
        used_slugs: set[str] = set()
        for url in drive_urls:
            try:
                file_id = extract_file_id(url)
            except ValueError as exc:
                print(f"[error] {exc}", file=sys.stderr)
                sys.exit(1)

            print(f"[drive] fetching {file_id} ...", end=" ", flush=True)
            try:
                title, content = fetch_doc_as_markdown(file_id, service)
            except Exception as exc:
                print(f"failed\n[error] {exc}", file=sys.stderr)
                sys.exit(1)

            base_slug = slugify(title) or file_id
            # Avoid silent collision when two docs slugify to the same name
            slug = base_slug
            counter = 1
            while slug in used_slugs:
                slug = f"{base_slug}-{counter}"
                counter += 1
            used_slugs.add(slug)

            tmp_file = tmp_dir / f"{slug}.md"
            tmp_file.write_text(content)
            doc_paths.append(tmp_file)
            print(f"ok ({title!r})")

    return doc_paths


def main() -> None:
    """Entry point for the ingest CLI.

    Raises:
        SystemExit: On validation errors or if any doc fails to ingest.
    """
    args = sys.argv[1:]
    if not args:
        print("Usage: uv run ingest <path/to/doc.md|google-doc-url> [...]")
        sys.exit(1)

    has_drive = any(is_drive_url(a) for a in args)
    # TemporaryDirectory is always created so _resolve_doc_paths gets a valid path;
    # it is cleaned up on exit even if ingest fails
    with tempfile.TemporaryDirectory(prefix="coe-wiki-drive-") as _tmp:
        tmp_dir = Path(_tmp) if has_drive else None
        doc_paths = _resolve_doc_paths(args, tmp_dir)

        repo = FilesystemWikiRepository(_WIKI_DIR)
        chat_fn = make_ollama_chat_fn(
            model=os.environ.get("OLLAMA_MODEL", "llama3.2:3b"),
            base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        )
        synthesize_source = make_source_synthesize_fn(chat_fn)
        synthesize_term = make_term_synthesize_fn(chat_fn)

        print(f"[ingest] ingesting {len(doc_paths)} doc(s) ...")
        try:
            run_ingest(doc_paths, repo, synthesize_source, synthesize_term)
            print("[ingest] done")
        except Exception as exc:
            print(f"[error] {exc}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
