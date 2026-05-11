"""Shared validation for ⟦@profile_slug⟧ mentions (followers only)."""

from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from models.user_subscription import UserSubscription

_MENTION_TOKEN_RE = re.compile(r'⟦@([^⟧]+)⟧')
_SLUG_IN_MENTION_RE = re.compile(r'^[A-Za-z0-9_-]{1,32}$')


class MentionTokenValidationError(Exception):
    """Invalid mention token or mention not allowed for this author."""


async def validate_and_canonicalize_mentions(
    body: str,
    session: AsyncSession,
    *,
    author_user_id: UUID,
) -> tuple[str, tuple[UUID, ...]]:
    """Return body with canonical ⟦@slug⟧ tokens and deduplicated mentioned user ids."""
    mention_hits = list(_MENTION_TOKEN_RE.finditer(body))
    normalized_slugs: list[str] = []
    for m in mention_hits:
        raw = m.group(1).strip()
        if raw == '' or not _SLUG_IN_MENTION_RE.fullmatch(raw):
            raise MentionTokenValidationError('invalid mention token')
        normalized_slugs.append(raw.lower())

    if not normalized_slugs:
        return body, ()

    unique_slugs = list(set(normalized_slugs))
    user_rows = (
        (
            await session.execute(
                select(User.id, User.profile_slug).where(
                    func.lower(User.profile_slug).in_(unique_slugs)
                )
            )
        )
        .all()
    )
    by_lower: dict[str, tuple[UUID, str]] = {}
    for row in user_rows:
        uid, slug = row[0], row[1]
        by_lower[str(slug).lower()] = (uid, str(slug))

    for slug in unique_slugs:
        if slug not in by_lower:
            raise MentionTokenValidationError('unknown profile in mention')

    mentioned_user_ids = {by_lower[s][0] for s in normalized_slugs}
    if author_user_id in mentioned_user_ids:
        raise MentionTokenValidationError('cannot mention yourself')

    sub_rows = (
        (
            await session.execute(
                select(UserSubscription.following_user_id).where(
                    UserSubscription.follower_user_id == author_user_id,
                    UserSubscription.following_user_id.in_(mentioned_user_ids),
                )
            )
        )
        .scalars()
        .all()
    )
    allowed = set(sub_rows)
    if not mentioned_user_ids.issubset(allowed):
        raise MentionTokenValidationError('mentions are limited to users you follow')

    def _mention_repl(match: re.Match[str]) -> str:
        key = match.group(1).strip().lower()
        _uid, canonical = by_lower[key]
        return f'⟦@{canonical.lower()}⟧'

    body = _MENTION_TOKEN_RE.sub(_mention_repl, body)
    ordered_ids = tuple(dict.fromkeys(by_lower[s][0] for s in normalized_slugs))
    return body, ordered_ids
