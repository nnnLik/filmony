from __future__ import annotations

from unittest.mock import patch

import pytest

from services.health.check_backend_readiness import (
    CheckBackendReadinessService,
    DependencyCheck,
    _resolve_redis_url,
)


def test_resolve_redis_url_prefers_celery_broker() -> None:
    with patch('services.health.check_backend_readiness.settings') as settings:
        settings.celery.broker_url = 'redis://broker:6379/0'
        settings.catalog_cache.redis_url = 'redis://catalog:6379/0'
        settings.watch_party.redis_url = ''
        assert _resolve_redis_url() == 'redis://broker:6379/0'


@pytest.mark.asyncio
async def test_postgres_failure_still_evaluates_redis() -> None:
    service = CheckBackendReadinessService.build()
    redis_called = False

    async def fail_postgres() -> DependencyCheck:
        return DependencyCheck(status='error', detail='connection refused')

    async def ok_redis() -> DependencyCheck:
        nonlocal redis_called
        redis_called = True
        return DependencyCheck(status='ok')

    service._check_postgres = fail_postgres  # type: ignore[method-assign]
    service._check_redis = ok_redis  # type: ignore[method-assign]

    result = await service.execute()

    assert redis_called
    assert result.status == 'error'
    assert result.checks['postgres'].status == 'error'
    assert result.checks['postgres'].detail == 'connection refused'
    assert result.checks['redis'].status == 'ok'
