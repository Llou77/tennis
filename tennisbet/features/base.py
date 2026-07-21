"""FeatureBuilder interface. Each builder contributes a slice of features for
a match; features.build merges them into one MatchFeatures.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..core.contracts import RawMatch


class FeatureBuilder(ABC):
    name: str = "base"

    @abstractmethod
    def build(self, match: RawMatch, **ctx) -> dict:
        """Return {feature_name: value} for this match. Must be leak-free:
        use only information available BEFORE match_date."""
        raise NotImplementedError
