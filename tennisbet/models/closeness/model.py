"""Closeness model. Label-agnostic: it trains on whatever target labels.py
produces for the configured label name. Regression for continuous labels,
classification for went_to_deciding_set.
"""
from __future__ import annotations

from ...core.contracts import ClosenessPrediction, MatchFeatures
from ..base import Predictor


class ClosenessModel(Predictor):
    version = "closeness-0.0.1"

    def __init__(self, label_name: str = "games_margin"):
        self.label_name = label_name

    def fit(self, X, y):
        raise NotImplementedError

    def predict(self, X):
        raise NotImplementedError

    def predict_match(self, mf: MatchFeatures) -> ClosenessPrediction:
        raise NotImplementedError
