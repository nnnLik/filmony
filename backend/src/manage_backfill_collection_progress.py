"""Backfill user_collection_progress for all active collections.

  docker compose exec -w /opt/app backend \\
    python src/manage_backfill_collection_progress.py
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from core.database import get_session_factory
from models.collection import Collection
from models.collection_film import CollectionFilm
from models.user_card import UserCard
from services.collections.meaningful_rated_card import meaningful_rated_card_criteria
from services.collections.refresh_user_collection_progress import (
    RefreshUserCollectionProgressService,
)

_log = logging.getLogger(__name__)


def _configure_script_logging() -> None:
    logging.basicConfig(level=logging.INFO, format='%(message)s')


async def _run() -> None:
    _configure_script_logging()
    factory = get_session_factory()

    async with factory() as session:
        collections = (
            (
                await session.execute(
                    select(Collection)
                    .where(Collection.is_active.is_(True))
                    .order_by(Collection.id.asc()),
                )
            )
            .scalars()
            .all()
        )

    _log.info('=== Collection progress backfill ===')
    _log.info('Active collections: %s', len(collections))

    total_users = 0
    for collection in collections:
        _log.info('--- collection id=%s slug=%s ---', collection.id, collection.slug)
        async with factory() as session:
            user_ids = (
                (
                    await session.execute(
                        select(UserCard.user_id)
                        .join(CollectionFilm, CollectionFilm.film_id == UserCard.film_id)
                        .where(
                            CollectionFilm.collection_id == collection.id,
                            *meaningful_rated_card_criteria(),
                        )
                        .distinct(),
                    )
                )
                .scalars()
                .all()
            )
        _log.info('users to refresh: %s', len(user_ids))
        total_users += len(user_ids)

        for user_id in user_ids:
            async with factory() as session:
                progress = await RefreshUserCollectionProgressService.build(session).execute(
                    user_id,
                    collection.id,
                )
                _log.info(
                    'progress %s: %s/%s',
                    user_id,
                    progress.rated_count,
                    progress.total_count,
                )

    _log.info('=== Done: collections=%s user-refreshes=%s ===', len(collections), total_users)


def main() -> None:
    asyncio.run(_run())


if __name__ == '__main__':
    main()
