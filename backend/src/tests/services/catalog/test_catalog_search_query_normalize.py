from __future__ import annotations

from services.catalog.catalog_search_query_normalize import normalize_catalog_search_query


def test_normalize_catalog_search_query_collapses_whitespace_lowercases() -> None:
    assert normalize_catalog_search_query('  Foo   Bar  ') == 'foo bar'
    assert normalize_catalog_search_query('HELLO') == 'hello'
    assert normalize_catalog_search_query('') == ''
    assert normalize_catalog_search_query('   \n\t  ') == ''
