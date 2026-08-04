from __future__ import annotations

from providers.tmdb.tmdb_credits_dto import TmdbCreditsDTO, TmdbCrewMemberDTO
from providers.tmdb.tmdb_find_dto import TmdbFindMovieResultDTO, TmdbFindResponseDTO
from providers.tmdb.tmdb_movie_dto import (
    TmdbCollectionRefDTO,
    TmdbMovieDetailDTO,
    TmdbProductionCountryDTO,
)


def fight_club_movie_detail() -> TmdbMovieDetailDTO:
    raw = {
        'id': 550,
        'imdb_id': 'tt0137523',
        'title': 'Бойцовский клуб',
        'original_title': 'Fight Club',
        'overview': 'A ticking-time-bomb insomniac...',
        'release_date': '1999-10-15',
        'poster_path': '/pB8BM7pdSpoB0x7enTRSh4DkOlS.jpg',
        'production_countries': [
            {'iso_3166_1': 'US', 'name': 'Соединенные Штаты Америки'},
        ],
        'belongs_to_collection': None,
        'credits': {
            'id': 550,
            'crew': [
                {
                    'id': 6886,
                    'name': 'David Fincher',
                    'job': 'Director',
                    'department': 'Directing',
                },
            ],
        },
    }
    return TmdbMovieDetailDTO(
        id=550,
        title='Бойцовский клуб',
        original_title='Fight Club',
        overview='A ticking-time-bomb insomniac...',
        release_date='1999-10-15',
        poster_path='/pB8BM7pdSpoB0x7enTRSh4DkOlS.jpg',
        imdb_id='tt0137523',
        belongs_to_collection=None,
        production_countries=(
            TmdbProductionCountryDTO(
                iso_3166_1='US',
                name='Соединенные Штаты Америки',
            ),
        ),
        credits=TmdbCreditsDTO(
            id=550,
            crew=(
                TmdbCrewMemberDTO(
                    id=6886,
                    name='David Fincher',
                    job='Director',
                    department='Directing',
                ),
            ),
        ),
        raw=raw,
    )


def star_wars_collection_movie_detail() -> TmdbMovieDetailDTO:
    raw = {
        'id': 11,
        'imdb_id': 'tt0076759',
        'title': 'Звёздные войны',
        'original_title': 'Star Wars',
        'overview': 'A long time ago...',
        'release_date': '1977-05-25',
        'poster_path': '/6FfCtAuVAW8XJjZ7eWeLibRLWTw.jpg',
        'production_countries': [
            {'iso_3166_1': 'US', 'name': 'United States of America'},
        ],
        'belongs_to_collection': {
            'id': 10,
            'name': 'Star Wars Collection',
            'poster_path': '/pWVLFh4OuejTpUaDQbB1C4zoS2p.jpg',
            'backdrop_path': '/iY2ujEY2m68OTTlPFTiHub9joHS.jpg',
        },
        'credits': {
            'id': 11,
            'crew': [
                {
                    'id': 1,
                    'name': 'George Lucas',
                    'job': 'Director',
                    'department': 'Directing',
                },
            ],
        },
    }
    return TmdbMovieDetailDTO(
        id=11,
        title='Звёздные войны',
        original_title='Star Wars',
        overview='A long time ago...',
        release_date='1977-05-25',
        poster_path='/6FfCtAuVAW8XJjZ7eWeLibRLWTw.jpg',
        imdb_id='tt0076759',
        belongs_to_collection=TmdbCollectionRefDTO(
            id=10,
            name='Star Wars Collection',
            poster_path='/pWVLFh4OuejTpUaDQbB1C4zoS2p.jpg',
            backdrop_path='/iY2ujEY2m68OTTlPFTiHub9joHS.jpg',
        ),
        production_countries=(
            TmdbProductionCountryDTO(iso_3166_1='US', name='United States of America'),
        ),
        credits=TmdbCreditsDTO(
            id=11,
            crew=(
                TmdbCrewMemberDTO(
                    id=1,
                    name='George Lucas',
                    job='Director',
                    department='Directing',
                ),
            ),
        ),
        raw=raw,
    )


class FakeTmdbTransport:
    def __init__(
        self,
        *,
        find_by_imdb: dict[str, int] | None = None,
        movies_by_id: dict[int, TmdbMovieDetailDTO] | None = None,
        search_results: dict[tuple[str, int | None], int] | None = None,
    ) -> None:
        self._find_by_imdb = find_by_imdb or {}
        self._movies_by_id = movies_by_id or {}
        self._search_results = search_results or {}

    async def find_movie_by_imdb_id(self, imdb_id: str) -> TmdbFindResponseDTO:
        movie_id = self._find_by_imdb.get(imdb_id)
        if movie_id is None:
            return TmdbFindResponseDTO.empty()
        return TmdbFindResponseDTO(
            movie_results=(
                TmdbFindMovieResultDTO(
                    id=movie_id,
                    title=f'TMDB #{movie_id}',
                    release_date=None,
                ),
            ),
        )

    async def search_movie_by_title_year(
        self,
        title: str,
        year: int | None,
    ) -> TmdbFindResponseDTO:
        movie_id = self._search_results.get((title.strip(), year))
        if movie_id is None:
            return TmdbFindResponseDTO.empty()
        return TmdbFindResponseDTO(
            movie_results=(
                TmdbFindMovieResultDTO(
                    id=movie_id,
                    title=title.strip(),
                    release_date=str(year) if year is not None else None,
                ),
            ),
        )

    async def get_movie_by_id(
        self,
        tmdb_id: int,
        *,
        append: tuple[str, ...] = ('credits', 'external_ids'),
    ) -> TmdbMovieDetailDTO:
        _ = append
        movie = self._movies_by_id.get(tmdb_id)
        if movie is None:
            raise RuntimeError(f'unknown tmdb id {tmdb_id}')
        return movie
