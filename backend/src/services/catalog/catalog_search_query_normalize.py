"""Normalize catalog search `q` for API, cache keys, and provider calls."""


def normalize_catalog_search_query(text: str) -> str:
    """Trim, collapse internal whitespace, and lowercase for stable keys and matching."""

    return ' '.join(text.strip().split()).lower()
