from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from services.cards.comment_reaction_tokens import (
    COMMENT_TEXT_MAX_LEN,
    CommentReactionTokenError,
    validate_comment_text_with_reaction_tokens,
)


def _catalog_session(rows: list[tuple[int, str]]) -> AsyncMock:
    result = MagicMock()
    result.all.return_value = rows
    session = AsyncMock()
    session.execute = AsyncMock(return_value=result)
    return session


@pytest.mark.asyncio
async def test_validate_comment_rewrites_legacy_unicode_token() -> None:
    session = _catalog_session([(12, 'gasp')])
    body, mentions = await validate_comment_text_with_reaction_tokens(
        'вау ⟦r12⟧ класс',
        session,
        author_user_id=uuid4(),
    )
    assert body == 'вау :gasp: класс'
    assert mentions == ()


@pytest.mark.asyncio
async def test_validate_comment_rewrites_legacy_ascii_token() -> None:
    session = _catalog_session([(12, 'gasp')])
    body, _mentions = await validate_comment_text_with_reaction_tokens(
        '[[r12]]',
        session,
        author_user_id=uuid4(),
    )
    assert body == ':gasp:'


@pytest.mark.asyncio
async def test_validate_comment_keeps_unknown_colon_shortcode() -> None:
    session = _catalog_session([(12, 'gasp')])
    body, _mentions = await validate_comment_text_with_reaction_tokens(
        'hello :foo: there',
        session,
        author_user_id=uuid4(),
    )
    assert body == 'hello :foo: there'


@pytest.mark.asyncio
async def test_validate_comment_unknown_legacy_id_errors() -> None:
    session = _catalog_session([(12, 'gasp')])
    with pytest.raises(CommentReactionTokenError, match='unknown reaction type in comment'):
        await validate_comment_text_with_reaction_tokens(
            '⟦r99⟧',
            session,
            author_user_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_validate_comment_skips_catalog_load_without_markers() -> None:
    session = AsyncMock()
    session.execute = AsyncMock()
    body, _mentions = await validate_comment_text_with_reaction_tokens(
        'plain comment',
        session,
        author_user_id=uuid4(),
    )
    assert body == 'plain comment'
    session.execute.assert_not_called()


@pytest.mark.asyncio
async def test_validate_comment_rejects_empty_and_oversize_before_rewrite() -> None:
    session = AsyncMock()
    session.execute = AsyncMock()
    with pytest.raises(CommentReactionTokenError, match='comment text must not be empty'):
        await validate_comment_text_with_reaction_tokens(
            '   ',
            session,
            author_user_id=uuid4(),
        )
    with pytest.raises(
        CommentReactionTokenError,
        match=f'comment text max length is {COMMENT_TEXT_MAX_LEN}',
    ):
        await validate_comment_text_with_reaction_tokens(
            'x' * (COMMENT_TEXT_MAX_LEN + 1),
            session,
            author_user_id=uuid4(),
        )
    session.execute.assert_not_called()


@pytest.mark.asyncio
async def test_validate_comment_rechecks_max_length_after_rewrite() -> None:
    shortcode = 'g' * 32
    session = _catalog_session([(12, shortcode)])
    prefix = 'x' * (COMMENT_TEXT_MAX_LEN - 5)
    body = f'{prefix}⟦r12⟧'
    assert len(body) == COMMENT_TEXT_MAX_LEN
    with pytest.raises(
        CommentReactionTokenError,
        match=f'comment text max length is {COMMENT_TEXT_MAX_LEN}',
    ):
        await validate_comment_text_with_reaction_tokens(
            body,
            session,
            author_user_id=uuid4(),
        )
