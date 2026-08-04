from __future__ import annotations

from models.catalog_item import CatalogItem
from models.user_card import UserCard


def test_catalog_item_provider_external_unique_name() -> None:
    names = {c.name for c in CatalogItem.__table__.constraints}
    assert 'uq_catalog_item_provider_external' in names


def test_movie_card_user_card_category_fk_not_null() -> None:
    col = UserCard.__table__.c.user_card_category_id
    assert col.nullable is False


def test_movie_card_provider_subject_columns() -> None:
    cols = UserCard.__table__.c
    assert cols.provider.nullable is False
    assert cols.external_id.nullable is True


def test_movie_card_kinopoisk_external_partial_unique_index() -> None:
    partial_names = {
        ix.name
        for ix in UserCard.__table__.indexes
        if ix.dialect_options.get('postgresql', {}).get('where') is not None
    }
    assert 'uq_user_card_user_provider_external_kinopoisk_partial' in partial_names


def test_movie_card_film_and_catalog_columns_nullable() -> None:
    assert UserCard.__table__.c.film_id.nullable is True
    assert UserCard.__table__.c.catalog_item_id.nullable is True


def test_movie_card_partial_unique_index_definitions() -> None:
    partial_names = {
        ix.name
        for ix in UserCard.__table__.indexes
        if ix.dialect_options.get('postgresql', {}).get('where') is not None
    }
    assert 'uq_user_card_user_catalog_item_id_partial' in partial_names
    assert 'uq_user_card_user_film_id_partial' in partial_names


def test_movie_card_legacy_global_unique_removed() -> None:
    legacy = {c.name for c in UserCard.__table__.constraints}
    assert 'uq_movie_card_user_film' not in legacy


def test_movie_card_user_display_columns_nullable() -> None:
    cols = UserCard.__table__.c
    assert cols.display_title.nullable is True
    assert cols.display_cover_url.nullable is True
    assert cols.display_summary.nullable is True
    assert cols.source_url.nullable is True


def test_manual_movie_card_can_have_title_without_catalog_or_film_link() -> None:
    """Manual cards store display_title; catalog_item_id and film_id may both be NULL."""
    cols = UserCard.__table__.c
    assert cols.film_id.nullable is True
    assert cols.catalog_item_id.nullable is True
    assert cols.display_title.nullable is True
