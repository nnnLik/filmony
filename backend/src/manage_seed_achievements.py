"""Seed achievement catalog rows from existing collection slugs.

Production (from repo root; backend container must be running):

  docker compose exec -w /opt/app filmony-backend alembic upgrade head
  make seed-achievements

Direct CLI (inside container):

  python src/manage_seed_achievements.py [--dry-run]

Idempotent: upserts ``Achievement`` rows keyed by ``collection_slug``.
"""

from __future__ import annotations

import argparse
import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from core.database import get_session_factory
from models.achievement import Achievement
from models.collection import Collection

_log = logging.getLogger(__name__)


def _achievement_description(collection: Collection) -> str:
    if collection.description:
        return collection.description
    return f'Завершите коллекцию «{collection.title}» на 100%.'


async def _seed(*, dry_run: bool) -> int:
    session_factory = get_session_factory()
    upserted = 0
    async with session_factory() as session:
        collections = list(
            (await session.execute(select(Collection).order_by(Collection.slug))).scalars().all()
        )
        for collection in collections:
            slug = collection.slug
            values = {
                'slug': slug,
                'collection_slug': slug,
                'title': collection.title,
                'description': _achievement_description(collection),
                'icon_key': collection.kind.value,
            }
            if dry_run:
                _log.info('would upsert achievement slug=%s', slug)
                upserted += 1
                continue
            stmt = (
                pg_insert(Achievement)
                .values(**values)
                .on_conflict_do_update(
                    index_elements=['collection_slug'],
                    set_={
                        'slug': slug,
                        'title': collection.title,
                        'description': values['description'],
                        'icon_key': values['icon_key'],
                    },
                )
            )
            await session.execute(stmt)
            upserted += 1
        if not dry_run:
            await session.commit()
    return upserted


async def _async_main(*, dry_run: bool) -> None:
    count = await _seed(dry_run=dry_run)
    _log.info('seed achievements complete: rows=%d dry_run=%s', count, dry_run)


def main() -> None:
    parser = argparse.ArgumentParser(description='Seed achievement catalog from collections')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_async_main(dry_run=args.dry_run))


if __name__ == '__main__':
    main()
