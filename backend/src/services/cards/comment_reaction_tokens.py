from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.reaction_type import ReactionType
from services.profile.validate_inline_mention_tokens import (
    MentionTokenValidationError,
    validate_and_canonicalize_mentions,
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
) -> str:
    """Strip comment body, enforce length, validate ⟦r{id}⟧ and ⟦@slug⟧ mentions."""
    body = text.strip()
    if body == '':
        raise CommentReactionTokenError('comment text must not be empty')
    if len(body) > COMMENT_TEXT_MAX_LEN:
        raise CommentReactionTokenError(f'comment text max length is {COMMENT_TEXT_MAX_LEN}')

    matches = list(REACTION_TOKEN_RE.finditer(body))

    ids: list[int] = []
    for m in matches:
        try:
            rid = int(m.group(1))
        except ValueError as e:
            raise CommentReactionTokenError('invalid reaction token') from e
        if rid < 1:
            raise CommentReactionTokenError('invalid reaction token')
        ids.append(rid)

    if ids:
        rows = (
            (await session.execute(select(ReactionType.id).where(ReactionType.id.in_(ids))))
            .scalars()
            .all()
        )
        found = {int(x) for x in rows}
        if not set(ids).issubset(found):
            raise CommentReactionTokenError('unknown reaction type in comment')

    try:
        body, _mention_ids = await validate_and_canonicalize_mentions(
            body, session, author_user_id=author_user_id
        )
    except MentionTokenValidationError as e:
        raise CommentReactionTokenError(str(e)) from e

    return body
