from __future__ import annotations

from providers.rawg.rawg_openapi_dto import (
    RawgGameDTO,
    RawgGameSingleDTO,
    RawgGamesListResponseDTO,
    rawg_open_blob_to_plain_json,
)


def test_rawg_game_single_accepts_list_reactions() -> None:
    doc = {
        'id': 420,
        'slug': 'detail-blob',
        'name': 'Detail Blob',
        'name_original': None,
        'description': None,
        'metacritic': None,
        'metacritic_platforms': [],
        'released': None,
        'tba': False,
        'updated': None,
        'background_image': None,
        'background_image_additional': None,
        'website': None,
        'rating': 0.0,
        'rating_top': None,
        'ratings': [],
        'reactions': [{'like': 1}],
        'added': None,
        'added_by_status': [],
        'playtime': None,
        'screenshots_count': None,
        'movies_count': None,
        'creators_count': None,
        'achievements_count': None,
        'parent_achievements_count': None,
        'reddit_url': None,
        'reddit_name': None,
        'reddit_description': None,
        'reddit_logo': None,
        'reddit_count': None,
        'twitch_count': None,
        'youtube_count': None,
        'reviews_text_count': None,
        'ratings_count': None,
        'suggestions_count': None,
        'alternative_names': [],
        'metacritic_url': None,
        'parents_count': None,
        'additions_count': None,
        'game_series_count': None,
        'esrb_rating': None,
        'platforms': [],
    }
    dto = RawgGameSingleDTO.from_dict(doc)
    assert rawg_open_blob_to_plain_json(dto.reactions) == [{'like': 1}]


def _minimal_list_game_row(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        'id': 9_131_099,
        'slug': 'witcher-blob-test',
        'name': 'Witcher Blob Test',
        'released': None,
        'tba': False,
        'background_image': None,
        'rating': 0.0,
        'rating_top': None,
        'ratings': {},
        'ratings_count': None,
        'reviews_text_count': None,
        'added': None,
        'added_by_status': {},
        'metacritic': None,
        'playtime': None,
        'suggestions_count': None,
        'updated': None,
        'esrb_rating': None,
        'platforms': [],
    }
    base.update(overrides)
    return base


def test_rawg_game_dto_parses_ratings_as_empty_list() -> None:
    dto = RawgGameDTO.from_dict(
        _minimal_list_game_row(
            ratings=[],
            added_by_status=[],
        ),
    )
    assert rawg_open_blob_to_plain_json(dto.ratings) == []
    assert rawg_open_blob_to_plain_json(dto.added_by_status) == []


def test_rawg_game_dto_parses_ratings_as_aggregate_list_preserves_entries() -> None:
    ratings_live = [
        {'id': 5, 'title': 'exceptional', 'count': 120, 'percent': 12.34},
        {'id': 4, 'title': 'recommended', 'count': 400, 'percent': 40.0},
    ]
    dto = RawgGameDTO.from_dict(_minimal_list_game_row(ratings=ratings_live))
    out = rawg_open_blob_to_plain_json(dto.ratings)
    assert out == ratings_live


def test_rawg_games_list_response_parses_when_results_have_list_ratings() -> None:
    doc = {
        'count': 1,
        'next': None,
        'previous': None,
        'results': [
            _minimal_list_game_row(
                id=9_131_100,
                slug='g2',
                name='Second',
                ratings=[],
                added_by_status=[
                    {'title': 'owned', 'yesterday': 1},
                ],
            ),
        ],
    }
    parsed = RawgGamesListResponseDTO.from_document(doc)
    assert parsed.count == 1
    assert len(parsed.results) == 1
    blob = rawg_open_blob_to_plain_json(parsed.results[0].ratings)
    assert blob == []
    assert rawg_open_blob_to_plain_json(parsed.results[0].added_by_status) == [
        {'title': 'owned', 'yesterday': 1}
    ]
