"""Head-to-head: overall and surface-specific record, recency-weighted."""
from __future__ import annotations

from .base import FeatureBuilder


class H2HFeatureBuilder(FeatureBuilder):
    name = "h2h"

    def build(self, match, **ctx) -> dict:
        raise NotImplementedError
