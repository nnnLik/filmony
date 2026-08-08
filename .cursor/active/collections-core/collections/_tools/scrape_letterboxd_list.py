#!/usr/bin/env python3
"""Scrape a Letterboxd official list into rank/name/year/letterboxd_uri JSON.

Run from backend:

  cd backend && uv run python ../.cursor/active/collections-core/collections/_tools/scrape_letterboxd_list.py --help

With ``--slug horror_250``, writes ``letterboxd_<slug>.json`` and ``.meta.json`` under
``collections/<slug>/intermediate/`` (directories created as needed).
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

COLLECTIONS_ROOT = Path(__file__).resolve().parent.parent

USER_AGENT = "Mozilla/5.0 (compatible; FilmonyScraper/1.0; +https://github.com/filmony)"
DEFAULT_DELAY_SECONDS = 1.0

# List rows: li.posteritem.numbered-list-item > div.react-component.LazyPoster
LAZY_POSTER_ITEM_RE = re.compile(
    r'<li class="posteritem numbered-list-item"[^>]*>\s*'
    r'<div class="react-component"[^>]*data-component-class="LazyPoster"[^>]*'
    r'data-item-name="([^"]*)"[^>]*data-item-link="([^"]*)"',
    re.DOTALL,
)
FILMS_COUNT_RE = re.compile(r"\b(\d+)\s+films\b", re.IGNORECASE)
PAGINATE_PAGE_NUM_RE = re.compile(r'<div class="paginate-pages[^"]*">(.*?)</div>', re.DOTALL)
PAGE_LINK_RE = re.compile(r"/page/(\d+)/")
TITLE_YEAR_RE = re.compile(r"^(.*)\s+\((\d{4})\)$")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_list_url(url: str) -> str:
    url = url.strip()
    if not url.endswith("/"):
        url += "/"
    return url


def _page_url(base_url: str, page: int) -> str:
    base_url = _normalize_list_url(base_url)
    if page <= 1:
        return base_url
    return f"{base_url}page/{page}/"


def fetch_html(url: str, *, timeout: float = 30.0) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} fetching {url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error fetching {url}: {exc.reason}") from exc


def parse_expected_count(page_html: str) -> int | None:
    match = FILMS_COUNT_RE.search(page_html)
    if not match:
        return None
    return int(match.group(1))


def parse_last_page(page_html: str) -> int:
    paginate_match = PAGINATE_PAGE_NUM_RE.search(page_html)
    page_numbers: list[int] = []
    if paginate_match:
        page_numbers.extend(int(n) for n in re.findall(r">(\d+)<", paginate_match.group(1)))
    page_numbers.extend(int(n) for n in PAGE_LINK_RE.findall(page_html))
    return max(page_numbers) if page_numbers else 1


def split_title_year(display_name: str) -> tuple[str, int | None]:
    decoded = html.unescape(display_name).strip()
    match = TITLE_YEAR_RE.match(decoded)
    if not match:
        return decoded, None
    return match.group(1).strip(), int(match.group(2))


def parse_films(page_html: str) -> list[dict[str, Any]]:
    films: list[dict[str, Any]] = []
    for display_name, item_link in LAZY_POSTER_ITEM_RE.findall(page_html):
        name, year = split_title_year(display_name)
        path = item_link.strip()
        if not path.startswith("/"):
            path = f"/{path}"
        films.append(
            {
                "name": name,
                "year": year,
                "letterboxd_uri": f"https://letterboxd.com{path}",
            }
        )
    return films


def scrape_list(
    url: str,
    *,
    delay_seconds: float = DEFAULT_DELAY_SECONDS,
) -> tuple[list[dict[str, Any]], int | None, int]:
    base_url = _normalize_list_url(url)
    first_html = fetch_html(_page_url(base_url, 1))
    expected_count = parse_expected_count(first_html)
    last_page = parse_last_page(first_html)

    all_films: list[dict[str, Any]] = []
    for page in range(1, last_page + 1):
        page_html = first_html if page == 1 else fetch_html(_page_url(base_url, page))
        page_films = parse_films(page_html)
        if not page_films:
            raise RuntimeError(f"No films parsed on page {page} of {base_url}")
        all_films.extend(page_films)
        if page < last_page and delay_seconds > 0:
            time.sleep(delay_seconds)

    ranked: list[dict[str, Any]] = []
    for index, film in enumerate(all_films, start=1):
        ranked.append({"rank": index, **film})

    return ranked, expected_count, len(ranked)


def write_outputs(
    output_dir: Path,
    slug: str,
    *,
    source_url: str,
    items: list[dict[str, Any]],
    expected_count: int | None,
    actual_count: int,
) -> tuple[Path, Path]:
    json_path = output_dir / f"letterboxd_{slug}.json"
    meta_path = output_dir / f"letterboxd_{slug}.meta.json"

    json_path.write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    meta = {
        "source_url": source_url,
        "scraped_at": _utc_now_iso(),
        "expected_count": expected_count,
        "actual_count": actual_count,
    }
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return json_path, meta_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scrape a Letterboxd official list into JSON + meta files.",
    )
    parser.add_argument(
        "--url",
        required=True,
        help="Letterboxd list URL (e.g. https://letterboxd.com/official/list/top-250-horror-films/)",
    )
    parser.add_argument(
        "--slug",
        required=True,
        help="Output slug; writes letterboxd_<slug>.json and letterboxd_<slug>.meta.json",
    )
    parser.add_argument(
        "--expected-count",
        type=int,
        default=None,
        help="Fail with exit code 1 if actual scraped count does not match this value",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY_SECONDS,
        help=f"Seconds to wait between page fetches (default: {DEFAULT_DELAY_SECONDS})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for output files (default: collections/<slug>/intermediate/ or script dir)",
    )
    return parser


def _resolve_output_dir(args: argparse.Namespace) -> Path:
    if args.output_dir is not None:
        return args.output_dir
    if args.slug:
        return COLLECTIONS_ROOT / args.slug / "intermediate"
    return Path(__file__).resolve().parent


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    output_dir = _resolve_output_dir(args)
    output_dir.mkdir(parents=True, exist_ok=True)

    source_url = _normalize_list_url(args.url)
    try:
        items, page_expected_count, actual_count = scrape_list(
            source_url,
            delay_seconds=args.delay,
        )
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    expected_count = args.expected_count if args.expected_count is not None else page_expected_count
    json_path, meta_path = write_outputs(
        output_dir,
        args.slug,
        source_url=source_url,
        items=items,
        expected_count=expected_count,
        actual_count=actual_count,
    )

    print(f"Wrote {actual_count} items to {json_path}")
    print(f"Wrote meta to {meta_path}")
    if page_expected_count is not None:
        print(f"Page-reported film count: {page_expected_count}")
    if expected_count is not None and actual_count != expected_count:
        print(
            f"error: count mismatch — expected {expected_count}, got {actual_count}",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
