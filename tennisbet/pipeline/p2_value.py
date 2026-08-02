"""P2: does the model beat the closing line?

    matches -> Elo features -> walk-forward OUT-OF-SAMPLE probabilities
            -> link odds    -> de-vig -> compare -> simulate betting

Crucial discipline: the probabilities scored here are produced **out of sample**
by the same walk-forward protocol as P1. Backtesting on in-sample predictions is
the classic way to invent an edge that evaporates the moment real money is on it.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..betting.backtest import BacktestResult, run_backtest, run_null_test
from ..evaluation.walkforward import season_folds
from ..models.outcome.model import OutcomeModel
from .p1_baseline import ELO_FEATURES, P1Config, prepare


@dataclass
class P2Config:
    start_season: int = 2015
    end_season: int | None = None
    book: str = "pinnacle"
    min_edge: float = 0.03
    kelly_fraction: float = 0.25
    max_stake: float = 0.05
    algo: str = "logistic"
    use_baseline: bool = False   # score raw Elo instead of a fitted model


def out_of_sample_probs(data, cfg: P2Config):
    """Walk-forward predictions for every evaluated season. Never in-sample."""
    import pandas as pd
    frames = []
    for season, train, test in season_folds(data, cfg.start_season, cfg.end_season):
        t = test.copy()
        if cfg.use_baseline:
            t["model_p_a"] = t["elo_blend_prob_a"]
        else:
            model = OutcomeModel(feature_cols=ELO_FEATURES, algo=cfg.algo)
            model.fit(train[ELO_FEATURES], train["label_winner"])
            t["model_p_a"] = model.predict_proba(t[ELO_FEATURES])
        frames.append(t)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def run(matches_with_odds, cfg: P2Config | None = None) -> dict:
    cfg = cfg or P2Config()
    data, _ = prepare(matches_with_odds, P1Config(start_season=cfg.start_season))
    scored = out_of_sample_probs(data, cfg)
    if len(scored) == 0:
        return {"error": "no seasons could be evaluated (not enough history)"}

    kw = dict(book=cfg.book, min_edge=cfg.min_edge,
              kelly_fraction=cfg.kelly_fraction, max_stake=cfg.max_stake)
    return {
        "n_scored": len(scored),
        "result": run_backtest(scored, prob_col="model_p_a", **kw),
        "null": run_null_test(scored, **kw),
    }


def format_report(out: dict) -> str:
    if "error" in out:
        return f"P2 failed: {out['error']}"
    res: BacktestResult = out["result"]
    null: BacktestResult = out["null"]
    lines = ["=== P2: model vs closing line ===", "", res.format(), "",
             "--- null test (market scored against itself) ---",
             f"bets: {null.n_bets}  roi: {null.roi:+.2%}"]
    lines.append("null test OK — harness is not manufacturing edge."
                 if null.n_bets == 0 else
                 "WARNING: null test found bets. The backtest is buggy; ignore all results above.")
    if res.by_season:
        lines += ["", f"{'season':<10}{'matches':>9}{'bets':>7}{'roi':>10}"]
        for s, v in res.by_season.items():
            lines.append(f"{str(s):<10}{v['n']:>9,}{v['bets']:>7}{v['roi']:>+10.2%}")
    return "\n".join(lines)
