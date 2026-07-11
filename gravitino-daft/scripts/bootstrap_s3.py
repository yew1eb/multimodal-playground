#!/usr/bin/env python3
"""Bootstrap an S3/MinIO-backed fileset catalog, schema and filesets.

This script assumes the gravitino-playground is running and that MinIO is
available at the endpoint configured in .env (default http://localhost:9000).
It is idempotent: missing objects are created, existing ones are skipped.
"""
from __future__ import annotations

import sys

import requests

sys.path.insert(0, str(__file__).rsplit("/scripts", 1)[0])

from gravitino_daft.config import (  # noqa: E402
    GRAVITINO_ENDPOINT,
    GRAVITINO_METALAKE,
    S3_ACCESS_KEY_ID,
    S3_BUCKET,
    S3_CATALOG,
    S3_ENDPOINT,
    S3_INPUT_FILESET,
    S3_OUTPUT_FILESET,
    S3_PATH_STYLE_ACCESS,
    S3_REGION,
    S3_SCHEMA,
    S3_SECRET_ACCESS_KEY,
    headers,
)


def _url(path: str) -> str:
    return f"{GRAVITINO_ENDPOINT}/api/metalakes{path}"


def ensure_metalake() -> None:
    """Create the metalake if it does not exist."""
    metalake_url = _url(f"/{GRAVITINO_METALAKE}")
    resp = requests.get(metalake_url, headers=headers())
    if resp.status_code == 200:
        print(f"[ok] metalake '{GRAVITINO_METALAKE}' already exists")
        return

    create_resp = requests.post(
        _url(""),
        headers=headers(),
        json={
            "name": GRAVITINO_METALAKE,
            "comment": "Local Gravitino playground metalake",
        },
    )
    if create_resp.status_code in (200, 201):
        print(f"[ok] created metalake '{GRAVITINO_METALAKE}'")
    else:
        raise RuntimeError(
            f"Failed to create metalake: {create_resp.status_code} {create_resp.text}"
        )


def ensure_s3_catalog() -> None:
    """Create the S3-backed FILESET catalog if it does not exist."""
    catalog_url = _url(f"/{GRAVITINO_METALAKE}/catalogs/{S3_CATALOG}")
    resp = requests.get(catalog_url, headers=headers())
    if resp.status_code == 200:
        print(f"[ok] catalog '{S3_CATALOG}' already exists")
        return

    # The property names with hyphens match the convention used by the
    # gravitino-playground init script. Some Gravitino clients (e.g. Java /
    # server-side) consume them in this form.
    create_resp = requests.post(
        _url(f"/{GRAVITINO_METALAKE}/catalogs"),
        headers=headers(),
        json={
            "name": S3_CATALOG,
            "type": "FILESET",
            "provider": "fileset",
            "comment": "S3/MinIO fileset catalog for gravitino-daft",
            "properties": {
                "location": f"s3a://{S3_BUCKET}/fileset/",
                "s3-endpoint": "http://minio:9000",
                "s3-access-key-id": S3_ACCESS_KEY_ID,
                "s3-secret-access-key": S3_SECRET_ACCESS_KEY,
                "s3-region": S3_REGION,
                "s3-path-style-access": str(S3_PATH_STYLE_ACCESS).lower(),
            },
        },
    )
    if create_resp.status_code in (200, 201):
        print(f"[ok] created catalog '{S3_CATALOG}'")
    else:
        raise RuntimeError(
            f"Failed to create catalog: {create_resp.status_code} {create_resp.text}"
        )


def ensure_s3_schema() -> None:
    """Create the schema under the S3-backed catalog if it does not exist."""
    schema_url = _url(
        f"/{GRAVITINO_METALAKE}/catalogs/{S3_CATALOG}/schemas/{S3_SCHEMA}"
    )
    resp = requests.get(schema_url, headers=headers())
    if resp.status_code == 200:
        print(f"[ok] schema '{S3_SCHEMA}' already exists")
        return

    create_resp = requests.post(
        _url(f"/{GRAVITINO_METALAKE}/catalogs/{S3_CATALOG}/schemas"),
        headers=headers(),
        json={
            "name": S3_SCHEMA,
            "comment": "Schema for gravitino-daft S3 experiments",
            "properties": {},
        },
    )
    if create_resp.status_code in (200, 201):
        print(f"[ok] created schema '{S3_SCHEMA}'")
    else:
        raise RuntimeError(
            f"Failed to create schema: {create_resp.status_code} {create_resp.text}"
        )


def ensure_s3_fileset(name: str) -> None:
    """Create a MANAGED fileset under the S3 schema if it does not exist."""
    fileset_url = _url(
        f"/{GRAVITINO_METALAKE}/catalogs/{S3_CATALOG}/schemas/{S3_SCHEMA}/filesets/{name}"
    )
    resp = requests.get(fileset_url, headers=headers())
    if resp.status_code == 200:
        print(f"[ok] fileset '{name}' already exists")
        return

    create_resp = requests.post(
        _url(
            f"/{GRAVITINO_METALAKE}/catalogs/{S3_CATALOG}/schemas/{S3_SCHEMA}/filesets"
        ),
        headers=headers(),
        json={
            "name": name,
            "comment": f"{name} S3 fileset for gravitino-daft experiments",
            "type": "MANAGED",
            "properties": {},
        },
    )
    if create_resp.status_code in (200, 201):
        print(f"[ok] created fileset '{name}'")
    else:
        raise RuntimeError(
            f"Failed to create fileset '{name}': {create_resp.status_code} {create_resp.text}"
        )


def main() -> None:
    print(f"Bootstrapping S3 fileset metadata at {GRAVITINO_ENDPOINT}")
    print(f"  catalog : {S3_CATALOG}")
    print(f"  schema  : {S3_SCHEMA}")
    print(f"  filesets: {S3_INPUT_FILESET}, {S3_OUTPUT_FILESET}")
    print(f"  S3 endpoint (host): {S3_ENDPOINT}")
    ensure_metalake()
    ensure_s3_catalog()
    ensure_s3_schema()
    ensure_s3_fileset(S3_INPUT_FILESET)
    ensure_s3_fileset(S3_OUTPUT_FILESET)
    print("[done]")


if __name__ == "__main__":
    main()
