"""normalize_absolute_http_url — protocol-relative Kinopoisk posters."""

from utils.http_url import normalize_absolute_http_url


def test_normalize_protocol_relative_gets_https() -> None:
    assert normalize_absolute_http_url('//avatars.mds.yandex.net/get/kinopoisk-image/x') == (
        'https://avatars.mds.yandex.net/get/kinopoisk-image/x'
    )


def test_normalize_https_unchanged() -> None:
    assert normalize_absolute_http_url('https://example.com/p.jpg') == 'https://example.com/p.jpg'


def test_normalize_none_and_empty() -> None:
    assert normalize_absolute_http_url(None) is None
    assert normalize_absolute_http_url('') is None
    assert normalize_absolute_http_url('   ') is None
