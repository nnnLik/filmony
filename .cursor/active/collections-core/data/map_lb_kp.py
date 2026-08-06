#!/usr/bin/env python3
"""Map Letterboxd Top 500 → Kinopoisk IDs via unofficial API (no DB).

Strategy:
1) Scrape IMDb id from each Letterboxd film page (async).
2) Resolve via GET /api/v2.2/films?imdbId=tt…
3) Fallback: GET /api/v2.2/films?keyword=…&yearFrom=&yearTo=

Outputs (same directory as this script by default, or /tmp when --in-container):
  letterboxd_top_500_kinopoisk.json
  letterboxd_top_500_kinopoisk.txt
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
        for attempt in range(30):
            async with self._sem:
                resp = await client.get(url, params=params, headers=self._headers)
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
        name: str,
        year: int | None,
    ) -> int | None:
        params: dict[str, Any] = {
            "keyword": name,
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
            if accept_keyword_match(lb_name=name, lb_year=year, item=item):
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


async def map_one(
    *,
    client: httpx.AsyncClient,
    kp: KinopoiskUnofficialClient,
    lb_sem: asyncio.Semaphore,
    entry: dict[str, Any],
) -> dict[str, Any]:
    rank = int(entry["rank"])
    name = str(entry["name"])
    year_raw = entry.get("year")
    year = int(year_raw) if year_raw is not None else None
    uri = str(entry.get("letterboxd_uri") or "")

    imdb_id: str | None = None
    if uri:
        imdb_id = await fetch_imdb_from_letterboxd(client, lb_sem, uri)

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
            kid = await kp.by_keyword_year(client, name=name, year=year)
            if kid is not None:
                method = "keyword"
        except httpx.HTTPError as exc:
            print(f"KP keyword error rank={rank} {name!r}: {exc}", file=sys.stderr)

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
                kid = await kp.by_imdb_id(client, known_imdb)
                method = "imdbId" if kid is not None else "TODO"
                if kid is None:
                    kid2 = await kp.by_keyword_year(client, name=name, year=year)
                    if kid2 is not None:
                        kid = kid2
                        method = "keyword"
                return {
                    "rank": rank,
                    "letterboxd_name": name,
                    "year": year,
                    "letterboxd_uri": uri or None,
                    "imdb_id": known_imdb,
                    "kinopoisk_id": kid if kid is not None else "TODO",
                    "match_method": method,
                }
            return await map_one(client=client, kp=kp, lb_sem=lb_sem, entry=entry)

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

    print("\n=== SUMMARY ===")
    print(f"Total: {len(rows_sorted)}")
    print(f"Matched: {matched} (imdbId={by_imdb}, keyword={by_kw})")
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


def parse_args() -> argparse.Namespace:
    here = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--input",
        default=str(here / "letterboxd_top_500.json"),
    )
    p.add_argument(
        "--output-json",
        default=str(here / "letterboxd_top_500_kinopoisk.json"),
    )
    p.add_argument(
        "--output-txt",
        default=str(here / "letterboxd_top_500_kinopoisk.txt"),
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
    return p.parse_args()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(amain(parse_args())))
