#!/usr/bin/env python3
"""Upload `emoji/<pack>/` files to RustFS (S3 API) as `reactions/<slug>/<filename>`.

Из **корня репозитория** (нужен `uv` и группа backend с boto3/asyncpg):

  # только объекты в S3 (endpoint по умолчанию для локального compose: 7900)
  uv run --project backend python scripts/upload_reactions_to_rustfs.py

  # то же + upsert строк в `reaction_type` (нужен DATABASE_URL)
  uv run --project backend python scripts/upload_reactions_to_rustfs.py --sync-db

  make sync-reactions-rustfs
  make sync-reactions-rustfs WITH_DB=1

Как создать бакет
-----------------
1. **Этот скрипт** — при первом запуске вызывает `head_bucket`; если бакета нет,
   выполняет `create_bucket` (как в AWS S3 API). Достаточно задать
   `RUSTFS_ACCESS_KEY`, `RUSTFS_SECRET_KEY`, `RUSTFS_BUCKET`, `RUSTFS_ENDPOINT`.

2. **AWS CLI** (с тем же endpoint, что у RustFS), пример для локального dev::

     aws s3 mb "s3://filmony-reactions" \\
       --endpoint-url "http://127.0.0.1:7900" \\
       --region us-east-1

3. **Веб-консоль RustFS** — порт **9001** на том же хосте, что и API (**9000**):
   в UI создать bucket с именем из `RUSTFS_BUCKET` (например `filmony-reactions`).

Прод (homelab): с машины, где доступен RustFS, выставьте
`RUSTFS_ENDPOINT=http(s)://<хост>:9000` и те же ключи, что в `vars/.env` homelab.

На проде **без uv на хосте** — один раз скопируйте скрипт рядом с ``emoji/`` и запустите
**внутри образа backend** (там уже есть Python, boto3, asyncpg и ``PYTHONPATH``)::

  scp scripts/upload_reactions_to_rustfs.py garbata:/opt/filmony/

  cd /opt/filmony   # каталог, где лежит compose.yml и vars/.env.production

  docker compose -f compose.yml run --rm \\
    --entrypoint "" \\
    -v /opt/filmony/upload_reactions_to_rustfs.py:/tmp/upload_reactions_to_rustfs.py:ro \\
    -v /opt/filmony/emoji:/emoji:ro \\
    backend \\
    /opt/pysetup/.venv/bin/python /tmp/upload_reactions_to_rustfs.py --emoji-root /emoji --sync-db

Если без ``--entrypoint ""`` появляется
``can't find '__main__' module in '/tmp/upload_reactions_to_rustfs.py'`` —
у образа ненулевой ENTRYPOINT; ``--entrypoint ""`` его сбрасывает.

Переменные ``RUSTFS_*`` и ``DATABASE_URL`` подтянутся из ``env_file`` сервиса ``backend``.
Если в ``.env`` только ``RUSTFS_INTERNAL_BASE_URL``, скрипт использует его как endpoint для S3.
"""

from __future__ import annotations

import argparse
import asyncio
import mimetypes
import os
import sys
import urllib.parse
from pathlib import Path
from typing import Any


def _default_rustfs_endpoint() -> str:
    for key in ("RUSTFS_ENDPOINT", "RUSTFS_INTERNAL_BASE_URL"):
        raw = (os.environ.get(key) or "").strip().rstrip("/")
        if raw:
            return raw
    return "http://127.0.0.1:7900"


def _ensure_backend_src_on_path() -> None:
    """Импорт из backend/src: в контейнере достаточно PYTHONPATH=/opt/app/src."""
    try:
        import const.reaction_packs as _reaction_packs  # noqa: F401
        return
    except ImportError:
        pass
    roots: list[Path] = []
    env_root = (os.environ.get("FILMONY_REPO_ROOT") or "").strip()
    if env_root:
        roots.append(Path(env_root) / "backend" / "src")
    roots.append(Path(__file__).resolve().parents[1] / "backend" / "src")
    for src in roots:
        if src.is_dir():
            src_str = str(src)
            if src_str not in sys.path:
                sys.path.insert(0, src_str)
            return
    print(
        "Не удалось импортировать backend/src: запустите из образа backend "
        "или задайте FILMONY_REPO_ROOT на корень клона filmony.",
        file=sys.stderr,
    )
    raise SystemExit(1)


def _load_reaction_tab_order() -> tuple[Any, ...]:
    """Импорт каталога вкладок: в контейнере backend достаточно PYTHONPATH=/opt/app/src."""
    _ensure_backend_src_on_path()
    from const.reaction_packs import REACTION_TAB_ORDER

    return REACTION_TAB_ORDER


def _load_reaction_shortcode_helpers() -> tuple[Any, Any, Any]:
    """derive_shortcode_stem, allocate_unique_shortcodes, _first_unused_shortcode."""
    _ensure_backend_src_on_path()
    from services.text.reaction_shortcodes import (
        _first_unused_shortcode,
        allocate_unique_shortcodes,
        derive_shortcode_stem,
    )

    return derive_shortcode_stem, allocate_unique_shortcodes, _first_unused_shortcode


def _allocate_unique_shortcodes_avoiding(
    rows: list[tuple[int, str, str]],
    used: set[str],
    *,
    derive_shortcode_stem: Any,
    allocate_unique_shortcodes: Any,
    first_unused_shortcode: Any,
) -> dict[int, str]:
    """Like allocate_unique_shortcodes, skipping shortcodes already in `used`."""
    if not used:
        return allocate_unique_shortcodes(rows)
    allocated: dict[int, str] = {}
    for row_id, asset_key, category_slug in rows:
        stem = derive_shortcode_stem(asset_key)
        chosen = first_unused_shortcode(stem, category_slug, row_id, used)
        used.add(chosen)
        allocated[row_id] = chosen
    return allocated


def postgres_dsn_for_native_asyncpg(raw: str) -> str:
    """Normalize SQLAlchemy/asyncpg DSN for asyncpg.connect."""
    u = raw.strip()
    for dialect in ("postgresql+asyncpg://", "postgres+asyncpg://"):
        if u.startswith(dialect):
            u = "postgresql://" + u[len(dialect) :]
            break
    parsed = urllib.parse.urlparse(u)
    if parsed.scheme not in {"postgresql", "postgres"}:
        return u
    if not parsed.path or parsed.path == "/":
        return u
    db = parsed.path.lstrip("/")
    new_path = f"/{db}" if db else ""
    if new_path == parsed.path:
        return u
    return urllib.parse.urlunparse(parsed._replace(path=new_path))


async def upsert_reaction_rows(
    dsn: str,
    uploaded: list[tuple[str, str, str]],
    *,
    image_url_template: str | None,
) -> None:
    """Rows: category_slug, filename, asset_key. image_url in DB from template or asset_key."""
    try:
        import asyncpg
    except ImportError:
        print(
            "asyncpg не найден: используйте `uv run --project backend`.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None

    derive_shortcode_stem, allocate_unique_shortcodes, first_unused_shortcode = (
        _load_reaction_shortcode_helpers()
    )

    conn = await asyncpg.connect(postgres_dsn_for_native_asyncpg(dsn))
    try:
        existing_rows = await conn.fetch(
            """
            SELECT id, asset_key, shortcode
            FROM reaction_type
            """
        )
        used: set[str] = {
            str(row["shortcode"]) for row in existing_rows if row["shortcode"]
        }
        existing_by_asset: dict[str, Any] = {
            str(row["asset_key"]): row for row in existing_rows
        }

        new_meta: list[tuple[str, str]] = []
        seen_new: set[str] = set()
        for category_slug, _fname, asset_key in uploaded:
            existing = existing_by_asset.get(asset_key)
            if existing is not None and existing["shortcode"]:
                continue
            if asset_key in seen_new:
                continue
            seen_new.add(asset_key)
            new_meta.append((asset_key, category_slug))

        allocated_by_asset: dict[str, str] = {}
        if new_meta:
            indexed = [
                (index, asset_key, slug)
                for index, (asset_key, slug) in enumerate(new_meta, start=1)
            ]
            allocated = _allocate_unique_shortcodes_avoiding(
                indexed,
                used,
                derive_shortcode_stem=derive_shortcode_stem,
                allocate_unique_shortcodes=allocate_unique_shortcodes,
                first_unused_shortcode=first_unused_shortcode,
            )
            for index, asset_key, _slug in indexed:
                allocated_by_asset[asset_key] = allocated[index]

        sql = """
            INSERT INTO reaction_type (
                image_url, category_slug, asset_key, shortcode
            )
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (asset_key) DO UPDATE SET
                image_url = EXCLUDED.image_url,
                category_slug = EXCLUDED.category_slug,
                shortcode = EXCLUDED.shortcode
        """
        for category_slug, _fname, asset_key in uploaded:
            if image_url_template:
                image_url = image_url_template.format(asset_key=asset_key)
            else:
                image_url = asset_key
            existing = existing_by_asset.get(asset_key)
            if existing is not None and existing["shortcode"]:
                shortcode = str(existing["shortcode"])
            else:
                shortcode = allocated_by_asset[asset_key]
            await conn.execute(
                sql, image_url, category_slug, asset_key, shortcode
            )
    finally:
        await conn.close()


def ensure_bucket(client: Any, bucket: str) -> None:
    from botocore.exceptions import ClientError

    try:
        client.head_bucket(Bucket=bucket)
    except ClientError:
        client.create_bucket(Bucket=bucket)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Upload emoji packs to RustFS and optionally upsert reaction_type.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print S3 keys; no upload and no DB.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip upload if object already exists (HeadObject).",
    )
    parser.add_argument(
        "--sync-db",
        action="store_true",
        help="After S3 upload, upsert rows into reaction_type.",
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL", ""),
        help="Postgres URL (or env DATABASE_URL). Required with --sync-db.",
    )
    parser.add_argument(
        "--endpoint",
        default=_default_rustfs_endpoint(),
        help="RustFS S3 API base URL (env RUSTFS_ENDPOINT or RUSTFS_INTERNAL_BASE_URL).",
    )
    parser.add_argument(
        "--bucket",
        default=os.environ.get("RUSTFS_BUCKET", "filmony-reactions"),
        help="Bucket name (or env RUSTFS_BUCKET).",
    )
    parser.add_argument(
        "--emoji-root",
        type=Path,
        default=None,
        help="Root folder with pack subdirs (default: <repo>/emoji).",
    )
    parser.add_argument(
        "--image-url-template",
        default="",
        help="Optional Python format for image_url in DB, e.g. "
        '"https://api.example.com/api/reactions/asset/{asset_key}". '
        "Empty: store asset_key as image_url fallback.",
    )
    return parser.parse_args(argv)


def _run_upload_loop(
    *,
    tabs: tuple[Any, ...],
    emoji_root: Path,
    bucket: str,
    client: Any | None,
    dry_run: bool,
    skip_existing: bool,
) -> tuple[list[tuple[str, str, str]], int, int]:
    from botocore.exceptions import ClientError

    uploaded: list[tuple[str, str, str]] = []
    uploaded_count = 0
    skipped_existing = 0

    for tab in tabs:
        folder = emoji_root / tab.directory
        if not folder.is_dir():
            print(f"skip missing dir: {folder}")
            continue
        for path in sorted(folder.iterdir()):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".png", ".gif", ".webp", ".jpg", ".jpeg"}:
                continue
            key = f"reactions/{tab.slug}/{path.name}"
            if dry_run:
                print(f"would upload: s3://{bucket or '<bucket>'}/{key}")
                uploaded.append((tab.slug, path.name, key))
                uploaded_count += 1
                continue

            assert client is not None
            if skip_existing:
                try:
                    client.head_object(Bucket=bucket, Key=key)
                    print(f"SKIP exists: {key}")
                    skipped_existing += 1
                    uploaded.append((tab.slug, path.name, key))
                    continue
                except ClientError as exc:
                    code = (exc.response.get("Error") or {}).get("Code", "")
                    if code not in {"404", "NoSuchKey", "NotFound"}:
                        raise

            ctype, _encoding = mimetypes.guess_type(path.name)
            extra: dict[str, str] = {}
            if ctype:
                extra["ContentType"] = ctype
            client.upload_file(str(path), bucket, key, ExtraArgs=extra or {})
            uploaded_count += 1
            uploaded.append((tab.slug, path.name, key))
            print(f"OK {key}")

    return uploaded, uploaded_count, skipped_existing


def main() -> int:
    argv = sys.argv[1:]
    ns = parse_args(argv)
    if ns.dry_run and ns.sync_db:
        print("Нельзя одновременно --dry-run и --sync-db.", file=sys.stderr)
        return 1

    try:
        import boto3
        from botocore.client import Config
    except ImportError:
        print(
            "Install boto3 (e.g. `uv sync --group prod` in backend/).", file=sys.stderr
        )
        return 1

    if ns.sync_db and not (ns.database_url or "").strip():
        print("--sync-db requires --database-url or DATABASE_URL.", file=sys.stderr)
        return 1

    reaction_tabs = _load_reaction_tab_order()

    access = os.environ.get("RUSTFS_ACCESS_KEY")
    secret = os.environ.get("RUSTFS_SECRET_KEY")
    bucket = (ns.bucket or "").strip()
    if not ns.dry_run and (not access or not secret or not bucket):
        print(
            "Set RUSTFS_ACCESS_KEY, RUSTFS_SECRET_KEY, and --bucket / RUSTFS_BUCKET "
            "(use --dry-run to only list keys).",
            file=sys.stderr,
        )
        return 1

    client: Any | None = None
    if not ns.dry_run:
        client = boto3.client(
            "s3",
            endpoint_url=ns.endpoint,
            aws_access_key_id=access,
            aws_secret_access_key=secret,
            region_name="us-east-1",
            config=Config(signature_version="s3v4"),
        )
        ensure_bucket(client, bucket)
        print(f"bucket ready: {bucket} @ {ns.endpoint}")

    if ns.emoji_root is not None:
        emoji_root = ns.emoji_root
    else:
        env_repo = (os.environ.get("FILMONY_REPO_ROOT") or "").strip()
        if env_repo:
            emoji_root = Path(env_repo) / "emoji"
        else:
            emoji_root = Path(__file__).resolve().parents[1] / "emoji"

    uploaded, uploaded_count, skipped_existing = _run_upload_loop(
        tabs=reaction_tabs,
        emoji_root=emoji_root,
        bucket=bucket,
        client=client,
        dry_run=ns.dry_run,
        skip_existing=ns.skip_existing,
    )

    print(f"done: {uploaded_count} object(s){' (dry-run)' if ns.dry_run else ''}")
    if skipped_existing:
        print(f"skipped (already in bucket): {skipped_existing}")

    if ns.sync_db:
        tpl = (ns.image_url_template or "").strip() or None
        asyncio.run(
            upsert_reaction_rows(
                ns.database_url.strip(), uploaded, image_url_template=tpl
            )
        )
        print(f"db: upserted {len(uploaded)} reaction_type row(s)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
