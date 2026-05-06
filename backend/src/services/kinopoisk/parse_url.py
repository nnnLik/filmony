from __future__ import annotations

import re
from urllib.parse import urlparse


class KinopoiskUrlParseError(Exception):
    pass


_FILM_ID_PATTERN = re.compile(r'/film/(\d+)(?:/|$)')


def parse_kinopoisk_film_id(url: str) -> int:
    value = url.strip()
    if value == '':
        raise KinopoiskUrlParseError('empty url')

    parsed = urlparse(value)
    host = parsed.netloc.lower()
    if not host.endswith('kinopoisk.ru'):
        raise KinopoiskUrlParseError('url must be from kinopoisk.ru')

    match = _FILM_ID_PATTERN.search(parsed.path)
    if match is None:
        raise KinopoiskUrlParseError('film id was not found in url')
    return int(match.group(1))
