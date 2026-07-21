"""Thin CLI so every module runs standalone:
    python -m tennisbet <stage>
Stages: ingest | features | train | predict | value | news | pipeline
Each currently reports that its module is a stub — the wiring is real, the
internals are the work ahead.
"""
from __future__ import annotations

import argparse

STAGES = ["ingest", "features", "train", "predict", "value", "news", "pipeline"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tennisbet")
    parser.add_argument("stage", choices=STAGES)
    parser.add_argument("--config", default="config/config.yaml")
    args = parser.parse_args(argv)
    print(f"[tennisbet] stage='{args.stage}' — module scaffolded, not yet implemented.")
    print("See the module README and the roadmap in docs/architecture.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
