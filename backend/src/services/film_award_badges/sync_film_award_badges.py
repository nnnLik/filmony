from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from daos.film_award_badge_dao import FilmAwardBadgeDAO
from models.film import Film
from models.film_award_badge import FilmAwardBadgeKind

_log = logging.getLogger(__name__)

_CURATED_DIR = Path(__file__).resolve().parents[2] / 'data/curated/oscars'
_MANIFEST_PATTERN = re.compile(r'^oscars_(\d{4})_kinopoisk\.json$')


@dataclass(frozen=True, slots=True)
class OscarBadgeDatasetRow:
    kinopoisk_id: int
    kind: FilmAwardBadgeKind
    ceremony_year: int


@dataclass(frozen=True, slots=True)
class SyncFilmAwardBadgesResult:
    files_processed: int
    rows_seen: int
    skipped_todo: int
    matched: int
    upserted: int
    unmatched_kinopoisk_ids: tuple[int, ...]


@dataclass
class SyncFilmAwardBadgesService:
    """Syncs Oscar Best Picture badges from curated Kinopoisk manifests onto films."""

    _session: AsyncSession
    _dao: FilmAwardBadgeDAO
    _curated_dir: Path

    @classmethod
    def build(
        cls,
        session: AsyncSession,
        *,
        curated_dir: Path | None = None,
    ) -> Self:
        return cls(
            _session=session,
            _dao=FilmAwardBadgeDAO(session),
            _curated_dir=curated_dir or _CURATED_DIR,
        )

    async def execute(self, *, dry_run: bool = False) -> SyncFilmAwardBadgesResult:
        rows, skipped_todo, files_processed = self._load_dataset()
        matched = 0
        upserted = 0
        unmatched: set[int] = set()

        for row in rows:
            film = await self._find_film_by_kinopoisk_id(row.kinopoisk_id)
            if film is None:
                unmatched.add(row.kinopoisk_id)
                continue
            matched += 1
            if dry_run:
                continue
            await self._dao.upsert_badge(
                film_id=film.id,
                kind=row.kind,
                ceremony_year=row.ceremony_year,
            )
            upserted += 1

        if not dry_run:
            await self._session.commit()

        if unmatched:
            _log.info(
                'sync film award badges: %d unmatched kinopoisk_id(s): %s',
                len(unmatched),
                sorted(unmatched)[:20],
            )

        return SyncFilmAwardBadgesResult(
            files_processed=files_processed,
            rows_seen=len(rows),
            skipped_todo=skipped_todo,
            matched=matched,
            upserted=upserted,
            unmatched_kinopoisk_ids=tuple(sorted(unmatched)),
        )

    def _load_dataset(self) -> tuple[list[OscarBadgeDatasetRow], int, int]:
        if not self._curated_dir.is_dir():
            raise FileNotFoundError(f'curated oscars dir missing: {self._curated_dir}')

        rows: list[OscarBadgeDatasetRow] = []
        skipped_todo = 0
        files_processed = 0

        for path in sorted(self._curated_dir.glob('oscars_*_kinopoisk.json')):
            if _MANIFEST_PATTERN.match(path.name) is None:
                continue
            match = _MANIFEST_PATTERN.match(path.name)
            assert match is not None
            ceremony_year = int(match.group(1))
            file_rows, file_skipped = self._load_manifest(path, ceremony_year=ceremony_year)
            rows.extend(file_rows)
            skipped_todo += file_skipped
            files_processed += 1

        return rows, skipped_todo, files_processed

    def _load_manifest(
        self,
        path: Path,
        *,
        ceremony_year: int,
    ) -> tuple[list[OscarBadgeDatasetRow], int]:
        raw: list[dict[str, Any]] = json.loads(path.read_text(encoding='utf-8'))
        skipped_todo = sum(1 for item in raw if item.get('kinopoisk_id') == 'TODO')
        rows: list[OscarBadgeDatasetRow] = []

        for item in raw:
            kp = item.get('kinopoisk_id')
            if kp == 'TODO' or kp is None:
                continue
            if not isinstance(kp, int):
                raise TypeError(
                    f'invalid kinopoisk_id in {path.name} sort_order {item.get("sort_order")}: {kp!r}',
                )
            kind = (
                FilmAwardBadgeKind.oscar_best_picture_winner
                if bool(item.get('is_winner'))
                else FilmAwardBadgeKind.oscar_best_picture_nominee
            )
            rows.append(
                OscarBadgeDatasetRow(
                    kinopoisk_id=kp,
                    kind=kind,
                    ceremony_year=int(item.get('ceremony_year') or ceremony_year),
                ),
            )

        return rows, skipped_todo

    async def _find_film_by_kinopoisk_id(self, kinopoisk_id: int) -> Film | None:
        result = await self._session.execute(
            select(Film).where(Film.kinopoisk_id == kinopoisk_id),
        )
        return result.scalar_one_or_none()
