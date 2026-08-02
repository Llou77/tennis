"""Walk-forward evaluation.

Random train/test splits are WRONG here: they let the model train on matches
that happened after the ones it predicts, and Elo state leaks across the split.
Every evaluation trains strictly on the past and predicts the next season.

    season 2005..2019  ->  predict 2020
    season 2005..2020  ->  predict 2021
    ...
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from .metrics import evaluate


@dataclass
class FoldResult:
    season: int
    metrics: dict
    n_train: int


def season_folds(df, start_season: int, end_season: int | None = None,
                 min_train: int = 500) -> Iterable[tuple[int, "object", "object"]]:
    """Yield (season, train_df, test_df) with train strictly before test."""
    seasons = sorted(df["season"].unique())
    end_season = end_season if end_season is not None else max(seasons)
    for s in seasons:
        if s < start_season or s > end_season:
            continue
        train = df[df["season"] < s]
        test = df[df["season"] == s]
        if len(train) < min_train or len(test) == 0:
            continue
        yield int(s), train, test


def run_walkforward(df, feature_cols: list[str], label_col: str,
                    model_factory: Callable[[], object],
                    start_season: int, end_season: int | None = None,
                    min_train: int = 500) -> list[FoldResult]:
    """Fit a fresh model per fold; never reuse one across seasons."""
    results: list[FoldResult] = []
    for season, train, test in season_folds(df, start_season, end_season, min_train):
        model = model_factory()
        model.fit(train[feature_cols], train[label_col])
        probs = model.predict_proba(test[feature_cols])
        results.append(FoldResult(
            season=season,
            metrics=evaluate(list(test[label_col]), list(probs)),
            n_train=len(train),
        ))
    return results


def summarize(results: list[FoldResult]) -> dict:
    """Sample-weighted average across folds."""
    if not results:
        return {}
    total = sum(r.metrics["n"] for r in results)
    keys = ["log_loss", "brier", "ece", "accuracy"]
    out = {k: sum(r.metrics[k] * r.metrics["n"] for r in results) / total for k in keys}
    out["n"] = total
    out["folds"] = len(results)
    return out
