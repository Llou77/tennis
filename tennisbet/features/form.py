"""Recent form, fatigue and rest: win rate over lookback window, matches in
last 14 days, days since last match, sets played recently, travel/time-zone.
"""
from __future__ import annotations

from .base import FeatureBuilder


class FormFeatureBuilder(FeatureBuilder):
    name = "form"

    def build(self, match, **ctx) -> dict:
        raise NotImplementedError
