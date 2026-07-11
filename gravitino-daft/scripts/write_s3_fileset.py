#!/usr/bin/env python3
"""Write a sample DataFrame to the S3-backed output fileset using Daft + GVFS and read it back."""
from __future__ import annotations

import sys

import daft

sys.path.insert(0, str(__file__).rsplit("/scripts", 1)[0])

from gravitino_daft.config import (  # noqa: E402
    S3_OUTPUT_FILESET,
    gravitino_io_config,
    s3_gvfs_path,
)


def main() -> None:
    io_config = gravitino_io_config()
    output_uri = s3_gvfs_path(S3_OUTPUT_FILESET, "sample_output.parquet")

    df = daft.from_pydict({
        "id": [1, 2, 3],
        "category": ["a", "b", "c"],
        "value": [10.0, 20.0, 30.0],
    })

    print(f"Writing to {output_uri}")
    df.write_parquet(output_uri, io_config=io_config)
    print("[ok] write completed")

    print(f"Reading back from {output_uri}")
    result = daft.read_parquet(output_uri, io_config=io_config)
    result.show()


if __name__ == "__main__":
    main()
