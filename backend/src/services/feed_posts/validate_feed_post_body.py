from __future__ import annotations

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
from services.text.reaction_shortcodes import (
    UnknownReactionTokenError,
    rewrite_reaction_tokens,
)
from services.text.spoiler_tokens import (
    SpoilerTokenValidationError,
    validate_spoiler_tokens,
)

# High safety cap for DoS protection; no product-facing character limit.
FEED_POST_BODY_MAX_LEN = 100_000


class FeedPostBodyValidationError(Exception):
    pass


async def validate_feed_post_body(
    text: str, session: AsyncSession, *, author_user_id: UUID
) -> tuple[str, tuple[UUID, ...]]:
    """Strip body, max length; canonicalize reaction tokens; validate card refs and mentions.

    Returns canonical body and deduplicated mentioned user ids (for notifications).
    """
    body = text.strip()
    if body == '':
        raise FeedPostBodyValidationError('body must not be empty')
    if len(body) > FEED_POST_BODY_MAX_LEN:
        raise FeedPostBodyValidationError(f'body max length is {FEED_POST_BODY_MAX_LEN}')

    if ':' in body or '⟦r' in body or '[[r' in body:
        rows = (await session.execute(select(ReactionType.id, ReactionType.shortcode))).all()
        id_to_shortcode = {int(row_id): str(shortcode) for row_id, shortcode in rows}
        known_shortcodes = set(id_to_shortcode.values())
        try:
            body = rewrite_reaction_tokens(
                body,
                id_to_shortcode=id_to_shortcode,
                known_shortcodes=known_shortcodes,
            )
        except UnknownReactionTokenError as e:
            raise FeedPostBodyValidationError('unknown reaction type in body') from e
        if len(body) > FEED_POST_BODY_MAX_LEN:
            raise FeedPostBodyValidationError(f'body max length is {FEED_POST_BODY_MAX_LEN}')

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

    try:
        body = validate_spoiler_tokens(body)
    except SpoilerTokenValidationError as e:
        raise FeedPostBodyValidationError(str(e)) from e

    return body, mention_ids
