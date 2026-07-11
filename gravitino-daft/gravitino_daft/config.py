"""Shared configuration loaded from environment variables."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


# Load .env from the project root if present.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env", override=False)


GRAVITINO_ENDPOINT = os.getenv("GRAVITINO_ENDPOINT", "http://localhost:8090").rstrip("/")
GRAVITINO_METALAKE = os.getenv("GRAVITINO_METALAKE", "metalake_demo")
GRAVITINO_CATALOG = os.getenv("GRAVITINO_CATALOG", "demo_fileset_catalog")
GRAVITINO_SCHEMA = os.getenv("GRAVITINO_SCHEMA", "demo")
GRAVITINO_USERNAME = os.getenv("GRAVITINO_USERNAME", "admin")
GRAVITINO_AUTH_TYPE = os.getenv("GRAVITINO_AUTH_TYPE", "simple")
INPUT_FILESET = os.getenv("INPUT_FILESET", "input")
OUTPUT_FILESET = os.getenv("OUTPUT_FILESET", "output")

# S3 / MinIO configuration used by the S3-backed fileset examples.
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://localhost:9000").rstrip("/")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID", "minioadmin")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY", "minioadmin")
S3_REGION = os.getenv("S3_REGION", "us-east-1")
S3_BUCKET = os.getenv("S3_BUCKET", "gravitino-bucket")
S3_PATH_STYLE_ACCESS = os.getenv("S3_PATH_STYLE_ACCESS", "true").lower() == "true"

S3_CATALOG = os.getenv("S3_CATALOG", "catalog_s3")
S3_SCHEMA = os.getenv("S3_SCHEMA", "demo_s3")
S3_INPUT_FILESET = os.getenv("S3_INPUT_FILESET", "input_s3")
S3_OUTPUT_FILESET = os.getenv("S3_OUTPUT_FILESET", "output_s3")


def headers() -> dict:
    """Return common headers for Gravitino REST API calls."""
    return {
        "Accept": "application/vnd.gravitino.v1+json",
        "Content-Type": "application/json",
    }


def gravitino_io_config():
    """Return a Daft IOConfig configured for Gravitino GVFS."""
    from daft.io import GravitinoConfig, IOConfig

    return IOConfig(
        gravitino=GravitinoConfig(
            endpoint=GRAVITINO_ENDPOINT,
            metalake_name=GRAVITINO_METALAKE,
            auth_type=GRAVITINO_AUTH_TYPE,
            username=GRAVITINO_USERNAME,
        )
    )


def s3_io_config():
    """Return a Daft IOConfig configured for direct S3/MinIO access.

    This is used to read/write the actual S3 objects that back a Gravitino
    fileset. The bucket, path-style access and endpoint match the defaults of
    the gravitino-playground MinIO service.
    """
    from daft.io import IOConfig, S3Config

    return IOConfig(
        s3=S3Config(
            endpoint_url=S3_ENDPOINT,
            key_id=S3_ACCESS_KEY_ID,
            access_key=S3_SECRET_ACCESS_KEY,
            region_name=S3_REGION,
            use_ssl=S3_ENDPOINT.startswith("https://"),
            force_virtual_addressing=False,
        )
    )


def gvfs_path(fileset: str, path: str = "") -> str:
    """Build a GVFS URL for the given fileset and optional path."""
    base = f"gvfs://fileset/{GRAVITINO_CATALOG}/{GRAVITINO_SCHEMA}/{fileset}"
    if path:
        path = path.lstrip("/")
        return f"{base}/{path}"
    return base


def s3_gvfs_path(fileset: str, path: str = "") -> str:
    """Build a GVFS URL for an S3-backed fileset and optional path."""
    base = f"gvfs://fileset/{S3_CATALOG}/{S3_SCHEMA}/{fileset}"
    if path:
        path = path.lstrip("/")
        return f"{base}/{path}"
    return base


def s3_actual_path(fileset: str, path: str = "") -> str:
    """Build an s3:// URL for the actual storage location of an S3-backed fileset.

    Gravitino fileset locations use the s3a:// scheme; Daft expects s3://.
    """
    base = f"s3://{S3_BUCKET}/fileset/{S3_SCHEMA}/{fileset}"
    if path:
        path = path.lstrip("/")
        return f"{base}/{path}"
    return base


def gvfs_options() -> dict:
    """Return options for the GravitinoVirtualFileSystem Python client.

    The Python GVFS client reads S3 credentials from underscore-style property
    names (s3_access_key_id, s3_secret_access_key, s3_endpoint). The catalog in
    gravitino-playground is created with hyphen-style names and the Docker
    internal endpoint (http://minio:9000), so we override them here for host-side
    access.
    """
    return {
        "auth_type": GRAVITINO_AUTH_TYPE,
        "s3_access_key_id": S3_ACCESS_KEY_ID,
        "s3_secret_access_key": S3_SECRET_ACCESS_KEY,
        "s3_endpoint": S3_ENDPOINT,
    }
