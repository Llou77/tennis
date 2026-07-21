"""Config loading. yaml is imported lazily so importing this module is cheap."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def load_config(path: str | Path = "config/config.yaml") -> dict[str, Any]:
    import yaml  # lazy
    p = Path(path)
    if not p.exists():
        example = Path("config/config.example.yaml")
        raise FileNotFoundError(
            f"{p} not found. Copy {example} to {p} and edit it."
        )
    with p.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)
