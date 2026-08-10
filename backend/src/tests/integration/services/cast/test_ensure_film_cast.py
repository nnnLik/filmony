from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session_factory
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
async def test_ensure_film_cast_persists_top_actors(prepare_db: None) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(kinopoisk_id=301, title='Matrix', year=1999, poster_url=None, genres=[])
        session.add(film)
        await session.commit()
        await session.refresh(film)
        film_id = film.id

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

    async with session_factory() as session:
        await EnsureFilmCastService.build(session, transport=transport).execute(film_id)

    async with session_factory() as session:
        persons = (await session.execute(select(Person))).scalars().all()
        film_actors = (await session.execute(select(FilmActor))).scalars().all()
    assert len(persons) == 1
    assert persons[0].kinopoisk_id == 733
    assert persons[0].name == 'Леонардо ДиКаприо'
    assert len(film_actors) == 1
    assert film_actors[0].role == 'Jack'
    assert film_actors[0].billing_order == 1


@pytest.mark.asyncio
async def test_ensure_film_cast_is_idempotent(prepare_db: None) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(kinopoisk_id=302, title='Film', year=2000, poster_url=None, genres=[])
        session.add(film)
        await session.commit()
        await session.refresh(film)
        film_id = film.id

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

    async with session_factory() as session:
        service = EnsureFilmCastService.build(session, transport=transport)
        await service.execute(film_id)
    async with session_factory() as session:
        service = EnsureFilmCastService.build(session, transport=transport)
        await service.execute(film_id)

    assert transport.calls == [302]
    async with session_factory() as session:
        count = (await session.execute(select(FilmActor))).scalars().all()
    assert len(count) == 1


@pytest.mark.asyncio
async def test_ensure_film_cast_persists_all_actors(prepare_db: None) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(kinopoisk_id=304, title='Large Cast', year=2020, poster_url=None, genres=[])
        session.add(film)
        await session.commit()
        await session.refresh(film)
        film_id = film.id

    staff = tuple(
        KinopoiskStaffMemberDTO(
            staff_id=i,
            name_ru=f'Actor {i}',
            name_en=None,
            profession_key='ACTOR',
            poster_url=None,
        )
        for i in range(1, 13)
    )
    transport = FakeKinopoiskStaffTransport(staff=staff)

    async with session_factory() as session:
        await EnsureFilmCastService.build(session, transport=transport).execute(film_id)

    async with session_factory() as session:
        film_actors = (await session.execute(select(FilmActor))).scalars().all()
        persons = (await session.execute(select(Person))).scalars().all()
    assert len(film_actors) == 12
    assert len(persons) == 12
    billing_orders = sorted(fa.billing_order for fa in film_actors)
    assert billing_orders == list(range(1, 13))


@pytest.mark.asyncio
async def test_ensure_film_cast_force_replaces_and_reuses_person(prepare_db: None) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(kinopoisk_id=305, title='Force Cast', year=2020, poster_url=None, genres=[])
        session.add(film)
        await session.flush()
        person = Person(kinopoisk_id=501, name='Original', poster_url=None)
        session.add(person)
        await session.flush()
        session.add(FilmActor(film_id=film.id, person_id=person.id, billing_order=1))
        await session.commit()
        await session.refresh(film)
        film_id = film.id
        person_id = person.id

    initial_staff = (
        KinopoiskStaffMemberDTO(
            staff_id=501,
            name_ru='Updated Name',
            name_en=None,
            profession_key='ACTOR',
            poster_url=None,
        ),
        KinopoiskStaffMemberDTO(
            staff_id=502,
            name_ru='New Actor',
            name_en=None,
            profession_key='ACTOR',
            poster_url=None,
        ),
    )
    transport = FakeKinopoiskStaffTransport(staff=initial_staff)

    async with session_factory() as session:
        await EnsureFilmCastService.build(session, transport=transport).execute(
            film_id,
            force=True,
        )

    async with session_factory() as session:
        film_actors = (await session.execute(select(FilmActor))).scalars().all()
        persons_501 = (
            (await session.execute(select(Person).where(Person.kinopoisk_id == 501)))
            .scalars()
            .all()
        )
        persons_502 = (
            (await session.execute(select(Person).where(Person.kinopoisk_id == 502)))
            .scalars()
            .all()
        )
        person_501 = (
            await session.execute(select(Person).where(Person.id == person_id))
        ).scalar_one()
    assert len(film_actors) == 2
    assert len(persons_501) == 1
    assert len(persons_502) == 1
    assert person_501.name == 'Updated Name'
    assert transport.calls == [305]


@pytest.mark.asyncio
async def test_ensure_film_cast_force_fetch_failure_preserves_cast(prepare_db: None) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(kinopoisk_id=306, title='Protected Cast', year=2020, poster_url=None, genres=[])
        session.add(film)
        await session.flush()
        person = Person(kinopoisk_id=601, name='Actor', poster_url=None)
        session.add(person)
        await session.flush()
        session.add(FilmActor(film_id=film.id, person_id=person.id, billing_order=1))
        await session.commit()
        await session.refresh(film)
        film_id = film.id

    transport = FakeKinopoiskStaffTransport(should_fail=True)

    async with session_factory() as session:
        await EnsureFilmCastService.build(session, transport=transport).execute(
            film_id,
            force=True,
        )

    async with session_factory() as session:
        film_actors = (await session.execute(select(FilmActor))).scalars().all()
    assert len(film_actors) == 1


@pytest.mark.asyncio
async def test_ensure_film_cast_swallows_kp_errors(prepare_db: None) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(kinopoisk_id=303, title='Film', year=2000, poster_url=None, genres=[])
        session.add(film)
        await session.commit()
        await session.refresh(film)
        film_id = film.id

    transport = FakeKinopoiskStaffTransport(should_fail=True)

    async with session_factory() as session:
        await EnsureFilmCastService.build(session, transport=transport).execute(film_id)

    async with session_factory() as session:
        rows = (await session.execute(select(FilmActor))).scalars().all()
    assert rows == []
