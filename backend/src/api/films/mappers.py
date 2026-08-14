from __future__ import annotations

from models.film import Film
from providers.tmdb.tmdb_snapshot_recommendations import extract_tmdb_recommendation_titles
from providers.tmdb.tmdb_snapshot_trailer import extract_youtube_trailer_url
from providers.tmdb.tmdb_snapshot_watch_providers import extract_ru_watch_provider_names


def film_passport_response_fields(film: Film) -> dict[str, object]:
    snapshot = film.tmdb_detail_snapshot_json
    return {
        'film_length': film.film_length,
        'slogan': film.slogan,
        'rating_kinopoisk': film.rating_kinopoisk,
        'rating_imdb': film.rating_imdb,
        'rating_age_limits': film.rating_age_limits,
        'tmdb_recommendations': extract_tmdb_recommendation_titles(snapshot),
        'trailer_youtube_url': extract_youtube_trailer_url(snapshot),
        'watch_providers_ru': extract_ru_watch_provider_names(snapshot),
    }


__all__ = ('film_passport_response_fields',)
