"""Collection guard: forbid integration-only fixtures under tests/unit/."""

from __future__ import annotations

from pathlib import Path

import pytest

_FORBIDDEN_IN_UNIT = frozenset({'prepare_db', 'async_client'})


def _item_path(item: pytest.Item) -> Path:
    raw = getattr(item, 'path', None)
    if raw is not None:
        return Path(raw)
    fspath = getattr(item, 'fspath', None)
    if fspath is not None:
        return Path(getattr(fspath, 'strpath', str(fspath)))
    return Path(str(item.fspath))


def _is_under_unit_tree(path: Path) -> bool:
    parts = path.parts
    try:
        tests_idx = parts.index('tests')
    except ValueError:
        normalized = str(path).replace('\\', '/')
        return '/unit/' in normalized or normalized.endswith('/unit')
    if tests_idx + 1 < len(parts) and parts[tests_idx + 1] == 'unit':
        return True
    normalized = str(path).replace('\\', '/')
    return '/unit/' in normalized or '\\unit\\' in str(path)


def pytest_collection_modifyitems(
    session: pytest.Session,
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    del session, config
    for item in items:
        if not _is_under_unit_tree(_item_path(item)):
            continue
        for name in item.fixturenames:
            if name in _FORBIDDEN_IN_UNIT:
                raise pytest.UsageError(
                    f'{item.nodeid}: fixture {name!r} is not allowed under tests/unit/ '
                    '(move the test to tests/integration/ or mock persistence).'
                )
