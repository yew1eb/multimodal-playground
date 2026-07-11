#!/usr/bin/env python3
"""Direct S3/MinIO access with Daft, using Gravitino only for metadata discovery.

This script shows an alternative to the GVFS data plane: query Gravitino for
a fileset's physical storage location, then read/write the underlying S3
objects with Daft's ``S3Config``. This is useful when:

- You already have an S3-aware toolchain and only need Gravitino as the
  metadata control plane.
- You want to bypass GVFS and manage credentials/endpoint entirely on the
  client side.
"""
from __future__ import annotations

import sys

import daft
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
    s3_actual_path,
    s3_io_config,
)


def get_fileset_location(name: str) -> str:
    """Fetch the storage location of an S3 fileset from Gravitino."""
    url = (
        f"{GRAVITINO_ENDPOINT}/api/metalakes/{GRAVITINO_METALAKE}/"
        f"catalogs/{S3_CATALOG}/schemas/{S3_SCHEMA}/filesets/{name}"
    )
    resp = requests.get(url, headers=headers())
    resp.raise_for_status()
    return resp.json()["fileset"]["storageLocation"]


def main() -> None:
    io_config = s3_io_config()

    input_location = get_fileset_location(S3_INPUT_FILESET)
    output_location = get_fileset_location(S3_OUTPUT_FILESET)
    print(f"[info] input fileset location : {input_location}")
    print(f"[info] output fileset location: {output_location}")

    # Direct S3 read of the input fileset.
    parquet_uri = s3_actual_path(S3_INPUT_FILESET, "*.parquet")
    print(f"\nReading {parquet_uri}")
    df = daft.read_parquet(parquet_uri, io_config=io_config)
    df.show()

    # Direct S3 write to the output fileset.
    output_uri = s3_actual_path(S3_OUTPUT_FILESET, "direct_sample.parquet")
    print(f"Writing to {output_uri}")
    sample = daft.from_pydict({
        "id": [10, 20, 30],
        "flag": [True, False, True],
        "score": [1.5, 2.5, 3.5],
    })
    sample.write_parquet(output_uri, io_config=io_config)
    print("[ok] write completed")

    print(f"Reading back from {output_uri}")
    daft.read_parquet(output_uri, io_config=io_config).show()


if __name__ == "__main__":
    main()
