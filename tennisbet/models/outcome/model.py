"""Outcome model: P(player_a wins). Consumes MatchFeatures, emits
OutcomePrediction. Baseline fallback = Elo-logistic; upgrade path = gradient
boosting. Calibration is mandatory before these probabilities touch betting.
"""
from __future__ import annotations

from ...core.contracts import MatchFeatures, OutcomePrediction
from ..base import Predictor


class OutcomeModel(Predictor):
    version = "outcome-0.0.1"

    def fit(self, X, y):
        raise NotImplementedError

    def predict(self, X):
        raise NotImplementedError

    def predict_match(self, mf: MatchFeatures) -> OutcomePrediction:
        # TODO: vectorize mf.features and return calibrated probability.
        raise NotImplementedError
