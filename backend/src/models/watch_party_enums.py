from __future__ import annotations

from enum import StrEnum


class WatchPartyStatus(StrEnum):
    active = 'active'
    ended = 'ended'


class WatchPartyMemberRole(StrEnum):
    host = 'host'
    guest = 'guest'


class WatchPartyMemberStatus(StrEnum):
    active = 'active'
    away = 'away'
    left = 'left'
