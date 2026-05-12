"""One-shot ⟦c⟧ + ⟦@⟧ resolution for comment bodies (same author/text pairing order)."""

from __future__ import annotations

import asyncio
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from services.cards.inline_movie_card_ref_tokens import (
    ReferencedInlineMovieCardSnippet,
    batch_resolve_inline_movie_card_refs,
)
from services.profile.batch_resolve_inline_mentions import (
    ReferencedMentionSnippet,
    batch_resolve_inline_mentions,
)


async def batch_resolve_comment_inline_refs(
    session: AsyncSession,
    author_text_pairs: list[tuple[UUID, str]],
) -> tuple[
    list[tuple[ReferencedInlineMovieCardSnippet, ...]],
    list[tuple[ReferencedMentionSnippet, ...]],
]:
    """Parallel batch for inline card refs and @-mentions; `texts` order matches `pairs`."""
    if not author_text_pairs:
        return [], []
    texts = [t for _, t in author_text_pairs]
    ref_lists, men_lists = await asyncio.gather(
        batch_resolve_inline_movie_card_refs(session, author_text_pairs),
        batch_resolve_inline_mentions(session, texts),
    )
    return ref_lists, men_lists
