"""Scoring rules for probabilistic predictions.

Accuracy is deliberately reported last and treated as a vanity metric: a model
that says 0.99 on every favourite and one that says 0.55 can share the same
accuracy while only one of them is bettable. Log loss and Brier score punish
miscalibration; calibration error measures it directly.
"""
from __future__ import annotations

import math

EPS = 1e-15


def _clip(p: float) -> float:
    return min(max(p, EPS), 1.0 - EPS)


def log_loss(y_true, y_prob) -> float:
    ys, ps = list(y_true), list(y_prob)
    if not ys:
        return float("nan")
    return -sum(y * math.log(_clip(p)) + (1 - y) * math.log(1 - _clip(p))
                for y, p in zip(ys, ps)) / len(ys)


def brier_score(y_true, y_prob) -> float:
    ys, ps = list(y_true), list(y_prob)
    if not ys:
        return float("nan")
    return sum((p - y) ** 2 for y, p in zip(ys, ps)) / len(ys)


def accuracy(y_true, y_prob, threshold: float = 0.5) -> float:
    ys, ps = list(y_true), list(y_prob)
    if not ys:
        return float("nan")
    return sum(int((p >= threshold) == bool(y)) for y, p in zip(ys, ps)) / len(ys)


def calibration_bins(y_true, y_prob, n_bins: int = 10) -> list[dict]:
    """Reliability table: predicted vs observed frequency per probability bin."""
    ys, ps = list(y_true), list(y_prob)
    bins: list[dict] = []
    for i in range(n_bins):
        lo, hi = i / n_bins, (i + 1) / n_bins
        idx = [j for j, p in enumerate(ps) if (p >= lo and (p < hi or (i == n_bins - 1 and p <= hi)))]
        if not idx:
            bins.append({"bin_lo": lo, "bin_hi": hi, "n": 0,
                         "mean_pred": float("nan"), "observed": float("nan")})
            continue
        bins.append({
            "bin_lo": lo, "bin_hi": hi, "n": len(idx),
            "mean_pred": sum(ps[j] for j in idx) / len(idx),
            "observed": sum(ys[j] for j in idx) / len(idx),
        })
    return bins


def expected_calibration_error(y_true, y_prob, n_bins: int = 10) -> float:
    """Weighted mean |predicted - observed| across bins. Lower is better."""
    bins = calibration_bins(y_true, y_prob, n_bins)
    total = sum(b["n"] for b in bins)
    if total == 0:
        return float("nan")
    return sum(b["n"] / total * abs(b["mean_pred"] - b["observed"])
               for b in bins if b["n"] > 0)


def evaluate(y_true, y_prob, n_bins: int = 10) -> dict:
    return {
        "n": len(list(y_true)),
        "log_loss": log_loss(y_true, y_prob),
        "brier": brier_score(y_true, y_prob),
        "ece": expected_calibration_error(y_true, y_prob, n_bins),
        "accuracy": accuracy(y_true, y_prob),
        "base_rate": (sum(y_true) / len(y_true)) if len(y_true) else float("nan"),
    }
