"""
Ingest CLI — placeholder.
Usage: uv run ingest <source> [<source> ...]
"""
import sys


def main():
    sources = sys.argv[1:]
    if not sources:
        print("Usage: uv run ingest <source> [<source> ...]")
        sys.exit(1)
    for source in sources:
        print(f"[ingest] {source} — not yet implemented")


if __name__ == "__main__":
    main()
