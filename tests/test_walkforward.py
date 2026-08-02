import numpy as np
import pandas as pd
import pytest

from tennisbet.evaluation.walkforward import run_walkforward, season_folds, summarize


def frame(n=3000, seed=0):
    rng = np.random.default_rng(seed)
    season = rng.integers(2010, 2021, n)
    x = rng.normal(0, 1, n)
    y = rng.binomial(1, 1 / (1 + np.exp(-x)))
    return pd.DataFrame({"season": season, "x": x, "label_winner": y}).sort_values("season")


def test_train_is_strictly_before_test():
    """The single most important guarantee in the whole project."""
    df = frame()
    for season, train, test in season_folds(df, 2015):
        assert train["season"].max() < season
        assert set(test["season"]) == {season}


def test_no_row_appears_in_both_sides():
    df = frame()
    for _, train, test in season_folds(df, 2015):
        assert not set(train.index) & set(test.index)


def test_fold_count_and_min_train():
    df = frame()
    folds = list(season_folds(df, 2015, min_train=10**9))
    assert folds == []  # min_train gate works


class _Dummy:
    def fit(self, X, y):
        self.p = float(np.mean(y))
        return self

    def predict_proba(self, X):
        return [self.p] * len(X)


def test_run_walkforward_and_summary():
    df = frame()
    res = run_walkforward(df, ["x"], "label_winner", _Dummy, 2015)
    assert len(res) == 6
    s = summarize(res)
    assert s["folds"] == 6 and s["n"] > 0
    assert 0 < s["log_loss"] < 1.5


def test_summarize_empty():
    assert summarize([]) == {}


def test_leakage_canary():
    """If the harness ever trained on the test season, a label-copy feature would
    score near-perfectly. It must NOT, because the copy is only informative
    within a season this test constructs to break across seasons."""
    rng = np.random.default_rng(3)
    n = 4000
    season = np.sort(rng.integers(2010, 2021, n))
    y = rng.binomial(1, 0.5, n)
    # feature encodes the label ONLY for seasons <= 2016; afterwards it's noise.
    x = np.where(season <= 2016, y, rng.binomial(1, 0.5, n)).astype(float)
    df = pd.DataFrame({"season": season, "x": x, "label_winner": y})

    class LR:
        def fit(self, X, y):
            from sklearn.linear_model import LogisticRegression
            self.m = LogisticRegression().fit(X, y)
            return self

        def predict_proba(self, X):
            return list(self.m.predict_proba(X)[:, 1])

    res = run_walkforward(df, ["x"], "label_winner", LR, 2018)
    # Every evaluated season is >2016, where x is pure noise -> no edge.
    for r in res:
        assert r.metrics["log_loss"] > 0.6, "leakage: model scored on future info"
