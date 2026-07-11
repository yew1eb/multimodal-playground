#!/usr/bin/env python3
"""Bootstrap Gravitino fileset catalog, schema, and filesets for local experiments.

Uses the Gravitino REST API directly so we don't rely on a specific Python client
version. The script is idempotent: it creates missing objects and skips existing ones.
"""
from __future__ import annotations

import sys

import requests

sys.path.insert(0, str(__file__).rsplit("/scripts", 1)[0])

from gravitino_daft.config import (  # noqa: E402
    GRAVITINO_CATALOG,
    GRAVITINO_ENDPOINT,
    GRAVITINO_METALAKE,
    GRAVITINO_SCHEMA,
    INPUT_FILESET,
    OUTPUT_FILESET,
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


def ensure_catalog() -> None:
    """Create the FILESET catalog if it does not exist."""
    catalog_url = _url(f"/{GRAVITINO_METALAKE}/catalogs/{GRAVITINO_CATALOG}")
    resp = requests.get(catalog_url, headers=headers())
    if resp.status_code == 200:
        print(f"[ok] catalog '{GRAVITINO_CATALOG}' already exists")
        return

    create_resp = requests.post(
        _url(f"/{GRAVITINO_METALAKE}/catalogs"),
        headers=headers(),
        json={
            "name": GRAVITINO_CATALOG,
            "type": "FILESET",
            "provider": "fileset",
            "comment": "Catalog for gravitino-daft experiments",
            "properties": {
                "location": f"file:///tmp/gravitino/{GRAVITINO_CATALOG}",
            },
        },
    )
    if create_resp.status_code in (200, 201):
        print(f"[ok] created catalog '{GRAVITINO_CATALOG}'")
    else:
        raise RuntimeError(
            f"Failed to create catalog: {create_resp.status_code} {create_resp.text}"
        )


def ensure_schema() -> None:
    """Create the schema if it does not exist."""
    schema_url = _url(f"/{GRAVITINO_METALAKE}/catalogs/{GRAVITINO_CATALOG}/schemas/{GRAVITINO_SCHEMA}")
    resp = requests.get(schema_url, headers=headers())
    if resp.status_code == 200:
        print(f"[ok] schema '{GRAVITINO_SCHEMA}' already exists")
        return

    create_resp = requests.post(
        _url(f"/{GRAVITINO_METALAKE}/catalogs/{GRAVITINO_CATALOG}/schemas"),
        headers=headers(),
        json={
            "name": GRAVITINO_SCHEMA,
            "comment": "Schema for gravitino-daft experiments",
            "properties": {},
        },
    )
    if create_resp.status_code in (200, 201):
        print(f"[ok] created schema '{GRAVITINO_SCHEMA}'")
    else:
        raise RuntimeError(
            f"Failed to create schema: {create_resp.status_code} {create_resp.text}"
        )


def ensure_fileset(name: str) -> None:
    """Create a MANAGED fileset if it does not exist."""
    fileset_url = _url(
        f"/{GRAVITINO_METALAKE}/catalogs/{GRAVITINO_CATALOG}/schemas/{GRAVITINO_SCHEMA}/filesets/{name}"
    )
    resp = requests.get(fileset_url, headers=headers())
    if resp.status_code == 200:
        print(f"[ok] fileset '{name}' already exists")
        return

    create_resp = requests.post(
        _url(
            f"/{GRAVITINO_METALAKE}/catalogs/{GRAVITINO_CATALOG}/schemas/{GRAVITINO_SCHEMA}/filesets"
        ),
        headers=headers(),
        json={
            "name": name,
            "comment": f"{name} fileset for gravitino-daft experiments",
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
    print(f"Bootstrapping Gravitino at {GRAVITINO_ENDPOINT}")
    ensure_metalake()
    ensure_catalog()
    ensure_schema()
    ensure_fileset(INPUT_FILESET)
    ensure_fileset(OUTPUT_FILESET)
    print("[done]")


if __name__ == "__main__":
    main()
