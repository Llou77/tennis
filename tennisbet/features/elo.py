"""Overall + surface-specific Elo. Strongest single signal in tennis modeling.
Maintain a rolling Elo table; expose pre-match ratings for both players.
"""
from __future__ import annotations

from .base import FeatureBuilder


class EloFeatureBuilder(FeatureBuilder):
    name = "elo"

    def __init__(self, k_factor: float = 32, surface_weight: float = 0.5):
        self.k = k_factor
        self.surface_weight = surface_weight

    def build(self, match, **ctx) -> dict:
        # TODO: return elo_a, elo_b, elo_surface_a, elo_surface_b, elo_diff...
        raise NotImplementedError
