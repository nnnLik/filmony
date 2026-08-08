"""Rule-based fun facts for personal digest (weekly and monthly)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol, Self
from uuid import UUID

if TYPE_CHECKING:
    from services.profile.build_monthly_recap import (
        MonthlyRecap,
        MonthlyRecapCollectionDeltaItem,
        MonthlyRecapDecadeItem,
        MonthlyRecapDistributionItem,
        MonthlyRecapMarathonItem,
    )

_PERIOD_SCOPE = {'week': 'недели', 'month': 'месяца'}


def _month_period_key(*, year: int, month: int) -> str:
    return f'{year}-{month:02d}'


_DIGEST_WEEKLY_MICROFUN: tuple[str, ...] = (
    'Неделя как неделя — только с оценками',
    'Pepe одобряет этот ритм просмотров',
    'Семь дней — семь поводов открыть Filmony',
    'Маленький отрезок, большая статистика',
    'Неделя прошла, popcorn statistics остались',
    'Три фильма за неделю — уже социальная жизнь',
)

_DIGEST_MONTHLY_MICROFUN: tuple[str, ...] = (
    'Месяц как месяц — только с оценками',
    'Pepe подводит итоги: не всё так плохо',
    'Календарь перевернулся — статистика осталась',
    'Тридцать дней пролетели, оценки остались',
    'Месячный отчёт готов. Pepe кивает',
    'Итоги месяца: цифры не врут',
)


@dataclass(frozen=True, slots=True)
class FunFactItem:
    rule_id: str
    text: str
    score: float


@dataclass(frozen=True, slots=True)
class DigestBuildContext:
    user_id: UUID
    period: Literal['week', 'month']
    period_key: str
    total_rated: int
    ratings: tuple[float, ...]
    genre_breakdown: tuple[tuple[str, int], ...]
    decade_breakdown: tuple[tuple[int, int], ...]
    marathons_unlocked: tuple[str, ...]
    collection_deltas: tuple[tuple[str, str, int, int | None], ...]
    new_countries_count: int
    streak_best_in_period: int


class DigestInsightRule(Protocol):
    rule_id: str

    def try_build(self, ctx: DigestBuildContext) -> FunFactItem | None: ...


def _period_scope(period: Literal['week', 'month']) -> str:
    return _PERIOD_SCOPE[period]


def _deterministic_index(*, seed: str, modulo: int) -> int:
    if modulo <= 0:
        return 0
    digest = hashlib.sha256(seed.encode()).hexdigest()
    return int(digest[:16], 16) % modulo


@dataclass(frozen=True, slots=True)
class GenreDominanceRule:
    rule_id: str = 'genre_dominance'

    def try_build(self, ctx: DigestBuildContext) -> FunFactItem | None:
        if ctx.total_rated <= 0 or not ctx.genre_breakdown:
            return None
        genre, count = max(ctx.genre_breakdown, key=lambda item: item[1])
        pct = round(count * 100 / ctx.total_rated)
        if pct < 60:
            return None
        scope = _period_scope(ctx.period)
        return FunFactItem(
            rule_id=self.rule_id,
            text=f'{genre} — {pct}% {scope}',
            score=float(pct),
        )


@dataclass(frozen=True, slots=True)
class RatingAllHighRule:
    rule_id: str = 'rating_all_high'

    def try_build(self, ctx: DigestBuildContext) -> FunFactItem | None:
        if not ctx.ratings:
            return None
        if any(rating < 8 for rating in ctx.ratings):
            return None
        return FunFactItem(
            rule_id=self.rule_id,
            text='Без разочарований',
            score=80.0,
        )


@dataclass(frozen=True, slots=True)
class RatingWideSpreadRule:
    rule_id: str = 'rating_wide_spread'

    def try_build(self, ctx: DigestBuildContext) -> FunFactItem | None:
        if len(ctx.ratings) < 2:
            return None
        min_rating = min(ctx.ratings)
        max_rating = max(ctx.ratings)
        spread = max_rating - min_rating
        if spread < 4:
            return None
        min_label = int(min_rating) if min_rating == int(min_rating) else min_rating
        max_label = int(max_rating) if max_rating == int(max_rating) else max_rating
        return FunFactItem(
            rule_id=self.rule_id,
            text=f'Разброс вкуса {min_label}–{max_label}',
            score=float(spread * 10),
        )


@dataclass(frozen=True, slots=True)
class EraSkewRule:
    rule_id: str = 'era_skew'

    def try_build(self, ctx: DigestBuildContext) -> FunFactItem | None:
        if ctx.total_rated <= 0 or not ctx.decade_breakdown:
            return None
        decade_start, count = max(ctx.decade_breakdown, key=lambda item: item[1])
        pct = round(count * 100 / ctx.total_rated)
        if pct < 50:
            return None
        return FunFactItem(
            rule_id=self.rule_id,
            text=f'Одержим {decade_start}-ми',
            score=float(pct),
        )


@dataclass(frozen=True, slots=True)
class CollectionSprintRule:
    rule_id: str = 'collection_sprint'

    def try_build(self, ctx: DigestBuildContext) -> FunFactItem | None:
        best: FunFactItem | None = None
        for _slug, title, films_rated, total_films in ctx.collection_deltas:
            if total_films is None or total_films <= 0:
                continue
            pct = films_rated * 100 / total_films
            if pct < 10:
                continue
            candidate = FunFactItem(
                rule_id=self.rule_id,
                text=f'Прокачал {title}',
                score=float(pct),
            )
            if best is None or candidate.score > best.score:
                best = candidate
        return best


@dataclass(frozen=True, slots=True)
class MarathonCompleteRule:
    rule_id: str = 'marathon_complete'

    def try_build(self, ctx: DigestBuildContext) -> FunFactItem | None:
        if not ctx.marathons_unlocked:
            return None
        label = ctx.marathons_unlocked[0]
        return FunFactItem(
            rule_id=self.rule_id,
            text=f'Закрыл марафон {label}',
            score=70.0,
        )


@dataclass(frozen=True, slots=True)
class NewCountryBurstRule:
    rule_id: str = 'new_country_burst'

    def try_build(self, ctx: DigestBuildContext) -> FunFactItem | None:
        if ctx.new_countries_count < 3:
            return None
        return FunFactItem(
            rule_id=self.rule_id,
            text=f'{ctx.new_countries_count} новых стран',
            score=float(ctx.new_countries_count * 15),
        )


@dataclass(frozen=True, slots=True)
class StreakRecordRule:
    rule_id: str = 'streak_record'

    def try_build(self, ctx: DigestBuildContext) -> FunFactItem | None:
        if ctx.streak_best_in_period < 7:
            return None
        return FunFactItem(
            rule_id=self.rule_id,
            text=f'Рекорд серии: {ctx.streak_best_in_period}',
            score=float(ctx.streak_best_in_period * 5),
        )


@dataclass(frozen=True, slots=True)
class MicrofunFallbackRule:
    rule_id: str = 'microfun_fallback'

    def try_build(self, ctx: DigestBuildContext) -> FunFactItem | None:
        pool = _DIGEST_WEEKLY_MICROFUN if ctx.period == 'week' else _DIGEST_MONTHLY_MICROFUN
        if not pool:
            return None
        index = _deterministic_index(
            seed=f'{ctx.user_id}{ctx.period_key}{self.rule_id}',
            modulo=len(pool),
        )
        return FunFactItem(
            rule_id=self.rule_id,
            text=pool[index],
            score=1.0,
        )


_DEFAULT_RULES: tuple[DigestInsightRule, ...] = (
    GenreDominanceRule(),
    RatingAllHighRule(),
    RatingWideSpreadRule(),
    EraSkewRule(),
    CollectionSprintRule(),
    MarathonCompleteRule(),
    NewCountryBurstRule(),
    StreakRecordRule(),
)


def build_digest_context_for_month(
    *,
    user_id: UUID,
    year: int,
    month: int,
    total_rated: int,
    ratings: tuple[float, ...],
    genre_breakdown: list[MonthlyRecapDistributionItem],
    decade_breakdown: list[MonthlyRecapDecadeItem],
    marathons_unlocked: list[MonthlyRecapMarathonItem],
    collection_deltas: list[MonthlyRecapCollectionDeltaItem],
    new_countries_count: int,
    streak_best_in_period: int,
    collection_totals: dict[str, int] | None = None,
) -> DigestBuildContext:
    totals = collection_totals or {}
    return DigestBuildContext(
        user_id=user_id,
        period='month',
        period_key=_month_period_key(year=year, month=month),
        total_rated=total_rated,
        ratings=ratings,
        genre_breakdown=tuple((item.label, item.count) for item in genre_breakdown),
        decade_breakdown=tuple((item.decade_start, item.count) for item in decade_breakdown),
        marathons_unlocked=tuple(item.label for item in marathons_unlocked),
        collection_deltas=_collection_delta_tuples(collection_deltas, totals),
        new_countries_count=new_countries_count,
        streak_best_in_period=streak_best_in_period,
    )


def build_digest_context_from_monthly_recap(
    recap: MonthlyRecap,
    *,
    ratings: tuple[float, ...],
    collection_totals: dict[str, int] | None = None,
) -> DigestBuildContext:
    return build_digest_context_for_month(
        user_id=recap.user_id,
        year=recap.year,
        month=recap.month,
        total_rated=recap.total_rated,
        ratings=ratings,
        genre_breakdown=list(recap.genre_breakdown),
        decade_breakdown=list(recap.decade_breakdown),
        marathons_unlocked=list(recap.marathons_unlocked),
        collection_deltas=list(recap.collection_deltas),
        new_countries_count=recap.new_countries_count,
        streak_best_in_period=recap.streak_best_in_period,
        collection_totals=collection_totals,
    )


def build_digest_context_for_week(
    *,
    user_id: UUID,
    period_key: str,
    total_rated: int,
    ratings: tuple[float, ...],
    genre_breakdown: list[MonthlyRecapDistributionItem],
    decade_breakdown: list[MonthlyRecapDecadeItem],
    marathons_unlocked: list[MonthlyRecapMarathonItem],
    collection_deltas: list[MonthlyRecapCollectionDeltaItem],
    new_countries_count: int,
    streak_best_in_period: int,
    collection_totals: dict[str, int] | None = None,
) -> DigestBuildContext:
    totals = collection_totals or {}
    return DigestBuildContext(
        user_id=user_id,
        period='week',
        period_key=period_key,
        total_rated=total_rated,
        ratings=ratings,
        genre_breakdown=tuple((item.label, item.count) for item in genre_breakdown),
        decade_breakdown=tuple((item.decade_start, item.count) for item in decade_breakdown),
        marathons_unlocked=tuple(item.label for item in marathons_unlocked),
        collection_deltas=_collection_delta_tuples(collection_deltas, totals),
        new_countries_count=new_countries_count,
        streak_best_in_period=streak_best_in_period,
    )


def _collection_delta_tuples(
    deltas: list[MonthlyRecapCollectionDeltaItem],
    collection_totals: dict[str, int],
) -> tuple[tuple[str, str, int, int | None], ...]:
    return tuple(
        (
            delta.collection_slug,
            delta.title,
            delta.films_rated_in_period,
            collection_totals.get(delta.collection_slug),
        )
        for delta in deltas
    )


@dataclass
class BuildPersonalDigestFunFactsService:
    """Scores digest insight rules and returns top fun-fact lines for a period."""

    _rules: tuple[DigestInsightRule, ...] = _DEFAULT_RULES
    _microfun_rule: MicrofunFallbackRule = MicrofunFallbackRule()

    @classmethod
    def build(cls) -> Self:
        return cls()

    def execute(self, ctx: DigestBuildContext) -> list[str]:
        top_k = 3 if ctx.period == 'week' else 5
        items = self._collect_rule_items(ctx)
        items = self._apply_microfun_fallback(ctx, items)
        selected = self._select_top_k(items, ctx=ctx, top_k=top_k)
        return [item.text for item in selected]

    def _collect_rule_items(self, ctx: DigestBuildContext) -> list[FunFactItem]:
        items: list[FunFactItem] = []
        for rule in self._rules:
            built = rule.try_build(ctx)
            if built is not None:
                items.append(built)
        return items

    def _apply_microfun_fallback(
        self,
        ctx: DigestBuildContext,
        items: list[FunFactItem],
    ) -> list[FunFactItem]:
        if len(items) >= 2:
            return items
        pool = _DIGEST_WEEKLY_MICROFUN if ctx.period == 'week' else _DIGEST_MONTHLY_MICROFUN
        if not pool:
            return items
        result = list(items)
        fallback_index = 0
        while len(result) < 2:
            seed = f'{ctx.user_id}{ctx.period_key}microfun{fallback_index}'
            index = _deterministic_index(seed=seed, modulo=len(pool))
            text = pool[index]
            if not any(
                item.rule_id == 'microfun_fallback' and item.text == text for item in result
            ):
                result.append(
                    FunFactItem(
                        rule_id='microfun_fallback',
                        text=text,
                        score=1.0,
                    )
                )
            fallback_index += 1
            if fallback_index > len(pool) * 2:
                break
        return result

    def _select_top_k(
        self,
        items: list[FunFactItem],
        *,
        ctx: DigestBuildContext,
        top_k: int,
    ) -> list[FunFactItem]:
        if top_k <= 0:
            return []
        unique: dict[str, FunFactItem] = {}
        for item in items:
            key = (
                f'{item.rule_id}:{item.text}'
                if item.rule_id == 'microfun_fallback'
                else item.rule_id
            )
            existing = unique.get(key)
            if existing is None or item.score > existing.score:
                unique[key] = item
        ranked = sorted(
            unique.values(),
            key=lambda item: (
                -item.score,
                _deterministic_index(
                    seed=f'{ctx.user_id}{ctx.period_key}{item.rule_id}',
                    modulo=10_000,
                ),
                item.rule_id,
            ),
        )
        return ranked[:top_k]


__all__ = (
    'BuildPersonalDigestFunFactsService',
    'DigestBuildContext',
    'FunFactItem',
    'build_digest_context_for_month',
    'build_digest_context_for_week',
    'build_digest_context_from_monthly_recap',
)
