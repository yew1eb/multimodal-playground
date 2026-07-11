#!/usr/bin/env python3
"""Read sample files from the input fileset using Daft + GVFS."""
from __future__ import annotations

import sys

import daft

sys.path.insert(0, str(__file__).rsplit("/scripts", 1)[0])

from gravitino_daft.config import INPUT_FILESET, gvfs_path, gravitino_io_config  # noqa: E402


def main() -> None:
    io_config = gravitino_io_config()

    # Read all parquet files in the input fileset.
    parquet_uri = gvfs_path(INPUT_FILESET, "*.parquet")
    print(f"Reading {parquet_uri}")
    df = daft.read_parquet(parquet_uri, io_config=io_config)
    print("Parquet content:")
    df.show()

    # Read CSV as an alternative format demonstration.
    csv_uri = gvfs_path(INPUT_FILESET, "*.csv")
    print(f"Reading {csv_uri}")
    csv_df = daft.read_csv(csv_uri, io_config=io_config)
    print("CSV content:")
    csv_df.show()

    # Glob all files in the fileset.
    glob_uri = gvfs_path(INPUT_FILESET, "**/*")
    print(f"Listing files via glob: {glob_uri}")
    files_df = daft.from_glob_path(glob_uri, io_config=io_config)
    print("Files in fileset:")
    files_df.show()


if __name__ == "__main__":
    main()
