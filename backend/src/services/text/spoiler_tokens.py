from __future__ import annotations

SPOILER_OPEN = '⟦S⟧'
SPOILER_CLOSE = '⟦/S⟧'
PIPE_SPOILER_MARK = '||'

_KIND_PIPE = 'pipe'
_KIND_LEGACY = 'legacy'


class SpoilerTokenValidationError(ValueError):
    """Invalid spoiler block markers in text."""


def validate_spoiler_tokens(body: str) -> str:
    """Ensure spoiler blocks are balanced, non-nested, and non-empty.

    Accepts ``||inner||`` and legacy ``⟦S⟧inner⟦/S⟧``. Returns a canonical
    body with every valid block rewritten to ``||inner||``.
    """
    pieces: list[str] = []
    last_copy = 0
    depth = 0
    open_idx = -1
    open_kind: str | None = None
    i = 0
    length = len(body)

    while i < length:
        if depth == 0:
            if body.startswith(SPOILER_OPEN, i):
                pieces.append(body[last_copy:i])
                depth = 1
                open_idx = i
                open_kind = _KIND_LEGACY
                i += len(SPOILER_OPEN)
                continue
            if body.startswith(PIPE_SPOILER_MARK, i):
                pieces.append(body[last_copy:i])
                depth = 1
                open_idx = i
                open_kind = _KIND_PIPE
                i += len(PIPE_SPOILER_MARK)
                continue
            if body.startswith(SPOILER_CLOSE, i):
                raise SpoilerTokenValidationError('unmatched spoiler closing marker')
            i += 1
            continue

        if open_kind == _KIND_LEGACY:
            if body.startswith(SPOILER_CLOSE, i):
                inner = body[open_idx + len(SPOILER_OPEN) : i]
                if inner.strip() == '':
                    raise SpoilerTokenValidationError('spoiler block must not be empty')
                pieces.append(PIPE_SPOILER_MARK + inner + PIPE_SPOILER_MARK)
                last_copy = i + len(SPOILER_CLOSE)
                depth = 0
                open_idx = -1
                open_kind = None
                i = last_copy
                continue
            if body.startswith(SPOILER_OPEN, i) or body.startswith(PIPE_SPOILER_MARK, i):
                raise SpoilerTokenValidationError('nested spoiler blocks are not allowed')
        elif open_kind == _KIND_PIPE:
            if body.startswith(PIPE_SPOILER_MARK, i):
                inner = body[open_idx + len(PIPE_SPOILER_MARK) : i]
                if inner.strip() == '':
                    raise SpoilerTokenValidationError('spoiler block must not be empty')
                pieces.append(PIPE_SPOILER_MARK + inner + PIPE_SPOILER_MARK)
                last_copy = i + len(PIPE_SPOILER_MARK)
                depth = 0
                open_idx = -1
                open_kind = None
                i = last_copy
                continue
            if body.startswith(SPOILER_OPEN, i) or body.startswith(SPOILER_CLOSE, i):
                raise SpoilerTokenValidationError('nested spoiler blocks are not allowed')

        i += 1

    if depth > 0:
        raise SpoilerTokenValidationError('unclosed spoiler block')

    pieces.append(body[last_copy:])
    return ''.join(pieces)
