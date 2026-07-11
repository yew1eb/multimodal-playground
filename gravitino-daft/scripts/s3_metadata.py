#!/usr/bin/env python3
"""List S3-backed fileset metadata from Gravitino using the REST API.

This is a small helper that shows how to discover fileset locations managed by
Gravitino. The returned ``storageLocation`` values can then be used to build
``s3://`` paths for Daft reads/writes.
"""
from __future__ import annotations

import sys

import requests

sys.path.insert(0, str(__file__).rsplit("/scripts", 1)[0])

from gravitino_daft.config import (  # noqa: E402
    GRAVITINO_ENDPOINT,
    GRAVITINO_METALAKE,
    S3_CATALOG,
    S3_INPUT_FILESET,
    S3_OUTPUT_FILESET,
    S3_SCHEMA,
    headers,
)


def list_filesets() -> list[str]:
    """Return the names of filesets under the S3 catalog/schema."""
    url = (
        f"{GRAVITINO_ENDPOINT}/api/metalakes/{GRAVITINO_METALAKE}/"
        f"catalogs/{S3_CATALOG}/schemas/{S3_SCHEMA}/filesets"
    )
    resp = requests.get(url, headers=headers())
    resp.raise_for_status()
    identifiers = resp.json().get("identifiers", [])
    return [ident["name"] for ident in identifiers]


def get_fileset_location(name: str) -> str:
    """Return the storage location of a specific fileset."""
    url = (
        f"{GRAVITINO_ENDPOINT}/api/metalakes/{GRAVITINO_METALAKE}/"
        f"catalogs/{S3_CATALOG}/schemas/{S3_SCHEMA}/filesets/{name}"
    )
    resp = requests.get(url, headers=headers())
    resp.raise_for_status()
    return resp.json()["fileset"]["storageLocation"]


def main() -> None:
    print(f"Gravitino endpoint: {GRAVITINO_ENDPOINT}")
    print(f"Catalog: {S3_CATALOG}, Schema: {S3_SCHEMA}")
    print("\nFilesets:")
    for name in list_filesets():
        location = get_fileset_location(name)
        daft_path = location.replace("s3a://", "s3://")
        print(f"  {name}")
        print(f"    Gravitino location: {location}")
        print(f"    Daft S3 path:       {daft_path}")

    print(f"\nInput fileset : {get_fileset_location(S3_INPUT_FILESET)}")
    print(f"Output fileset: {get_fileset_location(S3_OUTPUT_FILESET)}")


if __name__ == "__main__":
    main()
