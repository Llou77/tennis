"""Staking strategies. Fractional Kelly by default — full Kelly is too
aggressive given model uncertainty."""
from __future__ import annotations


def kelly_fraction(model_p: float, decimal_odds: float) -> float:
    b = decimal_odds - 1.0
    if b <= 0:
        return 0.0
    f = (b * model_p - (1.0 - model_p)) / b
    return max(0.0, f)


def stake_fraction(model_p: float, decimal_odds: float,
                   strategy: str = "fractional_kelly",
                   fraction: float = 0.25, flat: float = 0.01) -> float:
    if strategy == "flat":
        return flat
    if strategy == "kelly":
        return kelly_fraction(model_p, decimal_odds)
    if strategy == "fractional_kelly":
        return kelly_fraction(model_p, decimal_odds) * fraction
    raise ValueError(f"unknown staking strategy: {strategy}")
