#!/usr/bin/env python3
"""Read sample files from the S3-backed input fileset using Daft + GVFS.

This is the canonical "Daft + Gravitino + S3" path: Daft uses the Gravitino
IOConfig to resolve the virtual ``gvfs://`` path to the underlying S3/MinIO
objects. The only requirement on the host side is that ``minio`` resolves to
``127.0.0.1`` (the gravitino-playground exposes MinIO on port 9000).
"""
from __future__ import annotations

import sys

import daft

sys.path.insert(0, str(__file__).rsplit("/scripts", 1)[0])

from gravitino_daft.config import (  # noqa: E402
    INPUT_FILESET,
    S3_INPUT_FILESET,
    gravitino_io_config,
    s3_gvfs_path,
)


def main() -> None:
    io_config = gravitino_io_config()

    # Read all parquet files in the S3-backed input fileset.
    parquet_uri = s3_gvfs_path(S3_INPUT_FILESET, "*.parquet")
    print(f"Reading {parquet_uri}")
    df = daft.read_parquet(parquet_uri, io_config=io_config)
    print("Parquet content:")
    df.show()

    # Read CSV as an alternative format demonstration.
    csv_uri = s3_gvfs_path(S3_INPUT_FILESET, "*.csv")
    print(f"Reading {csv_uri}")
    csv_df = daft.read_csv(csv_uri, io_config=io_config)
    print("CSV content:")
    csv_df.show()

    # Glob all files in the fileset.
    glob_uri = s3_gvfs_path(S3_INPUT_FILESET, "**/*")
    print(f"Listing files via glob: {glob_uri}")
    files_df = daft.from_glob_path(glob_uri, io_config=io_config)
    print("Files in S3 fileset:")
    files_df.show()

    print(f"\n[note] This is the same GVFS pattern used by local filesets:")
    print(f"       local : gvfs://fileset/.../{INPUT_FILESET}")
    print(f"       s3    : {parquet_uri}")


if __name__ == "__main__":
    main()
