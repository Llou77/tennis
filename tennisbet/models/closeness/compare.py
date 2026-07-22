"""Compare candidate closeness labels under ONE fixed protocol.

We intentionally keep several closeness definitions (see labels.py) and compare
them instead of guessing one up front. The risk is metric-shopping — picking
whichever label looks best in-sample. Guard against it by fixing evaluation
BEFORE looking: walk-forward split, calibration, and — for labels with a real
market — a backtest against the closing line. Labels without a tradeable market
are informational only, never a betting signal.
"""
from __future__ import annotations

from .labels import LABELS

# Labels that map to an actual bookmaker market (can convert to betting value).
TRADEABLE = {"total_games", "went_to_deciding_set"}


def compare_labels(features, matches, label_names: list[str] | None = None):
    """Train one closeness model per label; return a comparison table
    (label error, calibration, and betting backtest for TRADEABLE labels).
    TODO: implement once P1 data + the walk-forward eval harness exist.
    """
    label_names = label_names or list(LABELS)
    raise NotImplementedError
