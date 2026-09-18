"""Wiki health check — validates acceptance criteria for a re-ingest run.

Usage:
    uv run python check_wiki_health.py [wiki-dir]

Exits 0 if the wiki passes all checks, 1 if any check fails.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

_WIKI_DIR = Path(__file__).parent.parent / 'wiki'
_WIKILINK_RE = re.compile(r'\[\[([^\]]+)\]\]')


@dataclass
class HealthReport:
    """Results of a wiki health check."""

    malformed_sources: list[str] = field(default_factory=list)
    sources_without_wikilinks: list[str] = field(default_factory=list)
    # Maps bare-term wikilink to slugs of source pages that mention it (≥2 only)
    qualifying_terms: dict[str, list[str]] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.malformed_sources and not self.sources_without_wikilinks


def check_wiki_health(wiki_dir: Path = _WIKI_DIR) -> HealthReport:
    """Scan wiki/sources/ and return a HealthReport with any issues found.

    A source page is malformed if it has no YAML frontmatter block.
    A source page is link-free if it contains no bare [[wikilinks]].
    Qualifying terms are bare wikilinks that appear in ≥2 distinct source pages.

    Args:
        wiki_dir: Root wiki directory (contains sources/, concepts/, etc.).

    Returns:
        HealthReport with per-check findings.
    """
    sources_dir = wiki_dir / 'sources'
    report = HealthReport()

    if not sources_dir.exists():
        return report

    term_to_slugs: dict[str, list[str]] = {}

    for md_file in sorted(sources_dir.glob('*.md')):
        slug = md_file.stem
        content = md_file.read_text(encoding='utf-8')

        if not content.startswith('---'):
            report.malformed_sources.append(slug)
            continue

        bare_links = [
            link for link in _WIKILINK_RE.findall(content)
            if '/' not in link
        ]
        if not bare_links:
            report.sources_without_wikilinks.append(slug)

        for term in bare_links:
            term_to_slugs.setdefault(term, []).append(slug)

    report.qualifying_terms = {
        term: slugs
        for term, slugs in term_to_slugs.items()
        if len(slugs) >= 2
    }
    return report


def _print_report(report: HealthReport, wiki_dir: Path) -> None:
    sources_dir = wiki_dir / 'sources'
    concepts_dir = wiki_dir / 'concepts'

    source_count = len(list(sources_dir.glob('*.md'))) if sources_dir.exists() else 0
    concept_count = len(list(concepts_dir.glob('*.md'))) if concepts_dir.exists() else 0

    print(f'wiki/sources/  {source_count} page(s)')
    print(f'wiki/concepts/ {concept_count} page(s)')
    print()

    if report.malformed_sources:
        print(f'[FAIL] Malformed source pages ({len(report.malformed_sources)}):')
        for slug in report.malformed_sources:
            print(f'       {slug}')
    else:
        print('[OK]   All source pages have YAML frontmatter')

    if report.sources_without_wikilinks:
        print(f'[FAIL] Source pages with no wikilinks ({len(report.sources_without_wikilinks)}):')
        for slug in report.sources_without_wikilinks:
            print(f'       {slug}')
    else:
        print('[OK]   All source pages have at least one [[wikilink]]')

    if report.qualifying_terms:
        print(f'[OK]   Terms qualifying for ≥2 rule ({len(report.qualifying_terms)}):')
        for term, slugs in list(report.qualifying_terms.items())[:5]:
            print(f'       [[{term}]] in: {slugs}')
        if len(report.qualifying_terms) > 5:
            print(f'       … and {len(report.qualifying_terms) - 5} more')
    else:
        print('[WARN] No terms qualify under the ≥2 rule yet')


def main() -> None:
    wiki_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else _WIKI_DIR
    report = check_wiki_health(wiki_dir)
    _print_report(report, wiki_dir)
    sys.exit(0 if report.ok else 1)


if __name__ == '__main__':
    main()
