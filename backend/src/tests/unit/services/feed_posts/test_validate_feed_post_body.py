from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from services.feed_posts.validate_feed_post_body import (
    FEED_POST_BODY_MAX_LEN,
    FeedPostBodyValidationError,
    validate_feed_post_body,
)


def _catalog_session(rows: list[tuple[int, str]]) -> AsyncMock:
    result = MagicMock()
    result.all.return_value = rows
    session = AsyncMock()
    session.execute = AsyncMock(return_value=result)
    return session


@pytest.mark.asyncio
async def test_validate_feed_post_rewrites_legacy_unicode_token() -> None:
    session = _catalog_session([(12, 'gasp')])
    body, mentions = await validate_feed_post_body(
        'вау ⟦r12⟧ класс',
        session,
        author_user_id=uuid4(),
    )
    assert body == 'вау :gasp: класс'
    assert mentions == ()


@pytest.mark.asyncio
async def test_validate_feed_post_rewrites_legacy_ascii_token() -> None:
    session = _catalog_session([(12, 'gasp')])
    body, _mentions = await validate_feed_post_body(
        '[[r12]]',
        session,
        author_user_id=uuid4(),
    )
    assert body == ':gasp:'


@pytest.mark.asyncio
async def test_validate_feed_post_keeps_unknown_colon_shortcode() -> None:
    session = _catalog_session([(12, 'gasp')])
    body, _mentions = await validate_feed_post_body(
        'hello :foo: there',
        session,
        author_user_id=uuid4(),
    )
    assert body == 'hello :foo: there'


@pytest.mark.asyncio
async def test_validate_feed_post_unknown_legacy_id_errors() -> None:
    session = _catalog_session([(12, 'gasp')])
    with pytest.raises(FeedPostBodyValidationError, match='unknown reaction type in body'):
        await validate_feed_post_body(
            '⟦r99⟧',
            session,
            author_user_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_validate_feed_post_skips_catalog_load_without_markers() -> None:
    session = AsyncMock()
    session.execute = AsyncMock()
    body, _mentions = await validate_feed_post_body(
        'plain post',
        session,
        author_user_id=uuid4(),
    )
    assert body == 'plain post'
    session.execute.assert_not_called()


@pytest.mark.asyncio
async def test_validate_feed_post_rechecks_max_length_after_rewrite() -> None:
    shortcode = 'g' * 32
    session = _catalog_session([(12, shortcode)])
    prefix = 'x' * (FEED_POST_BODY_MAX_LEN - 5)
    body = f'{prefix}⟦r12⟧'
    assert len(body) == FEED_POST_BODY_MAX_LEN
    with pytest.raises(
        FeedPostBodyValidationError,
        match=f'body max length is {FEED_POST_BODY_MAX_LEN}',
    ):
        await validate_feed_post_body(
            body,
            session,
            author_user_id=uuid4(),
        )
