from __future__ import annotations

SPOILER_OPEN = '⟦S⟧'
SPOILER_CLOSE = '⟦/S⟧'


class SpoilerTokenValidationError(ValueError):
    """Invalid spoiler block markers in text."""


def validate_spoiler_tokens(body: str) -> str:
    """Ensure spoiler blocks are balanced, non-nested, and non-empty."""
    depth = 0
    open_idx = -1
    i = 0
    length = len(body)

    while i < length:
        if body.startswith(SPOILER_OPEN, i):
            if depth > 0:
                raise SpoilerTokenValidationError('nested spoiler blocks are not allowed')
            depth = 1
            open_idx = i
            i += len(SPOILER_OPEN)
            continue

        if body.startswith(SPOILER_CLOSE, i):
            if depth == 0:
                raise SpoilerTokenValidationError('unmatched spoiler closing marker')
            inner_start = open_idx + len(SPOILER_OPEN)
            inner = body[inner_start:i]
            if inner.strip() == '':
                raise SpoilerTokenValidationError('spoiler block must not be empty')
            depth = 0
            open_idx = -1
            i += len(SPOILER_CLOSE)
            continue

        i += 1

    if depth > 0:
        raise SpoilerTokenValidationError('unclosed spoiler block')

    return body
