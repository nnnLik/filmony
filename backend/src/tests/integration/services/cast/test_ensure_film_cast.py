from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from models.film_actor import FilmActor
from models.person import Person
from providers.kinopoisk.kinopoisk_staff_dto import KinopoiskStaffMemberDTO
from services.cast.ensure_film_cast import EnsureFilmCastService


@dataclass
class FakeKinopoiskStaffTransport:
    staff: tuple[KinopoiskStaffMemberDTO, ...] = ()
    calls: list[int] = field(default_factory=list)
    should_fail: bool = False

    async def get_staff_by_film_id(self, kinopoisk_id: int) -> tuple[KinopoiskStaffMemberDTO, ...]:
        self.calls.append(kinopoisk_id)
        if self.should_fail:
            from providers.kinopoisk.kinopoisk_provider_transport import KinopoiskProviderTransport

            raise KinopoiskProviderTransport.KinopoiskProviderTransportError
        return self.staff


@pytest.mark.asyncio
async def test_ensure_film_cast_persists_top_actors(prepare_db: AsyncSession) -> None:
    session = prepare_db
    film = Film(kinopoisk_id=301, title='Matrix', year=1999, poster_url=None, genres=[])
    session.add(film)
    await session.commit()
    await session.refresh(film)

    transport = FakeKinopoiskStaffTransport(
        staff=(
            KinopoiskStaffMemberDTO(
                staff_id=733,
                name_ru='Леонардо ДиКаприо',
                name_en='Leonardo DiCaprio',
                profession_key='ACTOR',
                poster_url='https://example/poster.jpg',
                description='Jack',
            ),
            KinopoiskStaffMemberDTO(
                staff_id=11,
                name_ru='Director',
                name_en=None,
                profession_key='DIRECTOR',
                poster_url=None,
            ),
        ),
    )

    await EnsureFilmCastService.build(session, transport=transport).execute(film.id)

    persons = (await session.execute(select(Person))).scalars().all()
    film_actors = (await session.execute(select(FilmActor))).scalars().all()
    assert len(persons) == 1
    assert persons[0].kinopoisk_id == 733
    assert persons[0].name == 'Леонардо ДиКаприо'
    assert len(film_actors) == 1
    assert film_actors[0].role == 'Jack'
    assert film_actors[0].billing_order == 1


@pytest.mark.asyncio
async def test_ensure_film_cast_is_idempotent(prepare_db: AsyncSession) -> None:
    session = prepare_db
    film = Film(kinopoisk_id=302, title='Film', year=2000, poster_url=None, genres=[])
    session.add(film)
    await session.commit()
    await session.refresh(film)

    transport = FakeKinopoiskStaffTransport(
        staff=(
            KinopoiskStaffMemberDTO(
                staff_id=1,
                name_ru='Actor',
                name_en=None,
                profession_key='ACTOR',
                poster_url=None,
            ),
        ),
    )
    service = EnsureFilmCastService.build(session, transport=transport)
    await service.execute(film.id)
    await service.execute(film.id)

    assert transport.calls == [302]
    count = (await session.execute(select(FilmActor))).scalars().all()
    assert len(count) == 1


@pytest.mark.asyncio
async def test_ensure_film_cast_swallows_kp_errors(prepare_db: AsyncSession) -> None:
    session = prepare_db
    film = Film(kinopoisk_id=303, title='Film', year=2000, poster_url=None, genres=[])
    session.add(film)
    await session.commit()
    await session.refresh(film)

    transport = FakeKinopoiskStaffTransport(should_fail=True)

    await EnsureFilmCastService.build(session, transport=transport).execute(film.id)

    assert (await session.execute(select(FilmActor))).scalars().all() == []
