"""Candidate definitions of match "closeness".

The closeness target is a MODELING DECISION, not a given. Pick one label here
(set models.closeness.label in config). Each function maps a finished RawMatch
to a numeric target. Swapping the label must not require touching the model.

Parsing note: `score` looks like "6-4 3-6 7-6(5)". A real parser lives in a
TODO; these signatures define the contract.
"""
from __future__ import annotations

from typing import Callable

from ...core.contracts import RawMatch


def games_margin(match: RawMatch) -> float:
    """Absolute difference in total games won. Small = close."""
    raise NotImplementedError


def sets_margin(match: RawMatch) -> float:
    """Difference in sets won (e.g. 2-0 -> 2, 2-1 -> 1)."""
    raise NotImplementedError


def total_games(match: RawMatch) -> float:
    """Total games played — pairs naturally with an over/under games line."""
    raise NotImplementedError


def went_to_deciding_set(match: RawMatch) -> float:
    """1.0 if the match reached a final deciding set, else 0.0 (classification)."""
    raise NotImplementedError


def competitiveness_index(match: RawMatch) -> float:
    """0..1: 1 - |games_a - games_b| / total_games. 1 = maximally close."""
    raise NotImplementedError


# Registry — config picks by name.
LABELS: dict[str, Callable[[RawMatch], float]] = {
    "games_margin": games_margin,
    "sets_margin": sets_margin,
    "total_games": total_games,
    "went_to_deciding_set": went_to_deciding_set,
    "competitiveness_index": competitiveness_index,
}
