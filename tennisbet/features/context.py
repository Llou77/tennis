"""Match context: surface, tier, round, best_of, indoor/outdoor, altitude,
and match-time weather (from ingestion.weather).
"""
from __future__ import annotations

from .base import FeatureBuilder


class ContextFeatureBuilder(FeatureBuilder):
    name = "context"

    def build(self, match, **ctx) -> dict:
        raise NotImplementedError
