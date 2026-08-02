import numpy as np
import pandas as pd
import pytest

from tennisbet.evaluation.metrics import log_loss
from tennisbet.models.outcome.baseline import EloBaseline, RankBaseline
from tennisbet.models.outcome.model import OutcomeModel


def synthetic(n=3000, seed=0):
    rng = np.random.default_rng(seed)
    diff = rng.normal(0, 200, n)
    p = 1 / (1 + 10 ** (-diff / 400))
    y = rng.binomial(1, p)
    return pd.DataFrame({
        "elo_diff": diff,
        "elo_blend_prob_a": p,
        "rank_a": rng.integers(1, 200, n).astype(float),
        "rank_b": rng.integers(1, 200, n).astype(float),
    }), y


def test_elo_baseline_passthrough():
    X, y = synthetic()
    m = EloBaseline().fit(X, y)
    assert m.predict_proba(X) == list(X["elo_blend_prob_a"])


def test_rank_baseline_directionality():
    X = pd.DataFrame({"rank_a": [1.0, 100.0], "rank_b": [100.0, 1.0]})
    p = RankBaseline().predict_proba(X)
    assert p[0] > 0.5 > p[1]  # better rank (lower number) favoured


def test_model_learns_signal():
    X, y = synthetic()
    m = OutcomeModel(feature_cols=["elo_diff"], calibrate=False).fit(X, y)
    p = m.predict_proba(X)
    assert log_loss(y, p) < log_loss(y, [0.5] * len(y))


def test_model_beats_nothing_on_noise():
    """Sanity: with a pure-noise feature the model must NOT beat the base rate
    by much — catches accidental label leakage in the plumbing."""
    rng = np.random.default_rng(1)
    X = pd.DataFrame({"noise": rng.normal(0, 1, 2000)})
    y = rng.binomial(1, 0.5, 2000)
    m = OutcomeModel(feature_cols=["noise"], calibrate=False).fit(X, y)
    assert log_loss(y, m.predict_proba(X)) > 0.68  # ~ln(2)


def test_probabilities_in_range():
    X, y = synthetic()
    m = OutcomeModel(feature_cols=["elo_diff"]).fit(X, y)
    assert all(0.0 < p < 1.0 for p in m.predict_proba(X))


def test_nan_features_are_imputed():
    X, y = synthetic(500)
    X.loc[0:10, "elo_diff"] = np.nan
    m = OutcomeModel(feature_cols=["elo_diff"], calibrate=False).fit(X, y)
    assert not any(p != p for p in m.predict_proba(X))


def test_unfitted_model_raises():
    with pytest.raises(RuntimeError):
        OutcomeModel(feature_cols=["elo_diff"]).predict_proba(pd.DataFrame({"elo_diff": [0.0]}))


def test_save_load_roundtrip(tmp_path):
    X, y = synthetic(800)
    m = OutcomeModel(feature_cols=["elo_diff"]).fit(X, y)
    p1 = m.predict_proba(X.head(20))
    m.save(tmp_path / "m.joblib")
    p2 = OutcomeModel.load(tmp_path / "m.joblib").predict_proba(X.head(20))
    assert p1 == p2
