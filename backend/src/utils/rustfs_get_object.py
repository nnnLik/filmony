"""Authenticated S3 GetObject against RustFS for the reaction asset proxy."""

from __future__ import annotations

from dataclasses import dataclass

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError


@dataclass(frozen=True, slots=True)
class RustfsGetObjectResult:
    body: bytes
    content_type: str | None


class RustfsKeyNotFoundError(Exception):
    """Object missing in bucket."""


class RustfsClientError(Exception):
    """Transport, auth, or unknown S3 failure."""


def get_rustfs_object_bytes(
    *,
    endpoint_url: str,
    access_key_id: str,
    secret_access_key: str,
    bucket: str,
    key: str,
) -> RustfsGetObjectResult:
    """Sync GetObject (SigV4); run from `asyncio.to_thread` in async routes."""
    client = boto3.client(
        's3',
        endpoint_url=endpoint_url.rstrip('/'),
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name='us-east-1',
        config=Config(signature_version='s3v4'),
    )
    try:
        obj = client.get_object(Bucket=bucket, Key=key)
    except ClientError as exc:
        code = (exc.response.get('Error') or {}).get('Code', '')
        if code in {'NoSuchKey', '404'}:
            raise RustfsKeyNotFoundError(str(code)) from exc
        raise RustfsClientError(code or 'ClientError') from exc
    except OSError as exc:
        raise RustfsClientError(str(exc)) from exc

    body_bytes: bytes = obj['Body'].read()
    raw_ct = obj.get('ContentType')
    ctype: str | None = raw_ct.strip() if isinstance(raw_ct, str) and raw_ct.strip() else None
    return RustfsGetObjectResult(body=body_bytes, content_type=ctype)
