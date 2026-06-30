from __future__ import annotations

from uuid import UUID

from models.card_enums import CardCompany


def normalize_watch_with_user_ids(
    *,
    actor_user_id: UUID,
    company: CardCompany,
    watch_with_user_ids: list[UUID] | None,
    watch_with_user_id: UUID | None,
) -> list[UUID]:
    """Dedupe partner ids, drop actor; clear only when company is alone and none provided."""
    if company == CardCompany.alone:
        merged: list[UUID] = []
        seen: set[UUID] = set()
        for raw in list(watch_with_user_ids or []):
            if raw in seen or raw == actor_user_id:
                continue
            seen.add(raw)
            merged.append(raw)
        if (
            watch_with_user_id is not None
            and watch_with_user_id not in seen
            and watch_with_user_id != actor_user_id
        ):
            merged.append(watch_with_user_id)
        if not merged:
            return []
        if len(merged) > 20:
            raise ValueError('max 20 watch partners allowed')
        return merged

    merged = []
    seen: set[UUID] = set()
    for raw in list(watch_with_user_ids or []):
        if raw in seen or raw == actor_user_id:
            continue
        seen.add(raw)
        merged.append(raw)
    if (
        watch_with_user_id is not None
        and watch_with_user_id not in seen
        and watch_with_user_id != actor_user_id
    ):
        merged.append(watch_with_user_id)

    if len(merged) > 20:
        raise ValueError('max 20 watch partners allowed')
    return merged


def primary_watch_with_user_id(partner_ids: list[UUID]) -> UUID | None:
    return partner_ids[0] if partner_ids else None


def watch_with_user_ids_as_json(partner_ids: list[UUID]) -> list[str]:
    return [str(uid) for uid in partner_ids]
