from __future__ import annotations

from types import SimpleNamespace

from api.reactions.schemas import ReactionCatalogItemResponse
from services.reactions.list_reaction_catalog import _row


def test_catalog_row_and_schema_include_shortcode() -> None:
    rt = SimpleNamespace(
        id=12,
        asset_key='reactions/pepe/9137-gasp.png',
        image_url='https://example.com/gasp.png',
        category_slug='pepe',
        shortcode='gasp',
    )
    item = _row(rt)
    assert item.shortcode == 'gasp'
    assert item.id == 12
    payload = ReactionCatalogItemResponse(
        id=item.id,
        image_url=item.image_url,
        category_slug=item.category_slug,
        asset_key=item.asset_key,
        shortcode=item.shortcode,
    )
    assert payload.model_dump()['shortcode'] == 'gasp'
