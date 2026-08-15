from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from providers.tmdb.tmdb_snapshot_trailer import extract_youtube_trailer_url
from providers.tmdb.tmdb_snapshot_watch_providers import extract_ru_watch_provider_names
from services.films.resolve_tmdb_recommendations import ResolveTmdbRecommendationsService


def film_passport_response_fields(film: Film) -> dict[str, object]:
    return {
        'film_length': film.film_length,
        'slogan': film.slogan,
        'rating_kinopoisk': film.rating_kinopoisk,
        'rating_imdb': film.rating_imdb,
        'rating_age_limits': film.rating_age_limits,
        'trailer_youtube_url': extract_youtube_trailer_url(film.tmdb_detail_snapshot_json),
        'watch_providers_ru': extract_ru_watch_provider_names(film.tmdb_detail_snapshot_json),
    }


async def build_film_passport_response_fields(
    session: AsyncSession,
    film: Film,
) -> dict[str, object]:
    fields = film_passport_response_fields(film)
    recommendations = await ResolveTmdbRecommendationsService.build(session).execute(film)
    fields['tmdb_recommendations'] = [
        {
            'title': item.title,
            'film_id': item.film_id,
            'in_catalog': item.in_catalog,
        }
        for item in recommendations
    ]
    return fields


__all__ = ('build_film_passport_response_fields', 'film_passport_response_fields')
