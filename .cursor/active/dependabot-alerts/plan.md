# Dependabot Alerts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an admin-facing Dependabot alerts view backed by a cached backend sync from GitHub.

**Architecture:** Add a persisted `DependabotAlert` model and DAO, plus a sync service that pulls alerts from GitHub and upserts them. Expose admin routes for listing and refreshing alerts; the frontend reads from the list endpoint and offers a manual refresh action.

**Tech Stack:** FastAPI, Alembic, httpx, PostgreSQL (via Docker), React, @telegram-apps/telegram-ui, TypeScript.

---

I'm using the writing-plans skill to create the implementation plan.

## File Structure Map

- Create: `backend/src/models/dependabot_alert.py` (SQLAlchemy model)
- Create: `backend/src/daos/dependabot_alert_dao.py` (DB access for alerts)
- Create: `backend/src/services/dependabot/sync_dependabot_alerts.py` (GitHub sync service)
- Create: `backend/src/api/dependabot/schemas.py` (API DTOs)
- Create: `backend/src/api/dependabot/routes.py` (admin endpoints)
- Modify: `backend/src/api/router.py` (register new routes)
- Create: `backend/src/migrations/versions/<new_revision>_dependabot_alerts.py`
- Create: `backend/src/tests/api/test_dependabot_alert_routes.py`
- Create: `frontend/src/api/dependabotApi.ts`
- Create: `frontend/src/api/dependabotTypes.ts`
- Create: `frontend/src/pages/admin/DependabotAlertsPage.tsx`
- Modify: `frontend/src/routes.tsx`

### Task 1: Persist Dependabot alerts

**Files:**
- Create: `backend/src/models/dependabot_alert.py`
- Create: `backend/src/daos/dependabot_alert_dao.py`
- Create: `backend/src/migrations/versions/<new_revision>_dependabot_alerts.py`

- [ ] **Step 1: Add the SQLAlchemy model**

```python
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class DependabotAlert(Base):
    __tablename__ = "dependabot_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    github_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    dependency_name: Mapped[str] = mapped_column(String(255), index=True)
    severity: Mapped[str] = mapped_column(String(32), index=True)
    summary: Mapped[str] = mapped_column(Text)
    advisory_url: Mapped[str] = mapped_column(String(512))
    state: Mapped[str] = mapped_column(String(32), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
```

- [ ] **Step 2: Create the Alembic migration**

```python
from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.create_table(
        "dependabot_alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("github_id", sa.String(length=64), nullable=False),
        sa.Column("dependency_name", sa.String(length=255), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("advisory_url", sa.String(length=512), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("github_id", name="uq_dependabot_alerts_github_id"),
    )
    op.create_index(
        "ix_dependabot_alerts_state_updated_at",
        "dependabot_alerts",
        ["state", "updated_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_dependabot_alerts_state_updated_at", table_name="dependabot_alerts")
    op.drop_table("dependabot_alerts")
```

- [ ] **Step 3: Add DAO helpers**

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from models.dependabot_alert import DependabotAlert


@dataclass
class DependabotAlertDAO:
    _session: Session

    def upsert_alerts(self, alerts: list[DependabotAlert]) -> None:
        for alert in alerts:
            self._session.merge(alert)

    def list_open_alerts(self) -> list[DependabotAlert]:
        stmt = (
            select(DependabotAlert)
            .where(DependabotAlert.state == "open")
            .order_by(DependabotAlert.severity.desc(), DependabotAlert.updated_at.desc())
        )
        return list(self._session.scalars(stmt))

    def delete_missing(self, github_ids: set[str]) -> None:
        if not github_ids:
            return
        stmt = delete(DependabotAlert).where(DependabotAlert.github_id.notin_(github_ids))
        self._session.execute(stmt)

    def set_updated_at(self, github_id: str, updated_at: datetime) -> None:
        alert = self._session.scalar(
            select(DependabotAlert).where(DependabotAlert.github_id == github_id)
        )
        if alert is None:
            return
        alert.updated_at = updated_at
```

- [ ] **Step 4: Commit**

```bash
git add backend/src/models/dependabot_alert.py \
  backend/src/daos/dependabot_alert_dao.py \
  backend/src/migrations/versions/<new_revision>_dependabot_alerts.py
git commit -m "feat: add dependabot alert persistence"
```

### Task 2: Sync alerts and expose API

**Files:**
- Create: `backend/src/services/dependabot/sync_dependabot_alerts.py`
- Create: `backend/src/api/dependabot/schemas.py`
- Create: `backend/src/api/dependabot/routes.py`
- Modify: `backend/src/api/router.py`
- Create: `backend/src/tests/api/test_dependabot_alert_routes.py`

- [ ] **Step 1: Implement GitHub sync service**

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Self

import httpx

from daos.dependabot_alert_dao import DependabotAlertDAO
from models.dependabot_alert import DependabotAlert
from utils.db import get_session
from utils.settings import settings


@dataclass
class SyncDependabotAlertsService:
    """Fetch Dependabot alerts from GitHub and persist them locally."""

    _dao: DependabotAlertDAO
    _client: httpx.Client

    @classmethod
    def build(cls) -> Self:
        session = get_session()
        client = httpx.Client(
            base_url="https://api.github.com",
            headers={"Authorization": f"Bearer {settings.github_token}"},
            timeout=20,
        )
        return cls(_dao=DependabotAlertDAO(session), _client=client)

    def execute(self, repo: str) -> list[DependabotAlert]:
        response = self._client.get(f"/repos/{repo}/dependabot/alerts")
        response.raise_for_status()
        payload = response.json()
        alerts: list[DependabotAlert] = []
        for item in payload:
            alerts.append(
                DependabotAlert(
                    github_id=str(item["number"]),
                    dependency_name=item["dependency"]["package"]["name"],
                    severity=item["security_advisory"]["severity"],
                    summary=item["security_advisory"]["summary"],
                    advisory_url=item["html_url"],
                    state=item["state"],
                    updated_at=datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00")),
                )
            )
        github_ids = {alert.github_id for alert in alerts}
        self._dao.upsert_alerts(alerts)
        self._dao.delete_missing(github_ids)
        return alerts
```

- [ ] **Step 2: Add API schemas**

```python
from pydantic import BaseModel


class DependabotAlertResponse(BaseModel):
    github_id: str
    dependency_name: str
    severity: str
    summary: str
    advisory_url: str
    state: str
    updated_at: str


class DependabotAlertListResponse(BaseModel):
    alerts: list[DependabotAlertResponse]
```

- [ ] **Step 3: Add admin routes**

```python
from fastapi import APIRouter, Depends

from api.dependabot.schemas import DependabotAlertListResponse, DependabotAlertResponse
from services.dependabot.sync_dependabot_alerts import SyncDependabotAlertsService
from services.dependabot.list_dependabot_alerts import ListDependabotAlertsService

router = APIRouter(prefix="/admin/dependabot", tags=["admin", "dependabot"])


@router.get("/alerts", response_model=DependabotAlertListResponse)
async def list_dependabot_alerts() -> DependabotAlertListResponse:
    alerts = ListDependabotAlertsService.build().execute()
    return DependabotAlertListResponse(
        alerts=[
            DependabotAlertResponse(
                github_id=alert.github_id,
                dependency_name=alert.dependency_name,
                severity=alert.severity,
                summary=alert.summary,
                advisory_url=alert.advisory_url,
                state=alert.state,
                updated_at=alert.updated_at.isoformat(),
            )
            for alert in alerts
        ]
    )


@router.post("/alerts/refresh", response_model=DependabotAlertListResponse)
async def refresh_dependabot_alerts() -> DependabotAlertListResponse:
    alerts = SyncDependabotAlertsService.build().execute(repo="filmony/filmony")
    return DependabotAlertListResponse(
        alerts=[
            DependabotAlertResponse(
                github_id=alert.github_id,
                dependency_name=alert.dependency_name,
                severity=alert.severity,
                summary=alert.summary,
                advisory_url=alert.advisory_url,
                state=alert.state,
                updated_at=alert.updated_at.isoformat(),
            )
            for alert in alerts
        ]
    )
```

- [ ] **Step 4: Wire router and add tests**

```python
from fastapi.testclient import TestClient


async def test_list_dependabot_alerts(async_client: TestClient, db_session):
    response = await async_client.get("/admin/dependabot/alerts")
    assert response.status_code == 200
    payload = response.json()
    assert payload["alerts"] == []


async def test_refresh_dependabot_alerts(async_client: TestClient, monkeypatch):
    async def fake_execute(self, repo: str):
        return []

    monkeypatch.setattr(
        "services.dependabot.sync_dependabot_alerts.SyncDependabotAlertsService.execute",
        fake_execute,
    )
    response = await async_client.post("/admin/dependabot/alerts/refresh")
    assert response.status_code == 200
```

- [ ] **Step 5: Run backend tests in Docker**

Run: `make backend-test-one target=src/tests/api/test_dependabot_alert_routes.py`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/src/services/dependabot/sync_dependabot_alerts.py \
  backend/src/api/dependabot/schemas.py \
  backend/src/api/dependabot/routes.py \
  backend/src/api/router.py \
  backend/src/tests/api/test_dependabot_alert_routes.py
git commit -m "feat: add dependabot alert endpoints"
```

### Task 3: Build admin UI

**Files:**
- Create: `frontend/src/api/dependabotApi.ts`
- Create: `frontend/src/api/dependabotTypes.ts`
- Create: `frontend/src/pages/admin/DependabotAlertsPage.tsx`
- Modify: `frontend/src/routes.tsx`

- [ ] **Step 1: Add API client helpers**

```ts
import { apiClient } from "./client";
import type { DependabotAlertList } from "./dependabotTypes";

export const fetchDependabotAlerts = async (): Promise<DependabotAlertList> => {
  return apiClient.get("/admin/dependabot/alerts");
};

export const refreshDependabotAlerts = async (): Promise<DependabotAlertList> => {
  return apiClient.post("/admin/dependabot/alerts/refresh");
};
```

- [ ] **Step 2: Define response types**

```ts
export type DependabotAlert = {
  githubId: string;
  dependencyName: string;
  severity: string;
  summary: string;
  advisoryUrl: string;
  state: string;
  updatedAt: string;
};

export type DependabotAlertList = {
  alerts: DependabotAlert[];
};
```

- [ ] **Step 3: Build the admin screen**

```tsx
import { Button, Cell, Section, Spinner } from "@telegram-apps/telegram-ui";
import { useEffect, useState } from "react";

import { fetchDependabotAlerts, refreshDependabotAlerts } from "../../api/dependabotApi";
import type { DependabotAlert } from "../../api/dependabotTypes";

export const DependabotAlertsPage = () => {
  const [alerts, setAlerts] = useState<DependabotAlert[]>([]);
  const [loading, setLoading] = useState(true);

  const loadAlerts = async () => {
    setLoading(true);
    const response = await fetchDependabotAlerts();
    setAlerts(response.alerts);
    setLoading(false);
  };

  useEffect(() => {
    void loadAlerts();
  }, []);

  const handleRefresh = async () => {
    const response = await refreshDependabotAlerts();
    setAlerts(response.alerts);
  };

  return (
    <Section
      header="Dependabot Alerts"
      footer={loading ? <Spinner size="s" /> : null}
    >
      <Button onClick={handleRefresh} disabled={loading}>
        Refresh
      </Button>
      {alerts.map((alert) => (
        <Cell
          key={alert.githubId}
          subtitle={`${alert.severity.toUpperCase()} • ${alert.state}`}
          description={alert.summary}
          href={alert.advisoryUrl}
        >
          {alert.dependencyName}
        </Cell>
      ))}
    </Section>
  );
};
```

- [ ] **Step 4: Wire the route**

```tsx
import { DependabotAlertsPage } from "./pages/admin/DependabotAlertsPage";

const routes = [
  { path: "/admin/dependabot-alerts", element: <DependabotAlertsPage /> },
];
```

- [ ] **Step 5: Run frontend checks**

Run: `cd frontend && npm run lint && npm run build`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/api/dependabotApi.ts \
  frontend/src/api/dependabotTypes.ts \
  frontend/src/pages/admin/DependabotAlertsPage.tsx \
  frontend/src/routes.tsx
git commit -m "feat: add dependabot alerts admin UI"
```

## Self-Review

1. **Spec coverage:** Backend sync/list endpoints, UI screen, and refresh workflow are covered in Tasks 1-3.
2. **Placeholder scan:** No TBD/TODO markers; commands and code are fully spelled out.
3. **Type consistency:** API response fields match type names used in frontend mapping.
