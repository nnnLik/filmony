"""S3-compatible client for RustFS (MinIO-style) using ``ReactionMediaSettings``.

Callers in routes typically use the module-level helpers with explicit credentials
(``asyncio.to_thread``); services use :meth:`RustfsS3Client.try_build_from_settings`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from conf import settings

S3_SERVICE_NAME = 's3'
RUSTFS_S3_REGION_NAME = 'us-east-1'
S3_SIGNATURE_VERSION = 's3v4'


@dataclass(frozen=True, slots=True)
class RustfsGetObjectResult:
    body: bytes
    content_type: str | None


class RustfsKeyNotFoundError(Exception):
    """Object missing in bucket."""


class RustfsClientError(Exception):
    """Transport, auth, or unknown S3 failure."""


class RustfsPutObjectError(Exception):
    """PutObject failure."""


class RustfsDeleteObjectError(Exception):
    """DeleteObject failure."""


def _boto_s3_client(*, endpoint_url: str, access_key_id: str, secret_access_key: str) -> Any:
    return boto3.client(
        S3_SERVICE_NAME,
        endpoint_url=endpoint_url.rstrip('/'),
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name=RUSTFS_S3_REGION_NAME,
        config=Config(signature_version=S3_SIGNATURE_VERSION),
    )


@dataclass
class RustfsS3Client:
    """Thin boto3 S3 wrapper for one RustFS bucket.

    Credentials and endpoint are taken from constructor arguments; use
    :meth:`try_build_from_settings` so callers do not thread env values manually.
    The boto3 client is created in ``__post_init__`` (one client per instance).
    """

    endpoint_url: str
    access_key_id: str
    secret_access_key: str
    bucket: str
    _s3: Any = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        ep = self.endpoint_url.strip().rstrip('/')
        self.endpoint_url = ep
        self._s3 = _boto_s3_client(
            endpoint_url=ep,
            access_key_id=self.access_key_id,
            secret_access_key=self.secret_access_key,
        )

    @classmethod
    def try_build_from_settings(cls) -> RustfsS3Client | None:
        """Return a client when reaction media env is complete; otherwise ``None``."""
        m = settings.reaction_media
        endpoint = m.rustfs_internal_base_url.strip().rstrip('/')
        bucket = m.rustfs_bucket.strip()
        access = m.rustfs_access_key.strip()
        secret = m.rustfs_secret_key.strip()
        if not endpoint or not bucket or not access or not secret:
            return None
        return cls(
            endpoint_url=endpoint,
            access_key_id=access,
            secret_access_key=secret,
            bucket=bucket,
        )

    def get_object(self, key: str) -> RustfsGetObjectResult:
        try:
            obj = self._s3.get_object(Bucket=self.bucket, Key=key)
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

    def put_object(self, key: str, body: bytes, content_type: str) -> None:
        try:
            self._s3.put_object(
                Bucket=self.bucket,
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

    def delete_object(self, key: str) -> None:
        try:
            self._s3.delete_object(Bucket=self.bucket, Key=key)
        except ClientError as exc:
            raise RustfsDeleteObjectError(
                (exc.response.get('Error') or {}).get('Code', 'ClientError')
            ) from exc
        except OSError as exc:
            raise RustfsDeleteObjectError(str(exc)) from exc


def get_rustfs_object_bytes(
    *,
    endpoint_url: str,
    access_key_id: str,
    secret_access_key: str,
    bucket: str,
    key: str,
) -> RustfsGetObjectResult:
    """Sync GetObject; intended for ``asyncio.to_thread`` from async routes."""
    return RustfsS3Client(
        endpoint_url=endpoint_url,
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        bucket=bucket,
    ).get_object(key)


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
    """Sync PutObject; intended for ``asyncio.to_thread``."""
    RustfsS3Client(
        endpoint_url=endpoint_url,
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        bucket=bucket,
    ).put_object(key, body, content_type)


def delete_rustfs_object_bytes(
    *,
    endpoint_url: str,
    access_key_id: str,
    secret_access_key: str,
    bucket: str,
    key: str,
) -> None:
    """Sync DeleteObject; intended for ``asyncio.to_thread``."""
    RustfsS3Client(
        endpoint_url=endpoint_url,
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        bucket=bucket,
    ).delete_object(key)
