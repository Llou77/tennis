"""Thin data-store abstraction shared by all modules.

Default backend is parquet on the local filesystem under data.root.
Swap the body here to move to DuckDB/Postgres without touching callers.
pandas/pyarrow are imported lazily (only the `data` extra needs them).
"""
from __future__ import annotations

from pathlib import Path


def _table_path(root: str, name: str) -> Path:
    return Path(root) / f"{name}.parquet"


def write_table(df, name: str, root: str = "data") -> Path:
    Path(root).mkdir(parents=True, exist_ok=True)
    path = _table_path(root, name)
    df.to_parquet(path, index=False)
    return path


def read_table(name: str, root: str = "data"):
    import pandas as pd  # lazy
    path = _table_path(root, name)
    if not path.exists():
        raise FileNotFoundError(f"table '{name}' not found at {path}")
    return pd.read_parquet(path)
