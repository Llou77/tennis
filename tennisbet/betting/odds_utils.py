"""Pure odds math. No dependencies, fully tested — the numeric core of value
detection, so it must be correct."""
from __future__ import annotations


def decimal_to_implied(decimal_odds: float) -> float:
    if decimal_odds <= 1.0:
        raise ValueError("decimal odds must be > 1.0")
    return 1.0 / decimal_odds


def implied_to_decimal(p: float) -> float:
    if not 0.0 < p < 1.0:
        raise ValueError("probability must be in (0, 1)")
    return 1.0 / p


def american_to_decimal(american: int) -> float:
    if american == 0:
        raise ValueError("american odds cannot be 0")
    if american > 0:
        return 1.0 + american / 100.0
    return 1.0 + 100.0 / abs(american)


def overround(implied_probs: list[float]) -> float:
    """Bookmaker margin: how far the implied probs sum above 1."""
    return sum(implied_probs) - 1.0


def remove_overround(implied_probs: list[float]) -> list[float]:
    """Proportional de-vig: normalize implied probs to sum to 1.
    De-vig BEFORE comparing to model probabilities."""
    s = sum(implied_probs)
    if s <= 0:
        raise ValueError("implied probabilities must sum to > 0")
    return [p / s for p in implied_probs]
