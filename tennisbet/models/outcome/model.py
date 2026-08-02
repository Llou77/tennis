"""Outcome model: P(player_a wins).

Consumes `MatchFeatures`, emits `OutcomePrediction`. The estimator is swappable
(`algo="logistic"` or `"lightgbm"`) and calibration is applied on a held-out
*time-ordered* tail of the training data — never a random split, or the
calibrator sees the future.
"""
from __future__ import annotations

from pathlib import Path

from ...core.contracts import MatchFeatures, OutcomePrediction
from ..base import Predictor


class OutcomeModel(Predictor):
    version = "outcome-0.1.0"

    def __init__(self, feature_cols: list[str] | None = None,
                 algo: str = "logistic", calibrate: bool = True,
                 calibration_tail: float = 0.2, random_state: int = 7):
        self.feature_cols = feature_cols
        self.algo = algo
        self.calibrate = calibrate
        self.calibration_tail = calibration_tail
        self.random_state = random_state
        self._model = None
        self._calibrator = None
        self._imputer_means: dict[str, float] = {}

    # ---- internals -------------------------------------------------
    def _make_estimator(self):
        if self.algo == "logistic":
            from sklearn.linear_model import LogisticRegression
            from sklearn.pipeline import Pipeline
            from sklearn.preprocessing import StandardScaler
            return Pipeline([
                ("scale", StandardScaler()),
                ("clf", LogisticRegression(max_iter=2000, C=1.0)),
            ])
        if self.algo == "lightgbm":
            try:
                from lightgbm import LGBMClassifier
            except ImportError as e:
                raise ImportError(
                    "lightgbm not installed. `pip install -e \".[models]\"` "
                    "or use algo='logistic'."
                ) from e
            return LGBMClassifier(
                n_estimators=400, learning_rate=0.03, num_leaves=31,
                subsample=0.8, colsample_bytree=0.8,
                random_state=self.random_state, verbose=-1,
            )
        raise ValueError(f"unknown algo: {self.algo}")

    def _prepare(self, X, fit: bool = False):
        import pandas as pd
        cols = self.feature_cols or list(X.columns)
        Xd = X[cols].astype(float).copy()
        if fit:
            self._imputer_means = {c: float(Xd[c].mean()) for c in cols}
        for c in cols:
            Xd[c] = Xd[c].fillna(self._imputer_means.get(c, 0.0))
        return Xd

    # ---- Predictor API ---------------------------------------------
    def fit(self, X, y):
        import numpy as np
        if self.feature_cols is None:
            self.feature_cols = list(X.columns)
        Xd = self._prepare(X, fit=True)
        yv = np.asarray(y).astype(int)

        if self.calibrate and len(Xd) > 200:
            # Time-ordered tail: rows arrive chronologically, so the LAST slice
            # is the future relative to the rest. A random split would leak.
            cut = int(len(Xd) * (1.0 - self.calibration_tail))
            Xf, yf = Xd.iloc[:cut], yv[:cut]
            Xc, yc = Xd.iloc[cut:], yv[cut:]
            self._model = self._make_estimator()
            self._model.fit(Xf, yf)
            from sklearn.isotonic import IsotonicRegression
            raw = self._model.predict_proba(Xc)[:, 1]
            self._calibrator = IsotonicRegression(out_of_bounds="clip")
            self._calibrator.fit(raw, yc)
        else:
            self._model = self._make_estimator()
            self._model.fit(Xd, yv)
            self._calibrator = None
        return self

    def predict_proba(self, X):
        if self._model is None:
            raise RuntimeError("model is not fitted")
        Xd = self._prepare(X)
        raw = self._model.predict_proba(Xd)[:, 1]
        if self._calibrator is not None:
            raw = self._calibrator.predict(raw)
        return [float(min(max(p, 1e-6), 1 - 1e-6)) for p in raw]

    def predict(self, X):
        return self.predict_proba(X)

    def predict_match(self, mf: MatchFeatures) -> OutcomePrediction:
        import pandas as pd
        row = pd.DataFrame([{c: mf.features.get(c) for c in (self.feature_cols or [])}])
        return OutcomePrediction(match_id=mf.match_id,
                                 p_a_win=self.predict_proba(row)[0],
                                 model_version=self.version)

    # ---- persistence -----------------------------------------------
    def save(self, path: str | Path):
        import joblib
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        return path

    @classmethod
    def load(cls, path: str | Path):
        import joblib
        return joblib.load(path)
