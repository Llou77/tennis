"""Parameter-free reference models.

Before any ML, you need a number to beat. Two references:

* `EloBaseline` — take the blended-Elo probability as-is. No fitting at all.
* `RankBaseline` — the naive "higher-ranked player wins" heuristic.

If a gradient-boosted model can't beat `EloBaseline` on log loss out of sample,
the extra machinery is buying nothing and should be thrown away.
"""
from __future__ import annotations


class EloBaseline:
    """Uses a precomputed Elo probability column. `fit` is a no-op by design."""

    version = "elo-baseline-1.0"

    def __init__(self, prob_col: str = "elo_blend_prob_a"):
        self.prob_col = prob_col

    def fit(self, X, y=None):
        return self

    def predict_proba(self, X):
        return list(X[self.prob_col])


class RankBaseline:
    """Crude sanity floor: probability from ATP rank difference via a logistic
    squash. Missing ranks fall back to 0.5."""

    version = "rank-baseline-1.0"

    def __init__(self, scale: float = 0.0035):
        self.scale = scale

    def fit(self, X, y=None):
        return self

    def predict_proba(self, X):
        import math
        out = []
        for ra, rb in zip(X["rank_a"], X["rank_b"]):
            if ra is None or rb is None or ra != ra or rb != rb:
                out.append(0.5)
                continue
            # lower rank number = stronger, so B - A
            out.append(1.0 / (1.0 + math.exp(-self.scale * (float(rb) - float(ra)))))
        return out
