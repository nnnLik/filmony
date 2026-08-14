from __future__ import annotations

from models.film import Film
from providers.tmdb.tmdb_snapshot_recommendations import extract_tmdb_recommendation_titles
from providers.tmdb.tmdb_snapshot_trailer import extract_youtube_trailer_url
from providers.tmdb.tmdb_snapshot_watch_providers import extract_ru_watch_provider_names


def film_passport_response_fields(film: Film) -> dict[str, object]:
    snapshot = film.tmdb_detail_snapshot_json
    passport = film.kinopoisk_passport
    return {
        'film_length': passport.film_length if passport is not None else None,
        'slogan': passport.slogan if passport is not None else None,
        'rating_kinopoisk': passport.rating_kinopoisk if passport is not None else None,
        'rating_imdb': passport.rating_imdb if passport is not None else None,
        'rating_age_limits': passport.rating_age_limits if passport is not None else None,
        'tmdb_recommendations': extract_tmdb_recommendation_titles(snapshot),
        'trailer_youtube_url': extract_youtube_trailer_url(snapshot),
        'watch_providers_ru': extract_ru_watch_provider_names(snapshot),
    }


__all__ = ('film_passport_response_fields',)
