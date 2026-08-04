from __future__ import annotations

import pytest

from services.text.spoiler_tokens import (
    SPOILER_CLOSE,
    SPOILER_OPEN,
    SpoilerTokenValidationError,
    validate_spoiler_tokens,
)


def test_validate_spoiler_tokens_accepts_balanced_block() -> None:
    body = f'before {SPOILER_OPEN}secret{SPOILER_CLOSE} after'
    assert validate_spoiler_tokens(body) == body


def test_validate_spoiler_tokens_rejects_unclosed_block() -> None:
    with pytest.raises(SpoilerTokenValidationError, match='unclosed'):
        validate_spoiler_tokens(f'{SPOILER_OPEN}secret')


def test_validate_spoiler_tokens_rejects_unmatched_close() -> None:
    with pytest.raises(SpoilerTokenValidationError, match='unmatched'):
        validate_spoiler_tokens(f'secret{SPOILER_CLOSE}')


def test_validate_spoiler_tokens_rejects_nested_blocks() -> None:
    nested = f'{SPOILER_OPEN}outer {SPOILER_OPEN}inner{SPOILER_CLOSE}{SPOILER_CLOSE}'
    with pytest.raises(SpoilerTokenValidationError, match='nested'):
        validate_spoiler_tokens(nested)


def test_validate_spoiler_tokens_rejects_empty_block() -> None:
    with pytest.raises(SpoilerTokenValidationError, match='empty'):
        validate_spoiler_tokens(f'{SPOILER_OPEN}{SPOILER_CLOSE}')
