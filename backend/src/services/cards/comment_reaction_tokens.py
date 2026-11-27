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
from services.text.reaction_shortcodes import (
    UnknownReactionTokenError,
    rewrite_reaction_tokens,
)
from services.text.spoiler_tokens import (
    SpoilerTokenValidationError,
    validate_spoiler_tokens,
)

COMMENT_TEXT_MAX_LEN = 250
REACTION_TOKEN_RE = re.compile(r'⟦r(\d+)⟧')


class CommentReactionTokenError(ValueError):
    pass


async def validate_comment_text_with_reaction_tokens(
    text: str,
    session: AsyncSession,
    *,
    author_user_id: UUID,
) -> tuple[str, tuple[UUID, ...]]:
    """Strip comment body, validate tokens; returns canonical text and ordered mention user ids."""
    body = text.strip()
    if body == '':
        raise CommentReactionTokenError('comment text must not be empty')
    if len(body) > COMMENT_TEXT_MAX_LEN:
        raise CommentReactionTokenError(f'comment text max length is {COMMENT_TEXT_MAX_LEN}')

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
            raise CommentReactionTokenError('unknown reaction type in comment') from e
        if len(body) > COMMENT_TEXT_MAX_LEN:
            raise CommentReactionTokenError(f'comment text max length is {COMMENT_TEXT_MAX_LEN}')

    try:
        await validate_inline_user_card_refs_for_author(
            body, session, author_user_id=author_user_id
        )
    except InlineUserCardRefTokenValidationError as e:
        raise CommentReactionTokenError(str(e)) from e

    try:
        body, mention_ids = await validate_and_canonicalize_mentions(
            body, session, author_user_id=author_user_id
        )
    except MentionTokenValidationError as e:
        raise CommentReactionTokenError(str(e)) from e

    try:
        body = validate_spoiler_tokens(body)
    except SpoilerTokenValidationError as e:
        raise CommentReactionTokenError(str(e)) from e

    return body, mention_ids
