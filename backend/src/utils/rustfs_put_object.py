"""Authenticated S3 PutObject against RustFS for user-uploaded feed images."""

from __future__ import annotations

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError


class RustfsPutObjectError(Exception):
    """Transport, auth, or unknown S3 failure."""


def put_rustfs_object_bytes(
    *,
    endpoint_url: str,
    access_key_id: str,
    secret_access_key: str,
    bucket: str,
    key: str,
    body: bytes,
    content_type: str,
) -> None:
    """Sync PutObject (SigV4); run from `asyncio.to_thread` in async routes."""
    client = boto3.client(
        's3',
        endpoint_url=endpoint_url.rstrip('/'),
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name='us-east-1',
        config=Config(signature_version='s3v4'),
    )
    try:
        client.put_object(
            Bucket=bucket,
            Key=key,
            Body=body,
            ContentType=content_type,
        )
    except ClientError as exc:
        raise RustfsPutObjectError(
            (exc.response.get('Error') or {}).get('Code', 'ClientError')
        ) from exc
    except OSError as exc:
        raise RustfsPutObjectError(str(exc)) from exc
