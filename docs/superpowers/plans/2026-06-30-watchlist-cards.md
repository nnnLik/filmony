# Watchlist Cards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a unified watchlist entry model for Card + ProviderMeta across providers, migrate legacy watchlist data, create feed posts on watch-later, and send watch-with invitations with Telegram push.

**Architecture:** Introduce a new `WatchlistEntry` data model and DAO for provider-aware cards. Route watchlist create/update through a single `CreateWatchlistEntryService` that handles feed post creation and optional watch-with invites (separate entry + Telegram push). Migrate legacy `user_watchlist_film` records into the new table, then remove legacy models and endpoints.

**Tech Stack:** FastAPI, SQLAlchemy/Alembic migrations, pytest + pytest-asyncio, Telegram push service, Docker-backed test commands.

---

## File Structure Map

### Backend
- Create: `backend/src/app/models/watchlist_entry.py` — SQLAlchemy model for unified watchlist entries.
- Create: `backend/src/app/daos/watchlist_entry_dao.py` — DAO for CRUD and lookup by user/card.
- Create: `backend/src/app/schemas/watchlist_entry.py` — request/response schemas for provider-aware payloads.
- Create: `backend/src/app/services/create_watchlist_entry_service.py` — orchestrates creation, feed post, and watch-with invite.
- Create: `backend/src/app/services/feed_posts/create_watchlist_feed_post_service.py` — feed post creation for watch-later.
- Create: `backend/src/app/services/send_watchlist_invite_notification_service.py` — Telegram push for invites.
- Modify: `backend/src/app/api/routes/watchlist.py` — new create/update endpoints using provider-aware payloads.
- Modify: `backend/src/app/api/routes/__init__.py` — register updated routes if needed.
- Create: `backend/src/migrations/versions/20260630_01_watchlist_entries.py` — new table for watchlist entries.
- Create: `backend/src/migrations/versions/20260630_02_migrate_watchlist_films.py` — data migration from legacy table.
- Delete: `backend/src/app/models/user_watchlist_film.py` — legacy model.
- Delete: `backend/src/app/daos/user_watchlist_film_dao.py` — legacy DAO.
- Modify: `backend/src/app/api/routes/legacy_watchlist.py` — remove legacy endpoints (or delete file if only legacy).

### Backend Tests
- Create: `backend/src/tests/services/test_create_watchlist_entry_service.py`
- Create: `backend/src/tests/services/test_create_watchlist_feed_post_service.py`
- Create: `backend/src/tests/services/test_send_watchlist_invite_notification_service.py`
- Create: `backend/src/tests/api/test_watchlist_routes.py`
- Create: `backend/src/tests/migrations/test_watchlist_migration.py`

### Delivery Artifacts
- Create: `.cursor/active/watchlist-cards/plan.md`
- Create: `.cursor/active/watchlist-cards/progress.md`
- Create: `.cursor/active/watchlist-cards/result.md`
- Create: `docs/features/watchlist-cards.md`
- Modify: `.cursor/memory/logs/action-log.md`
- Create: `.cursor/memory/logs/2026-06-30-watchlist-cards.md`

---

### Task 1: Add WatchlistEntry Model + DAO + Migration

**Files:**
- Create: `backend/src/app/models/watchlist_entry.py`
- Create: `backend/src/app/daos/watchlist_entry_dao.py`
- Create: `backend/src/migrations/versions/20260630_01_watchlist_entries.py`
- Test: `backend/src/tests/services/test_create_watchlist_entry_service.py`

- [ ] **Step 1: Write the failing test**

```python
import datetime as dt

from backend.src.app.services.create_watchlist_entry_service import (
    CreateWatchlistEntryService,
)


def test_create_watchlist_entry_persists_provider_meta(db_session, user_factory):
    user = user_factory()
    payload = {
        "card_id": "kp:12345",
        "provider_meta": {"provider": "kinopoisk", "data": {"kp_id": 12345}},
        "watch_tag": "watch_later",
        "watch_with_user_id": None,
    }

    service = CreateWatchlistEntryService.build()
    result = service.execute(
        actor_user_id=user.id,
        card_id=payload["card_id"],
        provider_meta=payload["provider_meta"],
        watch_tag=payload["watch_tag"],
        watch_with_user_id=None,
        created_at=dt.datetime(2026, 6, 30, 9, 0, 0, tzinfo=dt.timezone.utc),
    )

    entry = result.actor_entry
    assert entry.user_id == user.id
    assert entry.card_id == "kp:12345"
    assert entry.provider_meta["provider"] == "kinopoisk"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `make backend-test-one target=backend/src/tests/services/test_create_watchlist_entry_service.py::test_create_watchlist_entry_persists_provider_meta`  
Expected: FAIL with `ModuleNotFoundError` for `CreateWatchlistEntryService` or missing table.

- [ ] **Step 3: Write minimal implementation**

```python
# backend/src/app/models/watchlist_entry.py
from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, DateTime, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from backend.src.app.db import Base


class WatchlistEntry(Base):
    __tablename__ = "watchlist_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    card_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    provider_meta: Mapped[dict] = mapped_column(JSON, nullable=False)
    watch_tag: Mapped[str] = mapped_column(String(32), nullable=False)
    watch_with_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=dt.datetime.utcnow,
    )
```

```python
# backend/src/app/daos/watchlist_entry_dao.py
from __future__ import annotations

from backend.src.app.models.watchlist_entry import WatchlistEntry


class WatchlistEntryDAO:
    def get_by_id(self, *, session, entry_id: int) -> WatchlistEntry | None:
        return session.query(WatchlistEntry).filter(WatchlistEntry.id == entry_id).one_or_none()

    def update(self, *, session, entry: WatchlistEntry, watch_tag: str) -> WatchlistEntry:
        entry.watch_tag = watch_tag
        session.flush()
        return entry

    def create(
        self,
        *,
        session,
        user_id: int,
        card_id: str,
        provider_meta: dict,
        watch_tag: str,
        watch_with_user_id: int | None,
        created_at,
    ) -> WatchlistEntry:
        entry = WatchlistEntry(
            user_id=user_id,
            card_id=card_id,
            provider_meta=provider_meta,
            watch_tag=watch_tag,
            watch_with_user_id=watch_with_user_id,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add(entry)
        session.flush()
        return entry
```

```python
# backend/src/migrations/versions/20260630_01_watchlist_entries.py
from alembic import op
import sqlalchemy as sa

revision = "20260630_01_watchlist_entries"
down_revision = "20260629_02_watchlist_prep"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "watchlist_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("card_id", sa.String(length=128), nullable=False),
        sa.Column("provider_meta", sa.JSON(), nullable=False),
        sa.Column("watch_tag", sa.String(length=32), nullable=False),
        sa.Column("watch_with_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_watchlist_entries_user_id", "watchlist_entries", ["user_id"])
    op.create_index("ix_watchlist_entries_card_id", "watchlist_entries", ["card_id"])


def downgrade() -> None:
    op.drop_index("ix_watchlist_entries_card_id", table_name="watchlist_entries")
    op.drop_index("ix_watchlist_entries_user_id", table_name="watchlist_entries")
    op.drop_table("watchlist_entries")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `make backend-test-one target=backend/src/tests/services/test_create_watchlist_entry_service.py::test_create_watchlist_entry_persists_provider_meta`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/app/models/watchlist_entry.py \
  backend/src/app/daos/watchlist_entry_dao.py \
  backend/src/migrations/versions/20260630_01_watchlist_entries.py \
  backend/src/tests/services/test_create_watchlist_entry_service.py
git commit -m "feat: add watchlist entry model and migration"
```

---

### Task 2: Create Watchlist Entry Service (Feed + Invite)

**Files:**
- Create: `backend/src/app/services/create_watchlist_entry_service.py`
- Modify: `backend/src/app/services/__init__.py`
- Test: `backend/src/tests/services/test_create_watchlist_entry_service.py`

- [ ] **Step 1: Write the failing test**

```python
import datetime as dt

from backend.src.app.services.create_watchlist_entry_service import (
    CreateWatchlistEntryService,
)


def test_create_watchlist_entry_creates_invited_entry(db_session, user_factory):
    actor = user_factory()
    invited = user_factory()
    service = CreateWatchlistEntryService.build()

    result = service.execute(
        actor_user_id=actor.id,
        card_id="rawg:elden-ring",
        provider_meta={"provider": "rawg", "data": {"slug": "elden-ring"}},
        watch_tag="watch_later",
        watch_with_user_id=invited.id,
        created_at=dt.datetime(2026, 6, 30, 9, 0, 0, tzinfo=dt.timezone.utc),
    )

    assert result.actor_entry.user_id == actor.id
    assert result.invited_entry is not None
    assert result.invited_entry.user_id == invited.id
    assert result.invited_entry.card_id == "rawg:elden-ring"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `make backend-test-one target=backend/src/tests/services/test_create_watchlist_entry_service.py::test_create_watchlist_entry_creates_invited_entry`  
Expected: FAIL with missing service or return shape.

- [ ] **Step 3: Write minimal implementation**

```python
# backend/src/app/services/create_watchlist_entry_service.py
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self

from backend.src.app.daos.watchlist_entry_dao import WatchlistEntryDAO
from backend.src.app.services.send_watchlist_invite_notification_service import (
    SendWatchlistInviteNotificationService,
)
from backend.src.app.services.feed_posts.create_watchlist_feed_post_service import (
    CreateWatchlistFeedPostService,
)
from backend.src.app.db import get_session


@dataclass
class CreateWatchlistEntryResult:
    actor_entry: object
    invited_entry: object | None


@dataclass
class CreateWatchlistEntryService:
    """Creates a watchlist entry and, when requested, invites a friend.

    Always creates a feed post for the actor entry and optionally creates
    a second entry for the invited user, sending a Telegram push.
    """

    _watchlist_entry_dao: WatchlistEntryDAO
    _feed_post_service: CreateWatchlistFeedPostService
    _invite_notification_service: SendWatchlistInviteNotificationService

    @classmethod
    def build(cls) -> Self:
        return cls(
            _watchlist_entry_dao=WatchlistEntryDAO(),
            _feed_post_service=CreateWatchlistFeedPostService.build(),
            _invite_notification_service=SendWatchlistInviteNotificationService.build(),
        )

    def execute(
        self,
        *,
        actor_user_id: int,
        card_id: str,
        provider_meta: dict,
        watch_tag: str,
        watch_with_user_id: int | None,
        created_at: dt.datetime,
    ) -> CreateWatchlistEntryResult:
        with get_session() as session:
            actor_entry = self._watchlist_entry_dao.create(
                session=session,
                user_id=actor_user_id,
                card_id=card_id,
                provider_meta=provider_meta,
                watch_tag=watch_tag,
                watch_with_user_id=watch_with_user_id,
                created_at=created_at,
            )

            self._feed_post_service.execute(
                user_id=actor_user_id,
                card_id=card_id,
                provider_meta=provider_meta,
            )

            invited_entry = None
            if watch_with_user_id is not None:
                invited_entry = self._watchlist_entry_dao.create(
                    session=session,
                    user_id=watch_with_user_id,
                    card_id=card_id,
                    provider_meta=provider_meta,
                    watch_tag=watch_tag,
                    watch_with_user_id=actor_user_id,
                    created_at=created_at,
                )
                self._invite_notification_service.execute(
                    actor_user_id=actor_user_id,
                    invited_user_id=watch_with_user_id,
                    card_id=card_id,
                    provider_meta=provider_meta,
                )

        return CreateWatchlistEntryResult(
            actor_entry=actor_entry,
            invited_entry=invited_entry,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `make backend-test-one target=backend/src/tests/services/test_create_watchlist_entry_service.py::test_create_watchlist_entry_creates_invited_entry`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/app/services/create_watchlist_entry_service.py \
  backend/src/app/services/__init__.py \
  backend/src/tests/services/test_create_watchlist_entry_service.py
git commit -m "feat: add watchlist entry creation service"
```

---

### Task 3: Create Feed Post For Watch-Later

**Files:**
- Create: `backend/src/app/services/feed_posts/create_watchlist_feed_post_service.py`
- Test: `backend/src/tests/services/test_create_watchlist_feed_post_service.py`

- [ ] **Step 1: Write the failing test**

```python
from backend.src.app.services.feed_posts.create_watchlist_feed_post_service import (
    CreateWatchlistFeedPostService,
)


def test_watchlist_feed_post_payload(feed_post_client_mock):
    service = CreateWatchlistFeedPostService.build()

    payload = service.execute(
        user_id=7,
        card_id="kp:321",
        provider_meta={"provider": "kinopoisk", "data": {"kp_id": 321}},
    )

    assert payload["user_id"] == 7
    assert payload["card_id"] == "kp:321"
    assert payload["include_rating"] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `make backend-test-one target=backend/src/tests/services/test_create_watchlist_feed_post_service.py::test_watchlist_feed_post_payload`  
Expected: FAIL with missing service.

- [ ] **Step 3: Write minimal implementation**

```python
# backend/src/app/services/feed_posts/create_watchlist_feed_post_service.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from backend.src.app.services.feed_posts.feed_post_service import FeedPostService


@dataclass
class CreateWatchlistFeedPostService:
    """Create a watch-later feed post with limited content scope."""

    _feed_post_service: FeedPostService

    @classmethod
    def build(cls) -> Self:
        return cls(_feed_post_service=FeedPostService.build())

    def execute(self, *, user_id: int, card_id: str, provider_meta: dict) -> dict:
        payload = {
            "user_id": user_id,
            "card_id": card_id,
            "provider_meta": provider_meta,
            "include_title": True,
            "include_description": True,
            "include_poster": True,
            "include_comments": True,
            "include_emotions": True,
            "include_rating": False,
        }
        self._feed_post_service.create_watchlist_post(payload)
        return payload
```

- [ ] **Step 4: Run test to verify it passes**

Run: `make backend-test-one target=backend/src/tests/services/test_create_watchlist_feed_post_service.py::test_watchlist_feed_post_payload`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/app/services/feed_posts/create_watchlist_feed_post_service.py \
  backend/src/tests/services/test_create_watchlist_feed_post_service.py
git commit -m "feat: create watchlist feed post service"
```

---

### Task 4: Send Telegram Push for Watch-With Invites

**Files:**
- Create: `backend/src/app/services/send_watchlist_invite_notification_service.py`
- Test: `backend/src/tests/services/test_send_watchlist_invite_notification_service.py`

- [ ] **Step 1: Write the failing test**

```python
from backend.src.app.services.send_watchlist_invite_notification_service import (
    SendWatchlistInviteNotificationService,
)


def test_invite_notification_payload(push_client_mock):
    service = SendWatchlistInviteNotificationService.build()

    payload = service.execute(
        actor_user_id=11,
        invited_user_id=22,
        card_id="kp:123",
        provider_meta={"provider": "kinopoisk", "data": {"kp_id": 123}},
    )

    assert payload["user_id"] == 22
    assert payload["title"] == "Invite to watch together"
    assert "kp:123" in payload["deeplink"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `make backend-test-one target=backend/src/tests/services/test_send_watchlist_invite_notification_service.py::test_invite_notification_payload`  
Expected: FAIL with missing service.

- [ ] **Step 3: Write minimal implementation**

```python
# backend/src/app/services/send_watchlist_invite_notification_service.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from backend.src.app.services.telegram_push_service import TelegramPushService


@dataclass
class SendWatchlistInviteNotificationService:
    """Send a Telegram push when a watch-with invite is created."""

    _push_service: TelegramPushService

    @classmethod
    def build(cls) -> Self:
        return cls(_push_service=TelegramPushService.build())

    def execute(
        self,
        *,
        actor_user_id: int,
        invited_user_id: int,
        card_id: str,
        provider_meta: dict,
    ) -> dict:
        payload = {
            "user_id": invited_user_id,
            "title": "Invite to watch together",
            "body": "Open the card to see details.",
            "deeplink": f"filmony://watchlist/{card_id}",
            "metadata": {
                "actor_user_id": actor_user_id,
                "provider_meta": provider_meta,
            },
        }
        self._push_service.send(payload)
        return payload
```

- [ ] **Step 4: Run test to verify it passes**

Run: `make backend-test-one target=backend/src/tests/services/test_send_watchlist_invite_notification_service.py::test_invite_notification_payload`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/app/services/send_watchlist_invite_notification_service.py \
  backend/src/tests/services/test_send_watchlist_invite_notification_service.py
git commit -m "feat: send watchlist invite notification"
```

---

### Task 5: Add Watchlist API Routes (Create/Update + ProviderMeta)

**Files:**
- Modify: `backend/src/app/api/routes/watchlist.py`
- Modify: `backend/src/app/schemas/watchlist_entry.py`
- Test: `backend/src/tests/api/test_watchlist_routes.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest


@pytest.mark.asyncio
async def test_create_watchlist_entry_with_provider_meta(async_client, user_factory):
    user = user_factory()
    payload = {
        "card_id": "custom:concert-2026",
        "provider_meta": {"provider": "custom", "data": {"type": "concert"}},
        "watch_tag": "watch_later",
        "watch_with_user_id": None,
    }

    response = await async_client.post("/api/watchlist", json=payload, headers={"X-User-Id": str(user.id)})

    assert response.status_code == 201
    body = response.json()
    assert body["card_id"] == "custom:concert-2026"
    assert body["provider_meta"]["provider"] == "custom"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `make backend-test-one target=backend/src/tests/api/test_watchlist_routes.py::test_create_watchlist_entry_with_provider_meta`  
Expected: FAIL with 404 or schema validation error.

- [ ] **Step 3: Write minimal implementation**

```python
# backend/src/app/schemas/watchlist_entry.py
from enum import Enum

from pydantic import BaseModel


class WatchTag(str, Enum):
    watch_later = "watch_later"


class WatchlistEntryCreate(BaseModel):
    card_id: str
    provider_meta: dict
    watch_tag: WatchTag
    watch_with_user_id: int | None = None


class WatchlistEntryUpdate(BaseModel):
    watch_tag: WatchTag


class WatchlistEntryResponse(BaseModel):
    id: int
    user_id: int
    card_id: str
    provider_meta: dict
    watch_tag: str
    watch_with_user_id: int | None
```

```python
# backend/src/app/api/routes/watchlist.py
import datetime as dt

from fastapi import APIRouter, Depends, status

from backend.src.app.schemas.watchlist_entry import (
    WatchlistEntryCreate,
    WatchlistEntryResponse,
)
from backend.src.app.services.create_watchlist_entry_service import (
    CreateWatchlistEntryService,
)
from backend.src.app.api.deps import get_current_user_id

router = APIRouter()


@router.post("/watchlist", response_model=WatchlistEntryResponse, status_code=status.HTTP_201_CREATED)
def create_watchlist_entry(
    payload: WatchlistEntryCreate,
    user_id: int = Depends(get_current_user_id),
):
    service = CreateWatchlistEntryService.build()
    result = service.execute(
        actor_user_id=user_id,
        card_id=payload.card_id,
        provider_meta=payload.provider_meta,
        watch_tag=payload.watch_tag,
        watch_with_user_id=payload.watch_with_user_id,
        created_at=dt.datetime.now(dt.timezone.utc),
    )
    entry = result.actor_entry
    return WatchlistEntryResponse(
        id=entry.id,
        user_id=entry.user_id,
        card_id=entry.card_id,
        provider_meta=entry.provider_meta,
        watch_tag=entry.watch_tag,
        watch_with_user_id=entry.watch_with_user_id,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `make backend-test-one target=backend/src/tests/api/test_watchlist_routes.py::test_create_watchlist_entry_with_provider_meta`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/app/api/routes/watchlist.py \
  backend/src/app/schemas/watchlist_entry.py \
  backend/src/tests/api/test_watchlist_routes.py
git commit -m "feat: add provider-aware watchlist endpoints"
```

---

### Task 6: Migrate Legacy user_watchlist_film Data + Remove Legacy APIs

**Files:**
- Create: `backend/src/migrations/versions/20260630_02_migrate_watchlist_films.py`
- Delete: `backend/src/app/models/user_watchlist_film.py`
- Delete: `backend/src/app/daos/user_watchlist_film_dao.py`
- Modify: `backend/src/app/api/routes/legacy_watchlist.py`
- Test: `backend/src/tests/migrations/test_watchlist_migration.py`

- [ ] **Step 1: Write the failing test**

```python
def test_legacy_watchlist_migration_creates_entries(migration_runner):
    migration_runner.seed_user_watchlist_film(
        user_id=1,
        film_id=123,
        created_at="2026-06-01T10:00:00Z",
    )

    migration_runner.upgrade("20260630_02_migrate_watchlist_films")

    entries = migration_runner.fetch_watchlist_entries(user_id=1)
    assert len(entries) == 1
    assert entries[0]["card_id"] == "kp:123"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `make backend-test-one target=backend/src/tests/migrations/test_watchlist_migration.py::test_legacy_watchlist_migration_creates_entries`  
Expected: FAIL with missing migration.

- [ ] **Step 3: Write minimal implementation**

```python
# backend/src/migrations/versions/20260630_02_migrate_watchlist_films.py
from alembic import op

revision = "20260630_02_migrate_watchlist_films"
down_revision = "20260630_01_watchlist_entries"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO watchlist_entries (user_id, card_id, provider_meta, watch_tag, watch_with_user_id, created_at, updated_at)
        SELECT
            user_id,
            CONCAT('kp:', film_id) AS card_id,
            jsonb_build_object('provider', 'kinopoisk', 'data', jsonb_build_object('kp_id', film_id)) AS provider_meta,
            'watch_later' AS watch_tag,
            NULL AS watch_with_user_id,
            created_at,
            created_at
        FROM user_watchlist_film
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM watchlist_entries
        WHERE provider_meta ->> 'provider' = 'kinopoisk'
          AND watch_tag = 'watch_later'
        """
    )
```

- [ ] **Step 4: Remove legacy model/DAO and routes**

```bash
rm backend/src/app/models/user_watchlist_film.py
rm backend/src/app/daos/user_watchlist_film_dao.py
rm backend/src/app/api/routes/legacy_watchlist.py
```

- [ ] **Step 5: Run test to verify it passes**

Run: `make backend-test-one target=backend/src/tests/migrations/test_watchlist_migration.py::test_legacy_watchlist_migration_creates_entries`  
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/src/migrations/versions/20260630_02_migrate_watchlist_films.py \
  backend/src/tests/migrations/test_watchlist_migration.py \
  backend/src/app/models/user_watchlist_film.py \
  backend/src/app/daos/user_watchlist_film_dao.py \
  backend/src/app/api/routes/legacy_watchlist.py
git commit -m "feat: migrate legacy watchlist films"
```

---

### Task 7: Remove Legacy Watchlist Routes + Enforce Ownership Updates

**Files:**
- Modify: `backend/src/app/api/routes/watchlist.py`
- Modify: `backend/src/app/schemas/watchlist_entry.py`
- Test: `backend/src/tests/api/test_watchlist_routes.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest


@pytest.mark.asyncio
async def test_user_cannot_edit_other_watchlist_entry(async_client, user_factory, watchlist_entry_factory):
    owner = user_factory()
    other = user_factory()
    entry = watchlist_entry_factory(user_id=owner.id)

    response = await async_client.patch(
        f"/api/watchlist/{entry.id}",
        json={"watch_tag": "watch_later"},
        headers={"X-User-Id": str(other.id)},
    )

    assert response.status_code == 403
```

- [ ] **Step 2: Run test to verify it fails**

Run: `make backend-test-one target=backend/src/tests/api/test_watchlist_routes.py::test_user_cannot_edit_other_watchlist_entry`  
Expected: FAIL with 200 or 404.

- [ ] **Step 3: Write minimal implementation**

```python
# backend/src/app/api/routes/watchlist.py
from fastapi import HTTPException
from backend.src.app.api.deps import get_current_user_id
from backend.src.app.daos.watchlist_entry_dao import WatchlistEntryDAO
from backend.src.app.db import get_session


@router.patch("/watchlist/{entry_id}", response_model=WatchlistEntryResponse)
def update_watchlist_entry(
    entry_id: int,
    payload: WatchlistEntryUpdate,
    user_id: int = Depends(get_current_user_id),
):
    watchlist_entry_dao = WatchlistEntryDAO()
    with get_session() as session:
        entry = watchlist_entry_dao.get_by_id(session=session, entry_id=entry_id)
        if entry is None:
            raise HTTPException(status_code=404, detail="not_found")
        if entry.user_id != user_id:
            raise HTTPException(status_code=403, detail="forbidden")
        entry = watchlist_entry_dao.update(
            session=session,
            entry=entry,
            watch_tag=payload.watch_tag,
        )
        return WatchlistEntryResponse(
            id=entry.id,
            user_id=entry.user_id,
            card_id=entry.card_id,
            provider_meta=entry.provider_meta,
            watch_tag=entry.watch_tag,
            watch_with_user_id=entry.watch_with_user_id,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `make backend-test-one target=backend/src/tests/api/test_watchlist_routes.py::test_user_cannot_edit_other_watchlist_entry`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/app/api/routes/watchlist.py \
  backend/src/app/schemas/watchlist_entry.py \
  backend/src/tests/api/test_watchlist_routes.py
git commit -m "feat: enforce watchlist ownership updates"
```

---

### Task 8: Delivery Artifacts + Memory Log

**Files:**
- Create: `.cursor/active/watchlist-cards/plan.md`
- Create: `.cursor/active/watchlist-cards/progress.md`
- Create: `.cursor/active/watchlist-cards/result.md`
- Create: `docs/features/watchlist-cards.md`
- Modify: `.cursor/memory/logs/action-log.md`
- Create: `.cursor/memory/logs/2026-06-30-watchlist-cards.md`

- [ ] **Step 1: Create plan/progress/result docs**

```markdown
# Watchlist Cards

Status: in_progress

## Plan
- Add watchlist entry model and migration
- Ship create/update API with provider_meta
- Migrate legacy user_watchlist_film
- Send watch-with Telegram invites
```

- [ ] **Step 2: Create feature documentation**

```markdown
# Watchlist Cards

## Summary
- Unified watchlist entries support Card + ProviderMeta for multiple providers.
- Watch-with invites create independent entries plus Telegram push.

## API
- POST `/api/watchlist` accepts provider-aware payload with optional `watch_with_user_id`.
```

- [ ] **Step 3: Append action log entry**

```markdown
## 2026-06-30
- feature: watchlist-cards
  - action: plan
  - summary: Drafted implementation plan for unified watchlist entries and migration.
  - files: docs/superpowers/plans/2026-06-30-watchlist-cards.md
```

- [ ] **Step 4: Commit**

```bash
git add .cursor/active/watchlist-cards/plan.md \
  .cursor/active/watchlist-cards/progress.md \
  .cursor/active/watchlist-cards/result.md \
  docs/features/watchlist-cards.md \
  .cursor/memory/logs/action-log.md \
  .cursor/memory/logs/2026-06-30-watchlist-cards.md
git commit -m "docs: add watchlist cards delivery artifacts"
```

---

## Self-Review Checklist

1. **Spec coverage:** All requirements addressed by Tasks 1–7, including provider-aware Card + ProviderMeta, feed post creation, watch-with invites, independent entries, migration, and legacy removal.
2. **Placeholder scan:** No "TBD"/"TODO" or vague steps remain.
3. **Type consistency:** `watch_tag`, `provider_meta`, and `watch_with_user_id` fields are used consistently in models, services, and API schemas.

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-06-30-watchlist-cards.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration  
**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints  

**Which approach?**
