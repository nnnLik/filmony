"""Resolve ⟦@profile_slug⟧ tokens in comment/post bodies to viewer-safe display rows."""

from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User

_MENTION_TOKEN_RE = re.compile(r'⟦@([^⟧]+)⟧')


def mention_chip_display_label(
    *,
    profile_slug_lower: str,
    username: str | None,
    display_name: str | None,
    first_name: str | None,
    last_name: str | None,
) -> str:
    """Same priority as frontend `mentionChipLabelFromRow` (without row object)."""
    dn = (display_name or '').strip()
    if dn:
        return dn
    fl = ' '.join(x for x in [(first_name or '').strip(), (last_name or '').strip()] if x)
    if fl:
        return fl
    u = (username or '').strip()
    if u:
        return u[1:] if u.startswith('@') else u
    return profile_slug_lower


@dataclass(frozen=True, slots=True)
class ReferencedMentionSnippet:
    """Facts for rendering @… chips (slug key is lowercased, matches stored tokens)."""

    user_id: UUID
    profile_slug: str
    display_label: str
    username: str | None
    display_name: str | None
    first_name: str | None
    last_name: str | None


def ordered_unique_mention_slugs(body: str) -> tuple[str, ...]:
    """First-appearance order of distinct mention slugs (lowercased)."""
    seen: set[str] = set()
    out: list[str] = []
    for m in _MENTION_TOKEN_RE.finditer(body or ''):
        raw = m.group(1).strip().lower()
        if raw == '' or raw in seen:
            continue
        seen.add(raw)
        out.append(raw)
    return tuple(out)


async def batch_resolve_inline_mentions(
    session: AsyncSession,
    texts: list[str],
) -> list[tuple[ReferencedMentionSnippet, ...]]:
    """For each body text, snippets in first-slug appearance order (deduped per body)."""
    if not texts:
        return []
    slug_orders = [ordered_unique_mention_slugs(t) for t in texts]
    all_slugs: set[str] = set()
    for order in slug_orders:
        all_slugs.update(order)
    if not all_slugs:
        return [() for _ in texts]

    slug_list = list(all_slugs)
    rows = (
        await session.execute(
            select(
                User.id,
                User.profile_slug,
                User.username,
                User.display_name,
                User.first_name,
                User.last_name,
            ).where(func.lower(User.profile_slug).in_(slug_list))
        )
    ).all()

    by_lower: dict[str, ReferencedMentionSnippet] = {}
    for uid, slug, username, display_name, first_name, last_name in rows:
        key = str(slug).lower()
        by_lower[key] = ReferencedMentionSnippet(
            user_id=uid,
            profile_slug=key,
            display_label=mention_chip_display_label(
                profile_slug_lower=key,
                username=username,
                display_name=display_name,
                first_name=first_name,
                last_name=last_name,
            ),
            username=username,
            display_name=display_name,
            first_name=first_name,
            last_name=last_name,
        )

    out: list[tuple[ReferencedMentionSnippet, ...]] = []
    for order in slug_orders:
        snippets: list[ReferencedMentionSnippet] = []
        for slug in order:
            row = by_lower.get(slug)
            if row is not None:
                snippets.append(row)
        out.append(tuple(snippets))
    return out
