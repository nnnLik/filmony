from __future__ import annotations

from models.catalog_item import CatalogItem, CatalogProvider
from models.game import Game


def test_catalog_provider_includes_rawg() -> None:
    assert CatalogProvider.rawg.value == 'rawg'


def test_game_rawg_id_unique_constraint() -> None:
    names = {c.name for c in Game.__table__.constraints}
    assert 'uq_game_rawg_id' in names


def test_game_snapshot_and_json_columns_exist() -> None:
    cols = Game.__table__.c
    assert 'raw_search_snapshot' in cols
    assert 'raw_detail_snapshot' in cols
    assert 'platforms_json' in cols
    assert 'esrb_rating_json' in cols
    assert 'search_synced_at' in cols
    assert 'detail_synced_at' in cols


def test_catalog_item_game_id_fk() -> None:
    col = CatalogItem.__table__.c.game_id
    assert col.nullable is True
    fks = list(col.foreign_keys)
    assert len(fks) == 1
    assert fks[0].column.table.name == 'game'
