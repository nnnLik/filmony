from __future__ import annotations

from models.catalog_item import CatalogProvider


def watchlist_card_id_for_provider(provider: CatalogProvider | str, external_id: str) -> str:
    provider_val = provider.value if isinstance(provider, CatalogProvider) else str(provider)
    if provider_val == CatalogProvider.kinopoisk.value:
        return f'kp:{external_id}'
    return f'{provider_val}:{external_id}'
