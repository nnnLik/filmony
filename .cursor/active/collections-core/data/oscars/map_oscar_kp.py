#!/usr/bin/env python3
"""Map Oscar Best Picture nominees → Kinopoisk IDs via unofficial API.

Strategy:
1) Read source JSON with pre-verified imdb_id per film.
2) Resolve via GET /api/v2.2/films?imdbId=tt…
3) Fallback: GET /api/v2.2/films?keyword=…&yearFrom=&yearTo=

Outputs (per ceremony year):
  oscars_YYYY_kinopoisk.json
  oscars_YYYY_kinopoisk.txt
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

IMDB_RE = re.compile(r"^tt\d+$")


def _normalize_title(text: str) -> str:
    t = unicodedata.normalize("NFKD", text.casefold().strip())
    t = re.sub(r"[^\w\s]", " ", t)
    return " ".join(t.split())


def title_similarity(source_name: str, *candidates: str | None) -> float:
    src = _normalize_title(source_name)
    if not src:
        return 0.0
    best = 0.0
    for raw in candidates:
        if not raw or not str(raw).strip():
            continue
        cand = _normalize_title(str(raw))
        if not cand:
            continue
        best = max(best, SequenceMatcher(None, src, cand).ratio())
        if src in cand or cand in src:
            best = max(best, 0.88)
    return best


def accept_keyword_match(
    *,
    source_name: str,
    source_year: int | None,
    item: dict[str, Any],
) -> bool:
    titles = (
        item.get("nameEn"),
        item.get("nameOriginal"),
        item.get("nameRu"),
    )
    sim = title_similarity(source_name, *titles)
    year_raw = item.get("year")
    try:
        cy = int(year_raw) if year_raw is not None else None
    except (TypeError, ValueError):
        cy = None
    if source_year is None or cy is None:
        return sim >= 0.72
    yd = abs(source_year - cy)
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
            if accept_keyword_match(source_name=name, source_year=year, item=item):
                kid = item.get("kinopoiskId")
                if kid is not None:
                    return int(kid)
        return None


async def map_one(
    *,
    client: httpx.AsyncClient,
    kp: KinopoiskUnofficialClient,
    entry: dict[str, Any],
) -> dict[str, Any]:
    sort_order = int(entry["sort_order"])
    name = str(entry["name"])
    year_raw = entry.get("year")
    year = int(year_raw) if year_raw is not None else None
    imdb_id = str(entry.get("imdb_id") or "")
    is_winner = bool(entry.get("is_winner"))
    ceremony_year = int(entry["ceremony_year"])

    kid: int | None = None
    method = "TODO"

    if IMDB_RE.match(imdb_id):
        try:
            kid = await kp.by_imdb_id(client, imdb_id)
            if kid is not None:
                method = "imdbId"
        except httpx.HTTPError as exc:
            print(f"KP imdb error order={sort_order} {imdb_id}: {exc}", file=sys.stderr)

    if kid is None:
        try:
            kid = await kp.by_keyword_year(client, name=name, year=year)
            if kid is not None:
                method = "keyword"
        except httpx.HTTPError as exc:
            print(f"KP keyword error order={sort_order} {name!r}: {exc}", file=sys.stderr)

    return {
        "sort_order": sort_order,
        "name": name,
        "year": year,
        "imdb_id": imdb_id,
        "kinopoisk_id": kid if kid is not None else "TODO",
        "match_method": method,
        "is_winner": is_winner,
        "ceremony_year": ceremony_year,
    }


def write_outputs(rows: list[dict[str, Any]], out_json: Path, out_txt: Path) -> None:
    rows_sorted = sorted(rows, key=lambda r: int(r["sort_order"]))
    out_json.write_text(json.dumps(rows_sorted, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = []
    for row in rows_sorted:
        kid = row["kinopoisk_id"]
        label = str(kid) if isinstance(kid, int) else "TODO"
        winner = " ★" if row.get("is_winner") else ""
        lines.append(f"{row['sort_order']}. {row['name']}{winner} — {label}")
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
        if isinstance(row, dict) and isinstance(row.get("sort_order"), int):
            out[int(row["sort_order"])] = row
    return out


async def map_year(
    *,
    year: int,
    here: Path,
    kp: KinopoiskUnofficialClient,
    client: httpx.AsyncClient,
    resume: bool,
    only_todos: bool,
    force_todos: bool,
) -> tuple[int, int, int]:
    in_path = here / f"oscars_{year}.json"
    out_json = here / f"oscars_{year}_kinopoisk.json"
    out_txt = here / f"oscars_{year}_kinopoisk.txt"

    entries = json.loads(in_path.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise ValueError(f"{in_path} must be a JSON array")

    existing = load_existing(out_json) if resume else {}
    to_process: list[dict[str, Any]] = []
    kept: list[dict[str, Any]] = []
    for entry in entries:
        sort_order = int(entry["sort_order"])
        prev = existing.get(sort_order)
        if (
            resume
            and prev is not None
            and isinstance(prev.get("kinopoisk_id"), int)
            and not force_todos
        ):
            kept.append(prev)
            continue
        if resume and only_todos and prev is not None and isinstance(prev.get("kinopoisk_id"), int):
            kept.append(prev)
            continue
        to_process.append(entry)

    print(
        f"[{year}] Mapping {len(to_process)}/{len(entries)} films (kept={len(kept)})",
        flush=True,
    )

    rows: list[dict[str, Any]] = list(kept)
    tasks = [asyncio.create_task(map_one(client=client, kp=kp, entry=e)) for e in to_process]
    for coro in asyncio.as_completed(tasks):
        rows.append(await coro)

    write_outputs(rows, out_json, out_txt)
    rows_sorted = sorted(rows, key=lambda r: int(r["sort_order"]))
    matched = sum(1 for r in rows_sorted if isinstance(r["kinopoisk_id"], int))
    todos = sum(1 for r in rows_sorted if r["kinopoisk_id"] == "TODO")
    print(f"[{year}] matched={matched} TODO={todos}", flush=True)
    return len(rows_sorted), matched, todos


async def amain(args: argparse.Namespace) -> int:
    here = Path(args.data_dir).resolve()

    api_key = os.environ.get("KINOPOISK_API_KEY", "").strip()
    base_url = os.environ.get(
        "KINOPOISK_API_BASE_URL",
        "https://kinopoiskapiunofficial.tech/api",
    ).strip()
    if not api_key:
        print("KINOPOISK_API_KEY is empty", file=sys.stderr)
        return 2

    if args.year:
        years = [int(args.year)]
    else:
        years = sorted(
            int(p.stem.split("_")[1])
            for p in here.glob("oscars_20*.json")
            if "_kinopoisk" not in p.name and p.stem.split("_")[1].isdigit()
        )

    kp_sem = asyncio.Semaphore(args.kp_concurrency)
    kp = KinopoiskUnofficialClient(base_url, api_key, kp_sem)
    timeout = httpx.Timeout(30.0, connect=10.0)
    limits = httpx.Limits(max_connections=args.kp_concurrency + 10)

    grand_total = grand_matched = grand_todos = 0
    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        for year in years:
            total, matched, todos = await map_year(
                year=year,
                here=here,
                kp=kp,
                client=client,
                resume=args.resume,
                only_todos=args.only_todos,
                force_todos=args.force_todos,
            )
            grand_total += total
            grand_matched += matched
            grand_todos += todos

    print("\n=== SUMMARY ===")
    print(f"Years: {years}")
    print(f"Total: {grand_total}")
    print(f"Matched: {grand_matched}")
    print(f"TODO: {grand_todos}")
    return 0 if grand_todos == 0 else 1


def parse_args() -> argparse.Namespace:
    here = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", default=str(here))
    p.add_argument("--year", type=int, help="Single ceremony year (default: all)")
    p.add_argument("--kp-concurrency", type=int, default=3)
    p.add_argument("--resume", action="store_true")
    p.add_argument("--only-todos", action="store_true")
    p.add_argument("--force-todos", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(amain(parse_args())))
