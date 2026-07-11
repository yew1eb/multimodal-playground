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
            username=GRAVITINO_USERNAME,
        )
    )


def gvfs_path(fileset: str, path: str = "") -> str:
    """Build a GVFS URL for the given fileset and optional path."""
    base = f"gvfs://fileset/{GRAVITINO_CATALOG}/{GRAVITINO_SCHEMA}/{fileset}"
    if path:
        path = path.lstrip("/")
        return f"{base}/{path}"
    return base
