from __future__ import annotations


def escape_ilike_pattern(term: str) -> str:
    """Escape `%`, `_`, and `\\` for use with LIKE/ILIKE and `escape='\\\\'`."""
    return term.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
