"""Assemble all FeatureBuilders into one MatchFeatures per match.
Add/remove a builder here without touching the models module.
"""
from __future__ import annotations

from ..core.contracts import MatchFeatures, RawMatch
from .base import FeatureBuilder
from .context import ContextFeatureBuilder
from .elo import EloFeatureBuilder
from .form import FormFeatureBuilder
from .h2h import H2HFeatureBuilder
from .serve_return import ServeReturnFeatureBuilder

DEFAULT_BUILDERS: list[FeatureBuilder] = [
    EloFeatureBuilder(),
    FormFeatureBuilder(),
    ServeReturnFeatureBuilder(),
    H2HFeatureBuilder(),
    ContextFeatureBuilder(),
]


def build_features(match: RawMatch, builders: list[FeatureBuilder] | None = None,
                   **ctx) -> MatchFeatures:
    builders = builders or DEFAULT_BUILDERS
    feats: dict = {}
    for b in builders:
        feats.update(b.build(match, **ctx))
    return MatchFeatures(match_id=match.match_id, features=feats)
