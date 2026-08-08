"""Build personal digest DTO for weekly and monthly periods."""

from __future__ import annotations

import datetime as dt
from collections import Counter
from dataclasses import dataclass
from typing import Literal, Self
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.achievement import Achievement
from models.collection import Collection
from models.collection_film import CollectionFilm
from models.film import Film
from models.film_actor import FilmActor
from models.person import Person
from models.user_achievement import UserAchievement
from models.user_card import UserCard
from services.controversy.compute_weekly_controversy import ComputeWeeklyControversyService
from services.controversy.constants import MIN_SPREAD_FOR_TELEGRAM_DIGEST
from services.franchises.franchise_label import resolve_franchise_label
from services.gamification.compute_marathon_achievements import ComputeMarathonAchievementsService
from services.gamification.compute_passport_stamps import ComputePassportStampsService
from services.personal_digest.build_personal_digest_friends_section import (
    BuildPersonalDigestFriendsSectionService,
    FriendsDigestSection,
)
from services.personal_digest.build_personal_digest_fun_facts import (
    BuildPersonalDigestFunFactsService,
    build_digest_context_for_week,
)
from services.personal_digest.week_bounds import (
    format_week_period_label,
    parse_iso_week_period_key,
    previous_complete_iso_week,
    week_bounds_for_iso_week,
)
from services.profile.build_monthly_recap import (
    BuildMonthlyRecapService,
    MonthlyRecap,
    MonthlyRecapAchievementItem,
    MonthlyRecapActorItem,
    MonthlyRecapCollectionDeltaItem,
    MonthlyRecapDecadeItem,
    MonthlyRecapDirectorItem,
    MonthlyRecapDistributionItem,
    MonthlyRecapFilmItem,
    MonthlyRecapFranchiseItem,
    MonthlyRecapMarathonItem,
    MonthlyRecapStampItem,
    _completion_timestamp,
    _max_consecutive_days_in_window,
    _month_bounds,
    month_period_key,
    previous_complete_month,
)
from services.streaks.batch_user_rating_streaks import BatchUserRatingStreaksService


@dataclass(frozen=True, slots=True)
class ControversyInsight:
    film_title: str
    friend_display: str
    spread: float
    anchor_film_id: int | None


@dataclass(frozen=True, slots=True)
class PersonalDigestDTO:
    user_id: UUID
    period: Literal['week', 'month']
    period_key: str
    period_label: str
    window_start: dt.datetime
    window_end: dt.datetime
    total_rated: int
    average_rating: float
    vs_previous_total_rated: int | None
    vs_previous_average_rating: float | None
    top_films: list[MonthlyRecapFilmItem]
    all_films: list[MonthlyRecapFilmItem]
    top_director_name: str | None
    top_director_count: int
    top_director_kinopoisk_id: int | None
    top_actor_kinopoisk_id: int | None
    top_actor_name: str | None
    top_actor_count: int
    director_breakdown: list[MonthlyRecapDirectorItem]
    actor_breakdown: list[MonthlyRecapActorItem]
    genre_breakdown: list[MonthlyRecapDistributionItem]
    decade_breakdown: list[MonthlyRecapDecadeItem]
    top_country: str | None
    top_country_count: int
    new_countries_count: int
    franchise_breakdown: list[MonthlyRecapFranchiseItem]
    dominant_mood_after: str | None
    dominant_company: str | None
    new_stamps: list[MonthlyRecapStampItem]
    marathons_unlocked: list[MonthlyRecapMarathonItem]
    achievements_unlocked: list[MonthlyRecapAchievementItem]
    collection_deltas: list[MonthlyRecapCollectionDeltaItem]
    peak_activity_date: dt.date | None
    peak_activity_count: int
    streak_current: int
    streak_best_in_period: int
    friends: FriendsDigestSection | None
    fun_facts: list[str]
    controversy: ControversyInsight | None
    year: int | None = None
    month: int | None = None
    genre_of_month: str | None = None
    genre_of_month_count: int = 0


@dataclass
class BuildPersonalDigestService:
    """Orchestrates personal digest data for weekly or monthly periods."""

    _session: AsyncSession
    _monthly_recap_svc: BuildMonthlyRecapService
    _friends_svc: BuildPersonalDigestFriendsSectionService

    class InvalidPeriod(Exception):
        pass

    class DigestNotFound(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(
            _session=session,
            _monthly_recap_svc=BuildMonthlyRecapService.build(session),
            _friends_svc=BuildPersonalDigestFriendsSectionService.build(session),
        )

    async def execute(
        self,
        user_id: UUID,
        *,
        period: Literal['week', 'month'],
        period_key: str | None = None,
        year: int | None = None,
        month: int | None = None,
    ) -> PersonalDigestDTO:
        if period == 'month':
            if year is not None and month is not None:
                resolved_key = month_period_key(year=year, month=month)
            elif period_key is not None:
                resolved_key = period_key
                year_str, month_str = period_key.split('-', maxsplit=1)
                year, month = int(year_str), int(month_str)
            else:
                year, month = previous_complete_month()
                resolved_key = month_period_key(year=year, month=month)
            try:
                recap = await self._monthly_recap_svc.execute(user_id, year=year, month=month)
            except BuildMonthlyRecapService.RecapNotFound:
                raise self.DigestNotFound from None
            digest = self._from_monthly_recap(recap, period_key=resolved_key)
            return digest

        if period != 'week':
            raise self.InvalidPeriod

        if period_key is not None:
            iso_year, iso_week = parse_iso_week_period_key(period_key)
            resolved_key = period_key
        else:
            resolved_key, iso_year, iso_week = previous_complete_iso_week()
        window_start, window_end = week_bounds_for_iso_week(
            iso_year=iso_year,
            iso_week=iso_week,
        )
        return await self._build_week_digest(
            user_id=user_id,
            period_key=resolved_key,
            window_start=window_start,
            window_end=window_end,
        )

    def _from_monthly_recap(self, recap: MonthlyRecap, *, period_key: str) -> PersonalDigestDTO:
        month_start, month_end = _month_bounds(recap.year, recap.month)
        return PersonalDigestDTO(
            user_id=recap.user_id,
            period='month',
            period_key=period_key,
            period_label=recap.month_label,
            window_start=month_start,
            window_end=month_end,
            total_rated=recap.total_rated,
            average_rating=recap.average_rating,
            vs_previous_total_rated=recap.vs_previous_total_rated,
            vs_previous_average_rating=recap.vs_previous_average_rating,
            top_films=list(recap.top_films),
            all_films=list(recap.top_films),
            top_director_name=recap.top_director_name,
            top_director_count=recap.top_director_count,
            top_director_kinopoisk_id=recap.top_director_kinopoisk_id,
            top_actor_kinopoisk_id=recap.top_actor_kinopoisk_id,
            top_actor_name=recap.top_actor_name,
            top_actor_count=recap.top_actor_count,
            director_breakdown=list(recap.director_breakdown),
            actor_breakdown=list(recap.actor_breakdown),
            genre_breakdown=list(recap.genre_breakdown),
            decade_breakdown=list(recap.decade_breakdown),
            top_country=recap.top_country,
            top_country_count=recap.top_country_count,
            new_countries_count=recap.new_countries_count,
            franchise_breakdown=list(recap.franchise_breakdown),
            dominant_mood_after=recap.dominant_mood_after,
            dominant_company=recap.dominant_company,
            new_stamps=list(recap.new_stamps),
            marathons_unlocked=list(recap.marathons_unlocked),
            achievements_unlocked=list(recap.achievements_unlocked),
            collection_deltas=list(recap.collection_deltas),
            peak_activity_date=recap.peak_activity_date,
            peak_activity_count=recap.peak_activity_count,
            streak_current=recap.streak_current,
            streak_best_in_period=recap.streak_best_in_period,
            friends=None,
            fun_facts=list(recap.fun_facts),
            controversy=None,
            year=recap.year,
            month=recap.month,
            genre_of_month=recap.genre_of_month,
            genre_of_month_count=recap.genre_of_month_count,
        )

    async def _build_week_digest(
        self,
        *,
        user_id: UUID,
        period_key: str,
        window_start: dt.datetime,
        window_end: dt.datetime,
    ) -> PersonalDigestDTO:
        rows = (
            await self._session.execute(
                select(
                    UserCard.id,
                    UserCard.film_id,
                    UserCard.catalog_item_id,
                    UserCard.rating,
                    UserCard.display_title,
                    UserCard.display_cover_url,
                    UserCard.company,
                    UserCard.mood_after,
                    _completion_timestamp().label('completed_at'),
                    Film.title,
                    Film.poster_url,
                    Film.genres,
                    Film.countries,
                    Film.year,
                    Film.primary_director_kinopoisk_id,
                    Film.primary_director_name,
                    Film.franchise_key,
                )
                .outerjoin(Film, Film.id == UserCard.film_id)
                .where(
                    UserCard.user_id == user_id,
                    UserCard.is_planned.is_(False),
                    _completion_timestamp() >= window_start,
                    _completion_timestamp() < window_end,
                )
            )
        ).all()

        if not rows:
            raise self.DigestNotFound

        films: list[MonthlyRecapFilmItem] = []
        rating_sum = 0.0
        activity_by_day: Counter[dt.date] = Counter()
        genre_counter: Counter[str] = Counter()
        director_counter: dict[int, tuple[str, int]] = {}
        franchise_counter: Counter[str] = Counter()
        country_counter: Counter[str] = Counter()
        decade_counter: Counter[int] = Counter()
        mood_after_counter: Counter[str] = Counter()
        company_counter: Counter[str] = Counter()
        week_countries: set[str] = set()

        for row in rows:
            rating_value = float(row.rating)
            rating_sum += rating_value
            completed_at = row.completed_at
            if completed_at is not None:
                if completed_at.tzinfo is None:
                    completed_at = completed_at.replace(tzinfo=dt.UTC)
                activity_by_day[completed_at.date()] += 1

            title = row.title or row.display_title or 'Без названия'
            films.append(
                MonthlyRecapFilmItem(
                    card_id=int(row.id),
                    film_id=int(row.film_id) if row.film_id is not None else None,
                    catalog_item_id=int(row.catalog_item_id)
                    if row.catalog_item_id is not None
                    else None,
                    title=str(title),
                    poster_url=row.poster_url or row.display_cover_url,
                    rating=rating_value,
                )
            )

            if row.genres:
                for genre in row.genres:
                    if isinstance(genre, str) and genre.strip():
                        genre_counter[genre.strip()] += 1

            if row.primary_director_kinopoisk_id is not None:
                director_id = int(row.primary_director_kinopoisk_id)
                director_name = (
                    str(row.primary_director_name or '').strip() or f'Режиссёр #{director_id}'
                )
                existing_name, existing_count = director_counter.get(
                    director_id, (director_name, 0)
                )
                director_counter[director_id] = (
                    existing_name or director_name,
                    existing_count + 1,
                )

            if row.franchise_key:
                franchise_key = str(row.franchise_key).strip()
                if franchise_key:
                    franchise_counter[franchise_key] += 1

            if row.countries:
                for country in row.countries:
                    if isinstance(country, str) and country.strip():
                        label = country.strip()
                        country_counter[label] += 1
                        week_countries.add(label)

            if row.year is not None:
                decade_start = (int(row.year) // 10) * 10
                decade_counter[decade_start] += 1

            if row.mood_after:
                mood_label = str(row.mood_after).strip()
                if mood_label:
                    mood_after_counter[mood_label] += 1
            if row.company:
                company_label = str(row.company).strip()
                if company_label:
                    company_counter[company_label] += 1

        total_rated = len(films)
        average_rating = round(rating_sum / total_rated, 1) if total_rated else 0.0
        sorted_films = sorted(films, key=lambda item: (-item.rating, -item.card_id))
        top_films = sorted_films[:3]

        peak_activity_date: dt.date | None = None
        peak_activity_count = 0
        if activity_by_day:
            peak_activity_date, peak_activity_count = activity_by_day.most_common(1)[0]

        genre_of_month: str | None = None
        genre_of_month_count = 0
        if genre_counter:
            genre_of_month, genre_of_month_count = genre_counter.most_common(1)[0]

        top_director_name: str | None = None
        top_director_count = 0
        top_director_kinopoisk_id: int | None = None
        if director_counter:
            top_director_kinopoisk_id, (top_director_name, top_director_count) = max(
                director_counter.items(),
                key=lambda item: (item[1][1], item[1][0]),
            )

        top_country: str | None = None
        top_country_count = 0
        if country_counter:
            top_country, top_country_count = country_counter.most_common(1)[0]

        new_countries_count = await self._count_new_countries_before_window(
            user_id=user_id,
            window_start=window_start,
            window_countries=week_countries,
        )

        genre_breakdown = [
            MonthlyRecapDistributionItem(label=genre, count=count)
            for genre, count in genre_counter.most_common(5)
        ]
        decade_breakdown = [
            MonthlyRecapDecadeItem(
                decade_start=decade_start,
                label=f'{decade_start}-е',
                count=count,
            )
            for decade_start, count in sorted(decade_counter.items(), key=lambda item: item[0])
        ]
        director_breakdown = [
            MonthlyRecapDirectorItem(kinopoisk_id=kinopoisk_id, label=name, count=count)
            for kinopoisk_id, (name, count) in sorted(
                director_counter.items(),
                key=lambda item: (-item[1][1], item[1][0]),
            )[:3]
        ]
        franchise_breakdown: list[MonthlyRecapFranchiseItem] = []
        for franchise_key, count in franchise_counter.most_common(3):
            franchise_breakdown.append(
                MonthlyRecapFranchiseItem(
                    franchise_key=franchise_key,
                    label=await resolve_franchise_label(self._session, franchise_key),
                    count=count,
                )
            )

        actor_breakdown = await self._actor_breakdown_in_window(
            user_id=user_id,
            window_start=window_start,
            window_end=window_end,
            limit=3,
        )
        top_actor_kinopoisk_id: int | None = None
        top_actor_name: str | None = None
        top_actor_count = 0
        if actor_breakdown:
            top_item = actor_breakdown[0]
            top_actor_kinopoisk_id = top_item.kinopoisk_id
            top_actor_name = top_item.label
            top_actor_count = top_item.count

        new_stamps = await self._stamps_unlocked_in_window(
            user_id=user_id,
            window_start=window_start,
            window_end=window_end,
        )
        marathons_unlocked = await self._marathons_unlocked_in_window(
            user_id=user_id,
            window_start=window_start,
            window_end=window_end,
        )
        collection_deltas = await self._collection_deltas_in_window(
            user_id=user_id,
            window_start=window_start,
            window_end=window_end,
        )
        achievements_unlocked = await self._achievements_unlocked_in_window(
            user_id=user_id,
            window_start=window_start,
            window_end=window_end,
        )

        window_end_date = window_end.date()
        streak_map = await BatchUserRatingStreaksService.build(self._session).execute(
            [user_id],
            today_utc=window_end_date - dt.timedelta(days=1),
        )
        streak_current = streak_map[user_id].current if user_id in streak_map else 0
        streak_best_in_period = _max_consecutive_days_in_window(
            set(activity_by_day.keys()),
            window_start=window_start.date(),
            window_end_exclusive=window_end_date,
        )

        vs_previous_total_rated, vs_previous_average_rating = await self._vs_previous_week(
            user_id=user_id,
            window_start=window_start,
            total_rated=total_rated,
            average_rating=average_rating,
        )

        dominant_mood_after: str | None = None
        if mood_after_counter:
            dominant_mood_after = mood_after_counter.most_common(1)[0][0]
        dominant_company: str | None = None
        if company_counter:
            dominant_company = company_counter.most_common(1)[0][0]

        friends = await self._friends_svc.execute(
            recipient_user_id=user_id,
            window_start=window_start,
            window_end=window_end,
        )
        controversy = await self._controversy_insight(
            user_id=user_id,
            window_end=window_end,
        )

        period_label = format_week_period_label(
            window_start=window_start,
            window_end_exclusive=window_end,
        )

        collection_totals = await self._collection_film_totals_by_slug(
            [item.collection_slug for item in collection_deltas]
        )
        fun_facts = BuildPersonalDigestFunFactsService.build().execute(
            build_digest_context_for_week(
                user_id=user_id,
                period_key=period_key,
                total_rated=total_rated,
                ratings=tuple(film.rating for film in films),
                genre_breakdown=genre_breakdown,
                decade_breakdown=decade_breakdown,
                marathons_unlocked=marathons_unlocked,
                collection_deltas=collection_deltas,
                new_countries_count=new_countries_count,
                streak_best_in_period=streak_best_in_period,
                collection_totals=collection_totals,
            )
        )

        return PersonalDigestDTO(
            user_id=user_id,
            period='week',
            period_key=period_key,
            period_label=period_label,
            window_start=window_start,
            window_end=window_end,
            total_rated=total_rated,
            average_rating=average_rating,
            vs_previous_total_rated=vs_previous_total_rated,
            vs_previous_average_rating=vs_previous_average_rating,
            top_films=top_films,
            all_films=sorted_films,
            top_director_name=top_director_name,
            top_director_count=top_director_count,
            top_director_kinopoisk_id=top_director_kinopoisk_id,
            top_actor_kinopoisk_id=top_actor_kinopoisk_id,
            top_actor_name=top_actor_name,
            top_actor_count=top_actor_count,
            director_breakdown=director_breakdown,
            actor_breakdown=actor_breakdown,
            genre_breakdown=genre_breakdown,
            decade_breakdown=decade_breakdown,
            top_country=top_country,
            top_country_count=top_country_count,
            new_countries_count=new_countries_count,
            franchise_breakdown=franchise_breakdown,
            dominant_mood_after=dominant_mood_after,
            dominant_company=dominant_company,
            new_stamps=new_stamps,
            marathons_unlocked=marathons_unlocked,
            achievements_unlocked=achievements_unlocked,
            collection_deltas=collection_deltas,
            peak_activity_date=peak_activity_date,
            peak_activity_count=peak_activity_count,
            streak_current=streak_current,
            streak_best_in_period=streak_best_in_period,
            friends=friends,
            fun_facts=fun_facts,
            controversy=controversy,
            genre_of_month=genre_of_month,
            genre_of_month_count=genre_of_month_count,
        )

    async def _collection_film_totals_by_slug(self, slugs: list[str]) -> dict[str, int]:
        if not slugs:
            return {}
        rows = (
            await self._session.execute(
                select(Collection.slug, func.count(CollectionFilm.id))
                .select_from(Collection)
                .join(CollectionFilm, CollectionFilm.collection_id == Collection.id)
                .where(Collection.slug.in_(slugs))
                .group_by(Collection.slug)
            )
        ).all()
        return {str(slug): int(count) for slug, count in rows}

    async def _count_new_countries_before_window(
        self,
        *,
        user_id: UUID,
        window_start: dt.datetime,
        window_countries: set[str],
    ) -> int:
        if not window_countries:
            return 0
        prior_rows = (
            await self._session.execute(
                select(Film.countries)
                .join(UserCard, UserCard.film_id == Film.id)
                .where(
                    UserCard.user_id == user_id,
                    UserCard.is_planned.is_(False),
                    _completion_timestamp() < window_start,
                )
            )
        ).all()
        prior_countries: set[str] = set()
        for (countries,) in prior_rows:
            if not countries:
                continue
            for country in countries:
                if isinstance(country, str) and country.strip():
                    prior_countries.add(country.strip())
        return len(window_countries - prior_countries)

    async def _vs_previous_week(
        self,
        *,
        user_id: UUID,
        window_start: dt.datetime,
        total_rated: int,
        average_rating: float,
    ) -> tuple[int | None, float | None]:
        prev_start = window_start - dt.timedelta(days=7)
        prev_end = window_start
        row = (
            await self._session.execute(
                select(
                    func.count(UserCard.id),
                    func.avg(UserCard.rating),
                ).where(
                    UserCard.user_id == user_id,
                    UserCard.is_planned.is_(False),
                    _completion_timestamp() >= prev_start,
                    _completion_timestamp() < prev_end,
                )
            )
        ).one()
        prev_total = int(row[0] or 0)
        if prev_total == 0:
            return None, None
        prev_avg = round(float(row[1]), 1)
        return total_rated - prev_total, round(average_rating - prev_avg, 1)

    async def _actor_breakdown_in_window(
        self,
        *,
        user_id: UUID,
        window_start: dt.datetime,
        window_end: dt.datetime,
        limit: int,
    ) -> list[MonthlyRecapActorItem]:
        rows = (
            await self._session.execute(
                select(
                    Person.kinopoisk_id,
                    Person.name,
                    func.count(UserCard.id),
                )
                .select_from(UserCard)
                .join(Film, Film.id == UserCard.film_id)
                .join(FilmActor, FilmActor.film_id == Film.id)
                .join(Person, Person.id == FilmActor.person_id)
                .where(
                    UserCard.user_id == user_id,
                    UserCard.is_planned.is_(False),
                    _completion_timestamp() >= window_start,
                    _completion_timestamp() < window_end,
                )
                .group_by(Person.kinopoisk_id, Person.name)
                .order_by(desc(func.count(UserCard.id)), Person.name, Person.kinopoisk_id)
                .limit(limit)
            )
        ).all()
        return [
            MonthlyRecapActorItem(
                kinopoisk_id=int(kinopoisk_id),
                label=str(name),
                count=int(count),
            )
            for kinopoisk_id, name, count in rows
        ]

    async def _stamps_unlocked_in_window(
        self,
        *,
        user_id: UUID,
        window_start: dt.datetime,
        window_end: dt.datetime,
    ) -> list[MonthlyRecapStampItem]:
        result = await ComputePassportStampsService.build(self._session).execute(user_id)
        items: list[MonthlyRecapStampItem] = []
        for stamp in result.stamps:
            if not stamp.unlocked or stamp.unlocked_at is None:
                continue
            unlocked_at = stamp.unlocked_at
            if unlocked_at.tzinfo is None:
                unlocked_at = unlocked_at.replace(tzinfo=dt.UTC)
            if window_start <= unlocked_at < window_end:
                items.append(
                    MonthlyRecapStampItem(
                        stamp_id=stamp.stamp_id,
                        title=stamp.title,
                        unlocked_at=unlocked_at,
                    )
                )
        items.sort(key=lambda item: item.unlocked_at)
        return items

    async def _marathons_unlocked_in_window(
        self,
        *,
        user_id: UUID,
        window_start: dt.datetime,
        window_end: dt.datetime,
    ) -> list[MonthlyRecapMarathonItem]:
        achievements = await ComputeMarathonAchievementsService.build(self._session).execute(
            user_id
        )
        items: list[MonthlyRecapMarathonItem] = []
        for achievement in achievements:
            unlocked_at = achievement.unlocked_at
            if unlocked_at.tzinfo is None:
                unlocked_at = unlocked_at.replace(tzinfo=dt.UTC)
            if window_start <= unlocked_at < window_end:
                items.append(
                    MonthlyRecapMarathonItem(
                        kind=achievement.kind,
                        key=achievement.key,
                        label=achievement.label,
                        unlocked_at=unlocked_at,
                    )
                )
        items.sort(key=lambda item: item.unlocked_at)
        return items

    async def _collection_deltas_in_window(
        self,
        *,
        user_id: UUID,
        window_start: dt.datetime,
        window_end: dt.datetime,
    ) -> list[MonthlyRecapCollectionDeltaItem]:
        rows = (
            await self._session.execute(
                select(
                    Collection.slug,
                    Collection.title,
                    func.count(UserCard.id),
                )
                .select_from(UserCard)
                .join(Film, Film.id == UserCard.film_id)
                .join(CollectionFilm, CollectionFilm.film_id == Film.id)
                .join(Collection, Collection.id == CollectionFilm.collection_id)
                .where(
                    UserCard.user_id == user_id,
                    UserCard.is_planned.is_(False),
                    _completion_timestamp() >= window_start,
                    _completion_timestamp() < window_end,
                )
                .group_by(Collection.id, Collection.slug, Collection.title)
                .order_by(desc(func.count(UserCard.id)), Collection.title, Collection.slug)
            )
        ).all()
        return [
            MonthlyRecapCollectionDeltaItem(
                collection_slug=str(slug),
                title=str(title),
                films_rated_in_period=int(count),
            )
            for slug, title, count in rows
        ]

    async def _achievements_unlocked_in_window(
        self,
        *,
        user_id: UUID,
        window_start: dt.datetime,
        window_end: dt.datetime,
    ) -> list[MonthlyRecapAchievementItem]:
        rows = (
            await self._session.execute(
                select(Achievement.slug, Achievement.title, UserAchievement.unlocked_at)
                .join(Achievement, Achievement.id == UserAchievement.achievement_id)
                .where(
                    UserAchievement.user_id == user_id,
                    UserAchievement.unlocked_at >= window_start,
                    UserAchievement.unlocked_at < window_end,
                )
                .order_by(UserAchievement.unlocked_at.asc())
            )
        ).all()
        return [
            MonthlyRecapAchievementItem(
                slug=str(slug),
                title=str(title),
                rarity_percent=None,
            )
            for slug, title, _ in rows
        ]

    async def _controversy_insight(
        self,
        *,
        user_id: UUID,
        window_end: dt.datetime,
    ) -> ControversyInsight | None:
        bundle = await ComputeWeeklyControversyService.build(self._session).execute(
            viewer_user_id=user_id,
            now=window_end - dt.timedelta(seconds=1),
        )
        if bundle is None:
            return None
        primary = bundle.primary
        if primary.spread < MIN_SPREAD_FOR_TELEGRAM_DIGEST:
            return None
        friend_display = 'другом'
        if primary.polar_low is not None:
            friend_display = primary.polar_low.author_display
        elif primary.polar_high is not None:
            friend_display = primary.polar_high.author_display
        return ControversyInsight(
            film_title=primary.title,
            friend_display=friend_display,
            spread=primary.spread,
            anchor_film_id=primary.anchor_film_id,
        )
