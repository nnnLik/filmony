from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from redis.asyncio import Redis
from sqlalchemy import text

from conf import settings
from core.database import get_session_factory


@dataclass(frozen=True, slots=True)
class DependencyCheck:
    status: str
    detail: str | None = None


@dataclass(frozen=True, slots=True)
class ReadinessResult:
    status: str
    checks: dict[str, DependencyCheck]

    @property
    def is_ready(self) -> bool:
        return self.status == 'ok'


def _resolve_redis_url() -> str | None:
    broker = settings.celery.broker_url.strip()
    if broker.startswith(('redis://', 'rediss://')):
        return broker
    catalog = (settings.catalog_cache.redis_url or '').strip()
    if catalog:
        return catalog
    watch_party = (settings.watch_party.redis_url or '').strip()
    if watch_party:
        return watch_party
    return None


@dataclass
class CheckBackendReadinessService:
    """Verifies Postgres and Redis connectivity for orchestrator readiness probes.

    Load balancers and deploy pipelines use readiness to decide whether this
    process can accept traffic; a failing check keeps the instance out of rotation
    until dependencies recover without restarting the process.
    """

    @classmethod
    def build(cls) -> Self:
        return cls()

    async def execute(self) -> ReadinessResult:
        postgres = await self._check_postgres()
        redis = await self._check_redis()
        checks = {
            'postgres': postgres,
            'redis': redis,
        }
        status = 'ok' if all(check.status == 'ok' for check in checks.values()) else 'error'
        return ReadinessResult(status=status, checks=checks)

    async def _check_postgres(self) -> DependencyCheck:
        try:
            session_factory = get_session_factory()
            async with session_factory() as session:
                await session.execute(text('SELECT 1'))
            return DependencyCheck(status='ok')
        except Exception as exc:
            return DependencyCheck(status='error', detail=str(exc))

    async def _check_redis(self) -> DependencyCheck:
        url = _resolve_redis_url()
        if url is None:
            return DependencyCheck(status='error', detail='redis_url_not_configured')
        client = Redis.from_url(
            url,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        try:
            await client.ping()
            return DependencyCheck(status='ok')
        except Exception as exc:
            return DependencyCheck(status='error', detail=str(exc))
        finally:
            await client.aclose()
