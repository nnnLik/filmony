#!/usr/bin/env python3
"""Upload `emoji/*/`-pack images to RustFS (S3 API) under `reactions/<category>/<file>`.

Из **корня репозитория** (boto3 в `backend` dev-группа):

  make sync-reactions-rustfs

Или вручную:

  RUSTFS_ENDPOINT=http://127.0.0.1:7900 \\
  RUSTFS_ACCESS_KEY=rustfsadmin RUSTFS_SECRET_KEY=rustfsadmin \\
  RUSTFS_BUCKET=filmony-reactions \\
  uv run --project backend python scripts/sync_reactions_to_rustfs.py

Перед этим: ``make start`` чтобы поднялись ``filmony-rustfs`` (порт хоста **7900**) и bucket создался автоматически.
"""

from __future__ import annotations

import mimetypes
import os
import sys
from pathlib import Path


def main() -> int:
    try:
        import boto3  # noqa: PLC0415
        from botocore.client import Config  # noqa: PLC0415
        from botocore.exceptions import ClientError  # noqa: PLC0415
    except ImportError:
        print('Install boto3 (e.g. `uv sync --group dev` in backend/).', file=sys.stderr)
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

    uploaded = 0
    emoji_root = repo_root / 'emoji'
    for tab in REACTION_TAB_ORDER:
        folder = emoji_root / tab.directory
        if not folder.is_dir():
            print(f'skip missing dir: {folder}')
            continue
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
            uploaded += 1
            print(f'OK {key}')

    print(f'done: {uploaded} object(s)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
