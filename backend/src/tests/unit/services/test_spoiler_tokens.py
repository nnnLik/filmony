from __future__ import annotations

import pytest

from services.text.spoiler_tokens import (
    PIPE_SPOILER_MARK,
    SPOILER_CLOSE,
    SPOILER_OPEN,
    SpoilerTokenValidationError,
    validate_spoiler_tokens,
)


def test_validate_spoiler_tokens_accepts_balanced_block() -> None:
    body = f'before {SPOILER_OPEN}secret{SPOILER_CLOSE} after'
    assert validate_spoiler_tokens(body) == 'before ||secret|| after'


def test_validate_spoiler_tokens_accepts_pipe_block() -> None:
    body = 'before ||secret|| after'
    assert validate_spoiler_tokens(body) == body


def test_validate_spoiler_tokens_canonicalizes_legacy_to_pipe() -> None:
    body = f'{SPOILER_OPEN}secret{SPOILER_CLOSE}'
    assert validate_spoiler_tokens(body) == f'{PIPE_SPOILER_MARK}secret{PIPE_SPOILER_MARK}'


def test_validate_spoiler_tokens_accepts_sequential_pipe_blocks() -> None:
    body = '||a|| and ||b||'
    assert validate_spoiler_tokens(body) == body


def test_validate_spoiler_tokens_canonicalizes_mixed_sequential() -> None:
    body = f'{SPOILER_OPEN}a{SPOILER_CLOSE} then ||b||'
    assert validate_spoiler_tokens(body) == '||a|| then ||b||'


def test_validate_spoiler_tokens_rejects_unclosed_block() -> None:
    with pytest.raises(SpoilerTokenValidationError, match='unclosed'):
        validate_spoiler_tokens(f'{SPOILER_OPEN}secret')


def test_validate_spoiler_tokens_rejects_unclosed_pipe() -> None:
    with pytest.raises(SpoilerTokenValidationError, match='unclosed'):
        validate_spoiler_tokens('||secret')


def test_validate_spoiler_tokens_rejects_unmatched_close() -> None:
    with pytest.raises(SpoilerTokenValidationError, match='unmatched'):
        validate_spoiler_tokens(f'secret{SPOILER_CLOSE}')


def test_validate_spoiler_tokens_rejects_nested_blocks() -> None:
    nested = f'{SPOILER_OPEN}outer {SPOILER_OPEN}inner{SPOILER_CLOSE}{SPOILER_CLOSE}'
    with pytest.raises(SpoilerTokenValidationError, match='nested spoiler blocks are not allowed'):
        validate_spoiler_tokens(nested)


def test_validate_spoiler_tokens_rejects_pipe_nested_in_legacy() -> None:
    nested = f'{SPOILER_OPEN}outer ||inner||{SPOILER_CLOSE}'
    with pytest.raises(SpoilerTokenValidationError, match='nested spoiler blocks are not allowed'):
        validate_spoiler_tokens(nested)


def test_validate_spoiler_tokens_rejects_legacy_nested_in_pipe() -> None:
    nested = f'||outer {SPOILER_OPEN}inner{SPOILER_CLOSE}||'
    with pytest.raises(SpoilerTokenValidationError, match='nested spoiler blocks are not allowed'):
        validate_spoiler_tokens(nested)


def test_validate_spoiler_tokens_rejects_empty_block() -> None:
    with pytest.raises(SpoilerTokenValidationError, match='empty'):
        validate_spoiler_tokens(f'{SPOILER_OPEN}{SPOILER_CLOSE}')


def test_validate_spoiler_tokens_rejects_empty_pipe() -> None:
    with pytest.raises(SpoilerTokenValidationError, match='empty'):
        validate_spoiler_tokens('||||')
