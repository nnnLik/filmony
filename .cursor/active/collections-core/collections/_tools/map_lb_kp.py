#!/usr/bin/env python3
"""Map Letterboxd list JSON → Kinopoisk IDs via unofficial API (no DB).

Strategy:
1) Scrape IMDb id from each Letterboxd film page (async).
2) Resolve via GET /api/v2.2/films?imdbId=tt…
3) Fallback: GET /api/v2.2/films?keyword=…&yearFrom=&yearTo= (EN title)
4) Optional RU aliases (--ru-aliases): keyword search per alias query → match_method=keyword_ru

Run from backend (httpx on PYTHONPATH):

  cd backend && uv run python ../.cursor/active/collections-core/collections/_tools/map_lb_kp.py --help

With --slug horror_250, defaults read/write under collections/<slug>/intermediate/.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import httpx

COLLECTIONS_ROOT = Path(__file__).resolve().parent.parent

IMDB_RE = re.compile(r"imdb\.com/title/(tt\d+)", re.I)
LB_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


def _normalize_title(text: str) -> str:
    t = unicodedata.normalize("NFKD", text.casefold().strip())
    t = re.sub(r"[^\w\s]", " ", t)
    return " ".join(t.split())


def title_similarity(letterboxd_name: str, *candidates: str | None) -> float:
    lb = _normalize_title(letterboxd_name)
    if not lb:
        return 0.0
    best = 0.0
    for raw in candidates:
        if not raw or not str(raw).strip():
            continue
        cand = _normalize_title(str(raw))
        if not cand:
            continue
        best = max(best, SequenceMatcher(None, lb, cand).ratio())
        if lb in cand or cand in lb:
            best = max(best, 0.88)
    return best


def accept_keyword_match(
    *,
    lb_name: str,
    lb_year: int | None,
    item: dict[str, Any],
) -> bool:
    titles = (
        item.get("nameEn"),
        item.get("nameOriginal"),
        item.get("nameRu"),
    )
    sim = title_similarity(lb_name, *titles)
    year_raw = item.get("year")
    try:
        cy = int(year_raw) if year_raw is not None else None
    except (TypeError, ValueError):
        cy = None
    if lb_year is None or cy is None:
        return sim >= 0.72
    yd = abs(lb_year - cy)
    if yd == 0:
        return sim >= 0.55
    if yd == 1:
        return sim >= 0.65
    return sim >= 0.92


def load_ru_aliases(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Failed to load --ru-aliases {path}: {exc}", file=sys.stderr)
        return []
    if not isinstance(data, list):
        print(f"--ru-aliases must be a JSON array: {path}", file=sys.stderr)
        return []
    return [row for row in data if isinstance(row, dict)]


def find_ru_alias_queries(
    aliases: list[dict[str, Any]],
    *,
    imdb_id: str | None,
    letterboxd_name: str,
    year: int | None,
) -> list[str]:
    name_fold = letterboxd_name.casefold()
    for entry in aliases:
        entry_imdb = entry.get("imdb_id")
        if imdb_id and isinstance(entry_imdb, str) and entry_imdb == imdb_id:
            return _alias_query_list(entry)
        entry_name = entry.get("letterboxd_name")
        if not isinstance(entry_name, str):
            continue
        if entry_name.casefold() != name_fold:
            continue
        entry_year = entry.get("year")
        if year is not None and entry_year is not None:
            try:
                if int(entry_year) != year:
                    continue
            except (TypeError, ValueError):
                pass
        return _alias_query_list(entry)
    return []


def _alias_query_list(entry: dict[str, Any]) -> list[str]:
    raw = entry.get("queries")
    if not isinstance(raw, list):
        return []
    return [str(q).strip() for q in raw if isinstance(q, str) and str(q).strip()]


class KinopoiskUnofficialClient:
    def __init__(self, base_url: str, api_key: str, semaphore: asyncio.Semaphore) -> None:
        self._base = base_url.rstrip("/")
        self._headers = {"X-API-KEY": api_key, "Accept": "application/json"}
        self._sem = semaphore

    async def films_by_filters(
        self,
        client: httpx.AsyncClient,
        *,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        url = f"{self._base}/v2.2/films"
        last: httpx.Response | None = None
        transient_errors = (
            httpx.ReadError,
            httpx.ConnectError,
            httpx.TimeoutException,
            httpx.RemoteProtocolError,
        )
        for attempt in range(30):
            try:
                async with self._sem:
                    resp = await client.get(url, params=params, headers=self._headers)
            except transient_errors:
                await asyncio.sleep(min(8.0, 0.5 * (attempt + 1)))
                continue
            last = resp
            if resp.status_code == 429:
                # Official swagger documents 5 rps; back off hard and keep trying.
                await asyncio.sleep(min(8.0, 0.5 * (attempt + 1)))
                continue
            if resp.status_code >= 500:
                await asyncio.sleep(min(5.0, 0.4 * (attempt + 1)))
                continue
            resp.raise_for_status()
            return resp.json()
        if last is not None:
            last.raise_for_status()
        return {}

    async def by_imdb_id(self, client: httpx.AsyncClient, imdb_id: str) -> int | None:
        data = await self.films_by_filters(client, params={"imdbId": imdb_id, "page": 1})
        items = data.get("items") or []
        if not items:
            return None
        kid = items[0].get("kinopoiskId")
        return int(kid) if kid is not None else None

    async def by_keyword_year(
        self,
        client: httpx.AsyncClient,
        *,
        keyword: str,
        lb_name: str,
        year: int | None,
    ) -> int | None:
        params: dict[str, Any] = {
            "keyword": keyword,
            "page": 1,
            "type": "FILM",
            "order": "NUM_VOTE",
        }
        if year is not None:
            params["yearFrom"] = year
            params["yearTo"] = year
        data = await self.films_by_filters(client, params=params)
        items = list(data.get("items") or [])
        if not items and year is not None:
            params["yearFrom"] = year - 1
            params["yearTo"] = year + 1
            data = await self.films_by_filters(client, params=params)
            items = list(data.get("items") or [])
        for item in items:
            if accept_keyword_match(lb_name=lb_name, lb_year=year, item=item):
                kid = item.get("kinopoiskId")
                if kid is not None:
                    return int(kid)
        return None


async def fetch_imdb_from_letterboxd(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    uri: str,
) -> str | None:
    for attempt in range(4):
        try:
            async with sem:
                resp = await client.get(
                    uri,
                    headers={"User-Agent": LB_UA, "Accept-Language": "en-US,en;q=0.9"},
                    follow_redirects=True,
                )
            if resp.status_code in (429, 503):
                await asyncio.sleep(0.5 * (attempt + 1))
                continue
            if resp.status_code >= 400:
                return None
            m = IMDB_RE.search(resp.text)
            return m.group(1) if m else None
        except httpx.HTTPError:
            await asyncio.sleep(0.4 * (attempt + 1))
    return None


async def resolve_kinopoisk_id(
    *,
    client: httpx.AsyncClient,
    kp: KinopoiskUnofficialClient,
    rank: int,
    name: str,
    year: int | None,
    imdb_id: str | None,
    ru_aliases: list[dict[str, Any]],
) -> tuple[int | None, str]:
    kid: int | None = None
    method = "TODO"
    if imdb_id:
        try:
            kid = await kp.by_imdb_id(client, imdb_id)
            if kid is not None:
                method = "imdbId"
        except httpx.HTTPError as exc:
            print(f"KP imdb error rank={rank} {imdb_id}: {exc}", file=sys.stderr)

    if kid is None:
        try:
            kid = await kp.by_keyword_year(client, keyword=name, lb_name=name, year=year)
            if kid is not None:
                method = "keyword"
        except httpx.HTTPError as exc:
            print(f"KP keyword error rank={rank} {name!r}: {exc}", file=sys.stderr)

    if kid is None and ru_aliases:
        queries = find_ru_alias_queries(
            ru_aliases,
            imdb_id=imdb_id,
            letterboxd_name=name,
            year=year,
        )
        for query in queries:
            try:
                kid = await kp.by_keyword_year(client, keyword=query, lb_name=name, year=year)
            except httpx.HTTPError as exc:
                print(f"KP RU keyword error rank={rank} {query!r}: {exc}", file=sys.stderr)
                continue
            if kid is not None:
                method = "keyword_ru"
                break

    return kid, method


async def map_one(
    *,
    client: httpx.AsyncClient,
    kp: KinopoiskUnofficialClient,
    lb_sem: asyncio.Semaphore,
    entry: dict[str, Any],
    ru_aliases: list[dict[str, Any]],
) -> dict[str, Any]:
    rank = int(entry["rank"])
    name = str(entry["name"])
    year_raw = entry.get("year")
    year = int(year_raw) if year_raw is not None else None
    uri = str(entry.get("letterboxd_uri") or "")

    imdb_id: str | None = None
    if uri:
        imdb_id = await fetch_imdb_from_letterboxd(client, lb_sem, uri)

    kid, method = await resolve_kinopoisk_id(
        client=client,
        kp=kp,
        rank=rank,
        name=name,
        year=year,
        imdb_id=imdb_id,
        ru_aliases=ru_aliases,
    )

    return {
        "rank": rank,
        "letterboxd_name": name,
        "year": year,
        "letterboxd_uri": uri or None,
        "imdb_id": imdb_id,
        "kinopoisk_id": kid if kid is not None else "TODO",
        "match_method": method,
    }


def write_outputs(rows: list[dict[str, Any]], out_json: Path, out_txt: Path) -> None:
    rows_sorted = sorted(rows, key=lambda r: int(r["rank"]))
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_txt.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(rows_sorted, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = []
    for row in rows_sorted:
        kid = row["kinopoisk_id"]
        label = str(kid) if isinstance(kid, int) else "TODO"
        lines.append(f"{row['rank']}. {row['letterboxd_name']} — {label}")
    out_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_existing(out_json: Path) -> dict[int, dict[str, Any]]:
    if not out_json.exists():
        return {}
    try:
        data = json.loads(out_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, list):
        return {}
    out: dict[int, dict[str, Any]] = {}
    for row in data:
        if isinstance(row, dict) and isinstance(row.get("rank"), int):
            out[int(row["rank"])] = row
    return out


async def amain(args: argparse.Namespace) -> int:
    in_path = Path(args.input)
    out_json = Path(args.output_json)
    out_txt = Path(args.output_txt)

    api_key = os.environ.get("KINOPOISK_API_KEY", "").strip()
    base_url = os.environ.get(
        "KINOPOISK_API_BASE_URL",
        "https://kinopoiskapiunofficial.tech/api",
    ).strip()
    if not api_key:
        print("KINOPOISK_API_KEY is empty", file=sys.stderr)
        return 2

    ru_aliases = load_ru_aliases(Path(args.ru_aliases) if args.ru_aliases else None)

    entries = json.loads(in_path.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        print("input must be a JSON array", file=sys.stderr)
        return 2

    existing = load_existing(out_json) if args.resume else {}
    to_process: list[dict[str, Any]] = []
    kept: list[dict[str, Any]] = []
    for entry in entries:
        rank = int(entry["rank"])
        prev = existing.get(rank)
        if (
            args.resume
            and prev is not None
            and isinstance(prev.get("kinopoisk_id"), int)
            and not args.force_todos
        ):
            kept.append(prev)
            continue
        if args.resume and args.only_todos and prev is not None and isinstance(prev.get("kinopoisk_id"), int):
            kept.append(prev)
            continue
        # Prefer previously scraped imdb_id to avoid re-hitting Letterboxd.
        if prev and prev.get("imdb_id") and not entry.get("imdb_id"):
            entry = {**entry, "imdb_id": prev["imdb_id"]}
        to_process.append(entry)

    kp_sem = asyncio.Semaphore(args.kp_concurrency)
    lb_sem = asyncio.Semaphore(args.lb_concurrency)
    kp = KinopoiskUnofficialClient(base_url, api_key, kp_sem)

    timeout = httpx.Timeout(30.0, connect=10.0)
    limits = httpx.Limits(max_connections=args.kp_concurrency + args.lb_concurrency + 10)

    print(
        f"Mapping {len(to_process)}/{len(entries)} films "
        f"(kept={len(kept)}, kp_concurrency={args.kp_concurrency}, "
        f"lb_concurrency={args.lb_concurrency})",
        flush=True,
    )

    rows: list[dict[str, Any]] = list(kept)

    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        async def _one(entry: dict[str, Any]) -> dict[str, Any]:
            # If imdb already known from previous run, skip Letterboxd scrape.
            known_imdb = entry.get("imdb_id")
            if isinstance(known_imdb, str) and known_imdb.startswith("tt"):
                rank = int(entry["rank"])
                name = str(entry["name"])
                year_raw = entry.get("year")
                year = int(year_raw) if year_raw is not None else None
                uri = str(entry.get("letterboxd_uri") or "")
                kid, method = await resolve_kinopoisk_id(
                    client=client,
                    kp=kp,
                    rank=rank,
                    name=name,
                    year=year,
                    imdb_id=known_imdb,
                    ru_aliases=ru_aliases,
                )
                return {
                    "rank": rank,
                    "letterboxd_name": name,
                    "year": year,
                    "letterboxd_uri": uri or None,
                    "imdb_id": known_imdb,
                    "kinopoisk_id": kid if kid is not None else "TODO",
                    "match_method": method,
                }
            return await map_one(
                client=client,
                kp=kp,
                lb_sem=lb_sem,
                entry=entry,
                ru_aliases=ru_aliases,
            )

        tasks = [asyncio.create_task(_one(entry)) for entry in to_process]
        done = 0
        for coro in asyncio.as_completed(tasks):
            row = await coro
            rows.append(row)
            done += 1
            if done % 25 == 0 or done == len(tasks):
                write_outputs(rows, out_json, out_txt)
                matched = sum(1 for r in rows if isinstance(r["kinopoisk_id"], int))
                todos = sum(1 for r in rows if r["kinopoisk_id"] == "TODO")
                print(
                    f"Progress: {done}/{len(tasks)} matched={matched} TODO={todos}",
                    flush=True,
                )

    write_outputs(rows, out_json, out_txt)
    rows_sorted = sorted(rows, key=lambda r: int(r["rank"]))
    matched = sum(1 for r in rows_sorted if isinstance(r["kinopoisk_id"], int))
    todos = sum(1 for r in rows_sorted if r["kinopoisk_id"] == "TODO")
    by_imdb = sum(1 for r in rows_sorted if r.get("match_method") == "imdbId")
    by_kw = sum(1 for r in rows_sorted if r.get("match_method") == "keyword")
    by_ru = sum(1 for r in rows_sorted if r.get("match_method") == "keyword_ru")

    print("\n=== SUMMARY ===")
    print(f"Total: {len(rows_sorted)}")
    print(f"Matched: {matched} (imdbId={by_imdb}, keyword={by_kw}, keyword_ru={by_ru})")
    print(f"TODO: {todos}")
    print(f"JSON: {out_json}")
    print(f"TXT:  {out_txt}")
    print("\nFirst 5:")
    for row in rows_sorted[:5]:
        print(
            f"  {row['rank']}. {row['letterboxd_name']} — {row['kinopoisk_id']} "
            f"[{row.get('match_method')}] imdb={row.get('imdb_id')}"
        )
    print("\nSample TODOs:")
    for row in [r for r in rows_sorted if r["kinopoisk_id"] == "TODO"][:15]:
        print(f"  {row['rank']}. {row['letterboxd_name']} ({row['year']}) imdb={row.get('imdb_id')}")
    return 0


def _default_paths(slug: str | None) -> tuple[Path, Path, Path]:
    here = Path(__file__).resolve().parent
    if slug:
        intermediate = COLLECTIONS_ROOT / slug / "intermediate"
        return (
            intermediate / f"letterboxd_{slug}.json",
            intermediate / f"letterboxd_{slug}_kinopoisk.json",
            intermediate / f"letterboxd_{slug}_kinopoisk.txt",
        )
    return (
        here / "letterboxd_top_500.json",
        here / "letterboxd_top_500_kinopoisk.json",
        here / "letterboxd_top_500_kinopoisk.txt",
    )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--slug",
        default=None,
        help="Collection slug; default I/O under collections/<slug>/intermediate/",
    )
    p.add_argument(
        "--input",
        default=None,
        help="Letterboxd scrape JSON (default: letterboxd_<slug>.json in intermediate/)",
    )
    p.add_argument(
        "--output-json",
        default=None,
        help="Kinopoisk mapping JSON output (default: letterboxd_<slug>_kinopoisk.json)",
    )
    p.add_argument(
        "--output-txt",
        default=None,
        help="Human-readable mapping TXT (default: letterboxd_<slug>_kinopoisk.txt)",
    )
    p.add_argument(
        "--ru-aliases",
        default=None,
        metavar="PATH",
        help="Optional JSON list of RU keyword aliases for tier-3 matching",
    )
    p.add_argument("--kp-concurrency", type=int, default=4)
    p.add_argument("--lb-concurrency", type=int, default=8)
    p.add_argument("--resume", action="store_true", help="Keep already matched kinopoisk_id ints")
    p.add_argument(
        "--only-todos",
        action="store_true",
        help="With --resume, reprocess only TODO rows",
    )
    p.add_argument("--force-todos", action="store_true", help="Reprocess everything")
    args = p.parse_args()

    default_in, default_json, default_txt = _default_paths(args.slug)
    if args.input is None:
        args.input = str(default_in)
    if args.output_json is None:
        args.output_json = str(default_json)
    if args.output_txt is None:
        args.output_txt = str(default_txt)
    return args


if __name__ == "__main__":
    raise SystemExit(asyncio.run(amain(parse_args())))
