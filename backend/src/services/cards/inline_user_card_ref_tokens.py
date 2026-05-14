"""Inline user-card markers in text: ⟦c{user_card_id}⟧ (author's own cards only)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from models.user_card import UserCard

CARD_REF_TOKEN_RE = re.compile(r'⟦c(\d+)⟧')

UNAVAILABLE_CARD_TITLE = 'Карточка недоступна'


class InlineUserCardRefTokenValidationError(Exception):
    """Invalid ⟦c{id}⟧ token or card does not belong to the author."""


@dataclass(frozen=True, slots=True)
class ReferencedInlineUserCardSnippet:
    user_card_id: int
    catalog_title: str
    catalog_release_year: int | None


def ordered_unique_card_ref_ids(body: str) -> tuple[int, ...]:
    """First-appearance order of distinct positive ids from ⟦c{id}⟧ markers."""
    seen: set[int] = set()
    out: list[int] = []
    for m in CARD_REF_TOKEN_RE.finditer(body or ''):
        try:
            cid = int(m.group(1))
        except ValueError:
            continue
        if cid < 1 or cid in seen:
            continue
        seen.add(cid)
        out.append(cid)
    return tuple(out)


async def validate_inline_user_card_refs_for_author(
    body: str,
    session: AsyncSession,
    *,
    author_user_id: UUID,
) -> None:
    """Raises InlineUserCardRefTokenValidationError if any ⟦c{id}⟧ is not an owned card."""
    ids = list(ordered_unique_card_ref_ids(body))
    if not ids:
        return
    rows = (
        await session.execute(select(UserCard.id, UserCard.user_id).where(UserCard.id.in_(ids)))
    ).all()
    by_id: dict[int, UUID] = {int(r[0]): r[1] for r in rows}
    for cid in ids:
        owner = by_id.get(cid)
        if owner is None:
            raise InlineUserCardRefTokenValidationError('unknown user card in inline reference')
        if owner != author_user_id:
            raise InlineUserCardRefTokenValidationError(
                'inline card references are limited to your own cards'
            )


async def batch_resolve_inline_user_card_refs(
    session: AsyncSession,
    requests: list[tuple[UUID, str]],
) -> list[tuple[ReferencedInlineUserCardSnippet, ...]]:
    """For each (author_user_id, text), snippets in first-id appearance order (deduped ids)."""
    if not requests:
        return []
    all_ids: set[int] = set()
    for _uid, text in requests:
        all_ids.update(ordered_unique_card_ref_ids(text))
    if not all_ids:
        return [() for _ in requests]

    rows = (
        await session.execute(
            select(
                UserCard.id,
                UserCard.user_id,
                func.coalesce(Film.title, UserCard.display_title, ''),
                Film.year,
            )
            .outerjoin(Film, Film.id == UserCard.film_id)
            .where(UserCard.id.in_(all_ids))
        )
    ).all()
    by_id: dict[int, tuple[UUID, str, int | None]] = {
        int(r[0]): (r[1], str(r[2]), r[3]) for r in rows
    }

    out: list[tuple[ReferencedInlineUserCardSnippet, ...]] = []
    for author_id, text in requests:
        snippets: list[ReferencedInlineUserCardSnippet] = []
        for cid in ordered_unique_card_ref_ids(text):
            row = by_id.get(cid)
            if row is None or row[0] != author_id:
                snippets.append(
                    ReferencedInlineUserCardSnippet(
                        user_card_id=cid,
                        catalog_title=UNAVAILABLE_CARD_TITLE,
                        catalog_release_year=None,
                    )
                )
            else:
                snippets.append(
                    ReferencedInlineUserCardSnippet(
                        user_card_id=cid,
                        catalog_title=row[1],
                        catalog_release_year=row[2],
                    )
                )
        out.append(tuple(snippets))
    return out
