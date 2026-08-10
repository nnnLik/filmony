from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Self

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from models.film_actor import FilmActor
from models.person import Person
from providers.kinopoisk.kinopoisk_provider_transport import KinopoiskProviderTransport
from services.cast.parse_top_actors import ParsedTopActor, parse_top_actors

logger = logging.getLogger(__name__)


@dataclass
class EnsureFilmCastService:
    """Ensures full Kinopoisk ACTOR cast exists for a film (idempotent).

    When ``force`` is True, existing film_actor links for the film are replaced;
    Person rows are upserted by kinopoisk_id (no duplicates).
    """

    _session: AsyncSession
    _kp_transport: KinopoiskProviderTransport

    @classmethod
    def build(
        cls,
        session: AsyncSession,
        *,
        transport: KinopoiskProviderTransport | None = None,
    ) -> Self:
        return cls(
            _session=session,
            _kp_transport=transport or KinopoiskProviderTransport(),
        )

    async def execute(self, film_id: int, *, force: bool = False) -> None:
        film = (
            await self._session.execute(select(Film).where(Film.id == film_id))
        ).scalar_one_or_none()
        if film is None or film.kinopoisk_id is None:
            return

        if not force:
            existing = (
                await self._session.execute(
                    select(FilmActor.id).where(FilmActor.film_id == film_id).limit(1),
                )
            ).scalar_one_or_none()
            if existing is not None:
                return

        try:
            staff = await self._kp_transport.get_staff_by_film_id(film.kinopoisk_id)
        except KinopoiskProviderTransport.KinopoiskProviderTransportError:
            logger.warning(
                'Failed to fetch Kinopoisk staff for film_id=%s kinopoisk_id=%s',
                film_id,
                film.kinopoisk_id,
                exc_info=True,
            )
            return

        actors = parse_top_actors(staff)
        if not actors:
            return

        if force:
            await self._session.execute(delete(FilmActor).where(FilmActor.film_id == film_id))

        for actor in actors:
            person = await self._upsert_person(actor)
            self._session.add(
                FilmActor(
                    film_id=film_id,
                    person_id=person.id,
                    billing_order=actor.billing_order,
                    role=actor.role,
                ),
            )
        await self._session.commit()

    async def _upsert_person(self, actor: ParsedTopActor) -> Person:
        existing = (
            await self._session.execute(
                select(Person).where(Person.kinopoisk_id == actor.kinopoisk_id),
            )
        ).scalar_one_or_none()
        if existing is not None:
            if actor.name:
                existing.name = actor.name
            if actor.poster_url:
                existing.poster_url = actor.poster_url
            return existing

        person = Person(
            kinopoisk_id=actor.kinopoisk_id,
            name=actor.name,
            poster_url=actor.poster_url,
        )
        self._session.add(person)
        await self._session.flush()
        return person
