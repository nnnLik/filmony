from __future__ import annotations

import datetime as dt
import secrets
from dataclasses import dataclass
from uuid import UUID

from conf import settings
from models.user import User


def expected_playback_ms(state: dict) -> int:
    """Extrapolates playback position from stored anchor and playing flag."""
    position_ms = int(state.get('position_ms', 0))
    playing = bool(state.get('playing', False))
    if not playing:
        return max(0, position_ms)
    updated_raw = state.get('updated_at') or state.get('position_at')
    if not updated_raw:
        return max(0, position_ms)
    try:
        updated_at = dt.datetime.fromisoformat(str(updated_raw).replace('Z', '+00:00'))
    except ValueError:
        return max(0, position_ms)
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=dt.UTC)
    else:
        updated_at = updated_at.astimezone(dt.UTC)
    elapsed_ms = max(0, int((dt.datetime.now(dt.UTC) - updated_at).total_seconds() * 1000))
    return max(0, position_ms + elapsed_ms)


def build_initial_playback_state(*, host_user_id: UUID) -> dict:
    now = dt.datetime.now(dt.UTC).isoformat()
    return {
        'playing': False,
        'position_ms': 0,
        'updated_at': now,
        'host_user_id': str(host_user_id),
        'version': 0,
    }


def build_invite_url(invite_slug: str) -> str:
    base = settings.watch_party.public_app_base_url.rstrip('/')
    return f'{base}/watch-party/{invite_slug}'


def format_user_display_name(user: User) -> str:
    if user.display_name and user.display_name.strip():
        return user.display_name.strip()
    parts = [user.first_name or '', user.last_name or '']
    joined = ' '.join(part for part in parts if part).strip()
    if joined:
        return joined
    return user.profile_slug or 'Пользователь'


def generate_invite_slug() -> str:
    return secrets.token_urlsafe(16)
