from __future__ import annotations

from http import HTTPStatus

import pytest

from providers.tmdb.tmdb_provider_transport import TmdbProviderTransport
from tests.support.fake_tmdb_transport import fight_club_movie_detail


@pytest.mark.asyncio
async def test_find_movie_by_imdb_id_parses_response(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get(
        self: object,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, object] | None = None,
    ) -> dict[str, object]:
        _ = (self, headers, params)
        assert '/find/tt0137523' in url
        return {
            'movie_results': [
                {'id': 550, 'title': 'Fight Club', 'release_date': '1999-10-15'},
            ],
        }

    monkeypatch.setattr(TmdbProviderTransport, 'get', fake_get)
    transport = TmdbProviderTransport()
    found = await transport.find_movie_by_imdb_id('tt0137523')
    assert found.first_movie_id() == 550


@pytest.mark.asyncio
async def test_search_movie_by_title_year(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get(
        self: object,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, object] | None = None,
    ) -> dict[str, object]:
        _ = (self, headers)
        assert url.endswith('/search/movie')
        assert params is not None
        assert params.get('query') == 'Fight Club'
        assert params.get('year') == 1999
        return {'results': [{'id': 550, 'title': 'Fight Club', 'release_date': '1999-10-15'}]}

    monkeypatch.setattr(TmdbProviderTransport, 'get', fake_get)
    transport = TmdbProviderTransport()
    found = await transport.search_movie_by_title_year('Fight Club', 1999)
    assert found.first_movie_id() == 550


@pytest.mark.asyncio
async def test_get_movie_by_id_with_append(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = fight_club_movie_detail().raw

    async def fake_get(
        self: object,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, object] | None = None,
    ) -> dict[str, object]:
        _ = (self, headers)
        assert url.endswith('/movie/550')
        assert params is not None
        assert params.get('append_to_response') == 'credits,external_ids'
        return payload

    monkeypatch.setattr(TmdbProviderTransport, 'get', fake_get)
    transport = TmdbProviderTransport()
    detail = await transport.get_movie_by_id(550)
    assert detail.id == 550
    assert detail.imdb_id == 'tt0137523'


@pytest.mark.asyncio
async def test_get_movie_by_id_not_found_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get(
        self: object,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, object] | None = None,
    ) -> dict[str, object]:
        _ = (self, url, headers, params)
        raise TmdbProviderTransport.ProviderUnexpectedStatusError(
            msg='unexpected status 404',
            status_code=HTTPStatus.NOT_FOUND,
        )

    monkeypatch.setattr(TmdbProviderTransport, 'get', fake_get)
    transport = TmdbProviderTransport()
    with pytest.raises(TmdbProviderTransport.TmdbProviderTransportError, match='movie not found'):
        await transport.get_movie_by_id(999999)
