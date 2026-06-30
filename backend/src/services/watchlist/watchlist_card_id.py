from __future__ import annotations

from models.catalog_item import CatalogProvider
from models.user_card import UserCard


def watchlist_card_id_for_provider(provider: CatalogProvider | str, external_id: str) -> str:
    provider_val = provider.value if isinstance(provider, CatalogProvider) else str(provider)
    if provider_val == CatalogProvider.kinopoisk.value:
        return f'kp:{external_id}'
    return f'{provider_val}:{external_id}'


def watchlist_card_id_from_user_card(card: UserCard) -> str | None:
    """Maps a planned ``UserCard`` row to the watchlist ``card_id`` key."""
    source_url = (card.source_url or '').strip()
    if source_url.startswith('custom:'):
        return source_url
    external_id = (card.external_id or '').strip()
    if external_id == '':
        return None
    return watchlist_card_id_for_provider(card.provider, external_id)
