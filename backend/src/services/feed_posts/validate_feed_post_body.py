from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.reaction_type import ReactionType
from services.cards.inline_user_card_ref_tokens import (
    InlineUserCardRefTokenValidationError,
    validate_inline_user_card_refs_for_author,
)
from services.profile.validate_inline_mention_tokens import (
    MentionTokenValidationError,
    validate_and_canonicalize_mentions,
)

FEED_POST_BODY_MAX_LEN = 2000
_REACTION_TOKEN_RE = re.compile(r'⟦r(\d+)⟧')


class FeedPostBodyValidationError(Exception):
    pass


async def validate_feed_post_body(
    text: str, session: AsyncSession, *, author_user_id: UUID
) -> tuple[str, tuple[UUID, ...]]:
    """Strip body, max length; validate ⟦r{id}⟧, ⟦c{card_id}⟧ (own cards), ⟦@slug⟧ mentions.

    Returns canonical body and deduplicated mentioned user ids (for notifications).
    """
    body = text.strip()
    if body == '':
        raise FeedPostBodyValidationError('body must not be empty')
    if len(body) > FEED_POST_BODY_MAX_LEN:
        raise FeedPostBodyValidationError(f'body max length is {FEED_POST_BODY_MAX_LEN}')

    matches = list(_REACTION_TOKEN_RE.finditer(body))
    ids: list[int] = []
    for m in matches:
        try:
            rid = int(m.group(1))
        except ValueError as e:
            raise FeedPostBodyValidationError('invalid reaction token') from e
        if rid < 1:
            raise FeedPostBodyValidationError('invalid reaction token')
        ids.append(rid)

    if ids:
        rows = (
            (await session.execute(select(ReactionType.id).where(ReactionType.id.in_(ids))))
            .scalars()
            .all()
        )
        found = {int(x) for x in rows}
        if not set(ids).issubset(found):
            raise FeedPostBodyValidationError('unknown reaction type in body')

    try:
        await validate_inline_user_card_refs_for_author(
            body, session, author_user_id=author_user_id
        )
    except InlineUserCardRefTokenValidationError as e:
        raise FeedPostBodyValidationError(str(e)) from e

    try:
        body, mention_ids = await validate_and_canonicalize_mentions(
            body, session, author_user_id=author_user_id
        )
    except MentionTokenValidationError as e:
        raise FeedPostBodyValidationError(str(e)) from e

    return body, mention_ids
