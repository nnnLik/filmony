#!/usr/bin/env python3
"""Upload `emoji/*/`-pack images to RustFS (S3 API) under `reactions/<category>/<file>`.

Из **корня репозитория**:

  make sync-reactions-rustfs

RustFS и upsert строк в Postgres (через `make sync-reactions-rustfs WITH_DB=1`; Makefile после `source vars/.env.development` заменит в `DATABASE_URL` хост `filmony-postgres:5432` на **127.0.0.1:55432** для запуска с хоста):

  make sync-reactions-rustfs WITH_DB=1

Без Makefile передайте **достигабельный с хоста** `DATABASE_URL` и флаг **`--sync-db`**.
Строку вида **`postgresql+asyncpg://`** (как для SQLAlchemy) скрипт приведёт к виду для ``asyncpg.connect``.

Перед первым запуском: ``make start`` (RustFS на хост-порту **7900**, Postgres проброшен на **55432**).
"""

from __future__ import annotations

import argparse
import asyncio
import mimetypes
import os
import sys
from pathlib import Path


def label_from_filename(filename: str) -> str:
    stem = Path(filename).stem.replace('_', ' ').replace('-', ' ')
    return stem[:118] if stem else Path(filename).name[:118]


def postgres_dsn_for_native_asyncpg(raw: str) -> str:
    """SQLAlchemy/async URL uses ``postgresql+asyncpg://…``; libpq/asyncpg expects ``postgresql://``."""
    u = raw.strip()
    for dialect in ('postgresql+asyncpg://', 'postgres+asyncpg://'):
        if u.startswith(dialect):
            return 'postgresql://' + u[len(dialect) :]
    return u


async def upsert_reaction_rows(
    dsn: str,
    uploaded: list[tuple[str, str, str, int]],
) -> None:
    """Строки: category_slug, file name, asset_key, sort_order."""
    try:
        import asyncpg  # noqa: PLC0415
    except ImportError:
        print('asyncpg не найден: используйте `uv run --project backend`.', file=sys.stderr)
        raise SystemExit(1) from None

    conn = await asyncpg.connect(postgres_dsn_for_native_asyncpg(dsn))
    try:
        sql = """
            INSERT INTO reaction_type (
                label, image_url, sort_order, is_active, category_slug, asset_key
            )
            VALUES ($1, $2, $3, true, $4, $5)
            ON CONFLICT (asset_key) DO UPDATE SET
                label = EXCLUDED.label,
                image_url = EXCLUDED.image_url,
                sort_order = EXCLUDED.sort_order,
                category_slug = EXCLUDED.category_slug,
                is_active = EXCLUDED.is_active
        """
        for category_slug, fname, asset_key, sort_order in uploaded:
            lbl = label_from_filename(fname)
            await conn.execute(sql, lbl, asset_key, sort_order, category_slug, asset_key)
    finally:
        await conn.close()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Sync emoji packs to RustFS and optionally reaction_type.')
    parser.add_argument(
        '--sync-db',
        action='store_true',
        help='После загрузки в S3 сделать upsert в таблицу reaction_type.',
    )
    parser.add_argument(
        '--database-url',
        default=os.environ.get('DATABASE_URL', ''),
        help='Строка подключения Postgres (или env DATABASE_URL). Нужно при --sync-db. '
        'Поддерживается то же DATABASE_URL что и у backend, в т.ч. postgresql+asyncpg://.',
    )
    return parser.parse_args(argv)


def main() -> int:
    argv = sys.argv[1:]
    ns = parse_args(argv)
    try:
        import boto3  # noqa: PLC0415
        from botocore.client import Config  # noqa: PLC0415
        from botocore.exceptions import ClientError  # noqa: PLC0415
    except ImportError:
        print('Install boto3 (e.g. `uv sync --group dev` in backend/).', file=sys.stderr)
        return 1

    if ns.sync_db and not (ns.database_url or '').strip():
        print('--sync-db требует --database-url или переменную DATABASE_URL.', file=sys.stderr)
        return 1

    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / 'backend' / 'src'))
    from const.reaction_packs import REACTION_TAB_ORDER  # noqa: PLC0415

    endpoint = os.environ.get('RUSTFS_ENDPOINT', 'http://127.0.0.1:7900').rstrip('/')
    access = os.environ.get('RUSTFS_ACCESS_KEY')
    secret = os.environ.get('RUSTFS_SECRET_KEY')
    bucket = os.environ.get('RUSTFS_BUCKET')
    if not access or not secret or not bucket:
        print(
            'Set RUSTFS_ACCESS_KEY, RUSTFS_SECRET_KEY, RUSTFS_BUCKET '
            '(and optionally RUSTFS_ENDPOINT).',
            file=sys.stderr,
        )
        return 1

    client = boto3.client(
        's3',
        endpoint_url=endpoint,
        aws_access_key_id=access,
        aws_secret_access_key=secret,
        region_name='us-east-1',
        config=Config(signature_version='s3v4'),
    )
    try:
        client.head_bucket(Bucket=bucket)
    except ClientError:
        client.create_bucket(Bucket=bucket)

    uploaded: list[tuple[str, str, str, int]] = []
    uploaded_count = 0
    emoji_root = repo_root / 'emoji'
    for tab_index, tab in enumerate(REACTION_TAB_ORDER):
        folder = emoji_root / tab.directory
        base_order = tab_index * 10_000
        if not folder.is_dir():
            print(f'skip missing dir: {folder}')
            continue
        sub_index = 0
        for path in sorted(folder.iterdir()):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {'.png', '.gif', '.webp', '.jpg', '.jpeg'}:
                continue
            key = f'reactions/{tab.slug}/{path.name}'
            ctype, _encoding = mimetypes.guess_type(path.name)
            extra: dict[str, str] = {}
            if ctype:
                extra['ContentType'] = ctype
            client.upload_file(str(path), bucket, key, ExtraArgs=extra or {})
            uploaded_count += 1
            sort_order = base_order + sub_index
            sub_index += 1
            uploaded.append((tab.slug, path.name, key, sort_order))
            print(f'OK {key}')

    print(f'done: {uploaded_count} object(s) in RustFS')

    if ns.sync_db:
        asyncio.run(upsert_reaction_rows(ns.database_url.strip(), uploaded))
        print(f'db: upserted {len(uploaded)} reaction_type row(s)')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
