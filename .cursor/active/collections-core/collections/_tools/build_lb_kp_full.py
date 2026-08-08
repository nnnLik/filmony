#!/usr/bin/env python3
"""Build *_kinopoisk_full.json from a Letterboxd→Kinopoisk mapping JSON.

For each row with a resolved integer ``kinopoisk_id``, fetches:
  GET /v2.2/films/{id}
  GET /v1/staff?filmId={id}

Embeds ``film``, ``director``, and up to 10 ``actors`` per row.

Staff is fetched via ``GET /v1/staff?filmId={id}`` (v2.2 ``/staff`` is not available).

Run from backend (httpx on PYTHONPATH):

  cd backend && uv run python ../.cursor/active/collections-core/collections/_tools/build_lb_kp_full.py --help

With ``--slug horror_250``, reads ``collections/<slug>/intermediate/*_kinopoisk.json``
and writes ``collections/<slug>/letterboxd_<slug>_kinopoisk_full.json``.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx

COLLECTIONS_ROOT = Path(__file__).resolve().parent.parent

CHECKPOINT_EVERY = 25
MAX_ACTORS = 10


def _optional_str(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text if text else None


def _parse_genres(payload: object) -> list[str]:
    if not isinstance(payload, list):
        return []
    genres: list[str] = []
    seen: set[str] = set()
    for item in payload:
        if not isinstance(item, dict):
            continue
        value = item.get("genre")
        if not isinstance(value, str):
            continue
        genre = value.strip()
        if not genre:
            continue
        key = genre.lower()
        if key in seen:
            continue
        seen.add(key)
        genres.append(genre)
    return genres


def _parse_countries(payload: object) -> list[str]:
    if not isinstance(payload, list):
        return []
    countries: list[str] = []
    seen: set[str] = set()
    for item in payload:
        if not isinstance(item, dict):
            continue
        value = item.get("country")
        if not isinstance(value, str):
            continue
        country = value.strip()
        if not country:
            continue
        key = country.lower()
        if key in seen:
            continue
        seen.add(key)
        countries.append(country)
    return countries


def _build_film(payload: dict[str, Any], *, kinopoisk_id: int) -> dict[str, Any] | None:
    title = payload.get("nameRu") or payload.get("nameEn") or payload.get("nameOriginal")
    if not isinstance(title, str) or not title.strip():
        return None
    year_raw = payload.get("year")
    year: int | None
    try:
        year = int(year_raw) if year_raw is not None else None
    except (TypeError, ValueError):
        year = None
    poster_url = payload.get("posterUrl")
    imdb_raw = payload.get("imdbId")
    imdb_id = imdb_raw.strip() if isinstance(imdb_raw, str) and imdb_raw.strip() else None
    return {
        "kinopoisk_id": kinopoisk_id,
        "title": title.strip(),
        "year": year,
        "poster_url": poster_url if isinstance(poster_url, str) and poster_url.strip() else None,
        "genres": _parse_genres(payload.get("genres")),
        "countries": _parse_countries(payload.get("countries")),
        "short_description": _optional_str(payload.get("shortDescription")),
        "description": _optional_str(payload.get("description")),
        "imdb_id": imdb_id,
    }


def _staff_person(member: dict[str, Any]) -> dict[str, Any] | None:
    staff_id = member.get("staffId")
    if staff_id is None:
        return None
    try:
        sid = int(staff_id)
    except (TypeError, ValueError):
        return None
    return {
        "kinopoisk_staff_id": sid,
        "name_ru": _optional_str(member.get("nameRu")),
        "name_en": _optional_str(member.get("nameEn")),
    }


def _parse_staff(staff_raw: list[Any]) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    director: dict[str, Any] | None = None
    actors: list[dict[str, Any]] = []
    for item in staff_raw:
        if not isinstance(item, dict):
            continue
        profession = item.get("professionKey")
        if profession == "DIRECTOR" and director is None:
            director = _staff_person(item)
        elif profession == "ACTOR" and len(actors) < MAX_ACTORS:
            person = _staff_person(item)
            if person is not None:
                actors.append({**person, "order": len(actors) + 1})
    return director, actors


def _letterboxd_name(row: dict[str, Any]) -> str:
    return str(row.get("letterboxd_name") or row.get("name") or "")


def _base_mapping_fields(row: dict[str, Any]) -> dict[str, Any]:
    lb_name = _letterboxd_name(row)
    year_raw = row.get("year")
    year = int(year_raw) if year_raw is not None else None
    return {
        "rank": int(row["rank"]),
        "letterboxd_name": lb_name,
        "name": lb_name,
        "year": year,
        "letterboxd_uri": row.get("letterboxd_uri"),
        "imdb_id": row.get("imdb_id"),
        "kinopoisk_id": row["kinopoisk_id"],
        "match_method": row.get("match_method"),
    }


class KinopoiskUnofficialClient:
    def __init__(self, base_url: str, api_key: str, semaphore: asyncio.Semaphore) -> None:
        self._base = base_url.rstrip("/")
        self._headers = {"X-API-KEY": api_key, "Accept": "application/json"}
        self._sem = semaphore

    async def _get_json(
        self,
        client: httpx.AsyncClient,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        url = f"{self._base}{path}"
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
                    resp = await client.get(url, headers=self._headers, params=params)
            except transient_errors:
                await asyncio.sleep(min(8.0, 0.5 * (attempt + 1)))
                continue
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
        raise httpx.HTTPError(f"exhausted retries for {path}")

    async def get_film(self, client: httpx.AsyncClient, kinopoisk_id: int) -> dict[str, Any]:
        payload = await self._get_json(client, f"/v2.2/films/{kinopoisk_id}")
        if not isinstance(payload, dict):
            raise httpx.HTTPError(f"unexpected film payload for kp={kinopoisk_id}")
        return payload

    async def get_staff(self, client: httpx.AsyncClient, kinopoisk_id: int) -> list[Any]:
        try:
            payload = await self._get_json(
                client,
                "/v1/staff",
                params={"filmId": kinopoisk_id},
            )
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return []
            raise
        if not isinstance(payload, list):
            raise httpx.HTTPError(f"unexpected staff payload for kp={kinopoisk_id}")
        return payload


def load_existing(out_path: Path) -> dict[int, dict[str, Any]]:
    if not out_path.exists():
        return {}
    try:
        data = json.loads(out_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, list):
        return {}
    out: dict[int, dict[str, Any]] = {}
    for row in data:
        if not isinstance(row, dict) or not isinstance(row.get("rank"), int):
            continue
        film = row.get("film")
        if isinstance(film, dict) and isinstance(film.get("kinopoisk_id"), int):
            out[int(row["rank"])] = row
    return out


def write_output(rows: list[dict[str, Any]], out_path: Path) -> None:
    rows_sorted = sorted(rows, key=lambda r: int(r["rank"]))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(rows_sorted, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _collect_todos(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    todos: list[dict[str, Any]] = []
    for entry in entries:
        kid = entry.get("kinopoisk_id")
        if not isinstance(kid, int):
            todos.append(entry)
    return todos


async def build_one(
    *,
    client: httpx.AsyncClient,
    kp: KinopoiskUnofficialClient,
    row: dict[str, Any],
) -> dict[str, Any]:
    kid = int(row["kinopoisk_id"])
    out = _base_mapping_fields(row)
    film_payload = await kp.get_film(client, kid)
    film = _build_film(film_payload, kinopoisk_id=kid)
    if film is not None:
        out["film"] = film
    staff_raw = await kp.get_staff(client, kid)
    director, actors = _parse_staff(staff_raw)
    if director is not None:
        out["director"] = director
    if actors:
        out["actors"] = actors
    return out


def _print_summary(rows: list[dict[str, Any]]) -> None:
    total = len(rows)
    with_film = sum(1 for r in rows if isinstance(r.get("film"), dict))
    with_director = sum(1 for r in rows if isinstance(r.get("director"), dict))
    actor_counts = [len(r.get("actors") or []) for r in rows if isinstance(r.get("actors"), list)]
    avg_actors = (sum(actor_counts) / len(actor_counts)) if actor_counts else 0.0
    print("\n=== SUMMARY ===")
    print(f"Total: {total}")
    print(f"With film: {with_film}")
    print(f"With director: {with_director}")
    print(f"Avg actors: {avg_actors:.2f}")


async def amain(args: argparse.Namespace) -> int:
    in_path = Path(args.input)
    out_path = Path(args.output)

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

    todos = _collect_todos(entries)
    if todos and not args.allow_todos:
        print("Unresolved kinopoisk_id (TODO) rows — resolve or pass --allow-todos:", file=sys.stderr)
        for row in sorted(todos, key=lambda r: int(r["rank"])):
            print(
                f"  {row['rank']}. {_letterboxd_name(row)} ({row.get('year')}) "
                f"kinopoisk_id={row.get('kinopoisk_id')!r}",
                file=sys.stderr,
            )
        return 1

    eligible = [e for e in entries if isinstance(e.get("kinopoisk_id"), int)]
    existing = load_existing(out_path) if args.resume else {}
    kept: list[dict[str, Any]] = []
    to_process: list[dict[str, Any]] = []
    for entry in eligible:
        rank = int(entry["rank"])
        prev = existing.get(rank)
        if args.resume and prev is not None:
            kept.append(prev)
            continue
        to_process.append(entry)

    kp_sem = asyncio.Semaphore(args.concurrency)
    kp = KinopoiskUnofficialClient(base_url, api_key, kp_sem)
    timeout = httpx.Timeout(30.0, connect=10.0)
    limits = httpx.Limits(max_connections=args.concurrency + 4)

    print(
        f"Building full manifest for {len(to_process)}/{len(eligible)} films "
        f"(kept={len(kept)}, concurrency={args.concurrency}, resume={args.resume})",
        flush=True,
    )

    rows: list[dict[str, Any]] = list(kept)

    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        tasks = [asyncio.create_task(build_one(client=client, kp=kp, row=entry)) for entry in to_process]
        done = 0
        for coro in asyncio.as_completed(tasks):
            row = await coro
            rows.append(row)
            done += 1
            if done % CHECKPOINT_EVERY == 0 or done == len(tasks):
                write_output(rows, out_path)
                print(f"Progress: {done}/{len(tasks)} checkpoint → {out_path}", flush=True)

    write_output(rows, out_path)
    _print_summary(sorted(rows, key=lambda r: int(r["rank"])))
    print(f"Output: {out_path}")
    return 0


def _default_paths(slug: str | None) -> tuple[Path, Path]:
    here = Path(__file__).resolve().parent
    if slug:
        coll_dir = COLLECTIONS_ROOT / slug
        intermediate = coll_dir / "intermediate"
        return (
            intermediate / f"letterboxd_{slug}_kinopoisk.json",
            coll_dir / f"letterboxd_{slug}_kinopoisk_full.json",
        )
    return (
        here / "letterboxd_top_500_kinopoisk.json",
        here / "letterboxd_top_500_kinopoisk_full.json",
    )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--slug",
        default=None,
        help="Collection slug; default I/O under collections/<slug>/",
    )
    p.add_argument(
        "--input",
        default=None,
        help="Mapping JSON (*_kinopoisk.json); required unless --slug is set",
    )
    p.add_argument(
        "--output",
        default=None,
        help="Full manifest output path (default: collections/<slug>/letterboxd_<slug>_kinopoisk_full.json)",
    )
    p.add_argument("--concurrency", type=int, default=4, help="Parallel Kinopoisk requests")
    p.add_argument(
        "--resume",
        action="store_true",
        help="Skip rows that already have film.kinopoisk_id in existing output",
    )
    p.add_argument(
        "--allow-todos",
        action="store_true",
        help="Skip mapping rows with non-int kinopoisk_id instead of failing",
    )
    args = p.parse_args()

    default_in, default_out = _default_paths(args.slug)
    if args.input is None:
        if args.slug is None:
            p.error("--input is required when --slug is not set")
        args.input = str(default_in)
    if args.output is None:
        args.output = str(default_out)
    return args


if __name__ == "__main__":
    raise SystemExit(asyncio.run(amain(parse_args())))
