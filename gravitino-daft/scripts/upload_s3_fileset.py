#!/usr/bin/env python3
"""Generate sample files and upload them to the S3-backed input fileset via GVFS.

This demonstrates the "Gravitino metadata + GVFS data plane" path: the actual
storage is S3/MinIO, but users interact with logical fileset paths such as
``gvfs://fileset/catalog_s3/demo_s3/input_s3/sample.parquet``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(__file__).rsplit("/scripts", 1)[0])

from gravitino_daft.config import (  # noqa: E402
    GRAVITINO_ENDPOINT,
    GRAVITINO_METALAKE,
    S3_INPUT_FILESET,
    gvfs_options,
    s3_gvfs_path,
)


def generate_sample_files(data_dir: Path) -> list[Path]:
    """Create parquet, csv, and json sample files under data_dir."""
    data_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["alice", "bob", "carol", "dave", "eve"],
        "score": [85.5, 92.0, 78.5, 88.0, 95.5],
    })

    files = []
    parquet_path = data_dir / "sample.parquet"
    csv_path = data_dir / "sample.csv"
    json_path = data_dir / "sample.json"

    df.to_parquet(parquet_path, index=False)
    df.to_csv(csv_path, index=False)
    json_path.write_text(json.dumps(df.to_dict(orient="records"), indent=2))

    files.extend([parquet_path, csv_path, json_path])
    print(f"[ok] generated sample files in {data_dir}")
    return files


def upload_to_s3_fileset(local_files: list[Path]) -> None:
    """Upload local files to the S3-backed input fileset using GVFS."""
    from gravitino import gvfs

    fs = gvfs.GravitinoVirtualFileSystem(
        server_uri=GRAVITINO_ENDPOINT,
        metalake_name=GRAVITINO_METALAKE,
        options=gvfs_options(),
    )

    target_dir = s3_gvfs_path(S3_INPUT_FILESET)
    if not fs.exists(target_dir):
        fs.mkdir(target_dir)

    for local_file in local_files:
        target_path = f"{target_dir}/{local_file.name}"
        with open(local_file, "rb") as src:
            with fs.open(target_path, "wb") as dst:
                dst.write(src.read())
        print(f"[ok] uploaded {local_file.name} -> {target_path}")

    print(f"[ok] files in {target_dir}:")
    for entry in fs.ls(target_dir):
        # fsspec/s3fs may return dict or string depending on detail=.
        name = entry["name"] if isinstance(entry, dict) else entry
        print(f"  - {name}")


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data" / "s3"
    local_files = generate_sample_files(data_dir)
    upload_to_s3_fileset(local_files)


if __name__ == "__main__":
    main()
