"""Serve/return performance: ace%, 1st-serve %, 1st/2nd-serve points won,
break points saved/converted, hold/break rates (surface-adjusted).
"""
from __future__ import annotations

from .base import FeatureBuilder


class ServeReturnFeatureBuilder(FeatureBuilder):
    name = "serve_return"

    def build(self, match, **ctx) -> dict:
        raise NotImplementedError
