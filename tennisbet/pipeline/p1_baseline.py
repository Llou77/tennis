"""P1: end-to-end baseline run.

    load matches -> Elo features -> walk-forward evaluation -> comparison table

Deliberately compares every model against two parameter-free references. A
gradient-boosted model that cannot beat plain Elo out of sample is not progress.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..evaluation.walkforward import run_walkforward, summarize
from ..features.elo import EloConfig, compute_elo_features
from ..models.outcome.baseline import EloBaseline, RankBaseline
from ..models.outcome.model import OutcomeModel

ELO_FEATURES = [
    "elo_diff", "elo_surf_diff", "elo_blend_diff",
    "elo_prob_a", "elo_surf_prob_a", "elo_blend_prob_a",
    "elo_matches_a", "elo_matches_b", "elo_matches_min",
]


@dataclass
class P1Config:
    start_season: int = 2015
    end_season: int | None = None
    min_elo_matches: int = 10      # burn-in: drop matches where a player is unrated
    surface_weight: float = 0.5
    drop_incomplete: bool = True   # walkovers/retirements are not clean labels
    algos: tuple[str, ...] = ("logistic",)


def prepare(df, cfg: P1Config):
    """Attach season + Elo features. Returns the model-ready frame."""
    import pandas as pd
    d = df.copy()
    d["season"] = pd.to_datetime(d["match_date"]).dt.year
    feats, engine = compute_elo_features(
        d, EloConfig(surface_weight=cfg.surface_weight))
    d = pd.concat([d.reset_index(drop=True), feats.reset_index(drop=True)], axis=1)
    if cfg.drop_incomplete and "completed" in d.columns:
        d = d[d["completed"].fillna(False)]
    if cfg.min_elo_matches > 0:
        d = d[d["elo_matches_min"] >= cfg.min_elo_matches]
    return d.reset_index(drop=True), engine


def run(df, cfg: P1Config | None = None) -> dict:
    """Run every model through the same walk-forward protocol."""
    cfg = cfg or P1Config()
    data, _ = prepare(df, cfg)
    results: dict[str, dict] = {}

    def _eval(name, factory, cols):
        res = run_walkforward(data, cols, "label_winner", factory,
                              cfg.start_season, cfg.end_season)
        results[name] = summarize(res)

    _eval("elo_baseline", lambda: EloBaseline(), ["elo_blend_prob_a"])
    if data["rank_a"].notna().any():
        _eval("rank_baseline", lambda: RankBaseline(), ["rank_a", "rank_b"])
    for algo in cfg.algos:
        _eval(f"outcome_{algo}",
              lambda a=algo: OutcomeModel(feature_cols=ELO_FEATURES, algo=a),
              ELO_FEATURES)
    return {"n_matches": len(data), "seasons": sorted(data["season"].unique().tolist()),
            "models": results}


def format_report(out: dict) -> str:
    lines = [
        f"Matches after filtering: {out['n_matches']:,}",
        f"Seasons: {out['seasons'][0]}–{out['seasons'][-1]}" if out["seasons"] else "Seasons: -",
        "",
        f"{'model':<20}{'log_loss':>10}{'brier':>9}{'ece':>8}{'acc':>8}{'folds':>7}{'n':>9}",
        "-" * 71,
    ]
    ranked = sorted(out["models"].items(), key=lambda kv: kv[1].get("log_loss", 9e9))
    for name, m in ranked:
        if not m:
            continue
        lines.append(f"{name:<20}{m['log_loss']:>10.4f}{m['brier']:>9.4f}"
                     f"{m['ece']:>8.4f}{m['accuracy']:>8.3f}{m['folds']:>7}{m['n']:>9,}")
    lines += ["", "Lower log_loss/brier/ece is better. Accuracy is the vanity metric —",
              "it is shown last on purpose. Beating elo_baseline on log_loss is the bar."]
    return "\n".join(lines)
