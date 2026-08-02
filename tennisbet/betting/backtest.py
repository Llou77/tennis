"""Closing-line backtest — the only test that says whether money can be made.

The headline number is NOT ROI. It is:

    model log loss   vs   de-vigged market log loss

on the same matches. If the model cannot predict better than the market's own
implied probabilities, every positive ROI you see is noise or a bug. ROI on a
few hundred bets has enormous variance; the log-loss comparison does not.

What is deliberately made hard here:

* **The vig is always removed** before comparing. Raw implied probabilities sum
  to ~1.05; comparing against those manufactures fake edge out of thin air.
* **You bet at the posted price**, but are scored against the de-vigged fair
  probability. That asymmetry is real and is what makes betting hard.
* **A null test ships with it** (`run_null_test`): feed the market's own
  probabilities back in as if they were the model. A correct backtest returns
  ~0% ROI. Anything meaningfully positive means the harness is lying to you.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .odds_utils import decimal_to_implied, remove_overround
from .staking import stake_fraction


@dataclass
class BacktestResult:
    n_matches: int = 0
    n_bets: int = 0
    staked: float = 0.0
    profit: float = 0.0
    model_log_loss: float = float("nan")
    market_log_loss: float = float("nan")
    model_brier: float = float("nan")
    market_brier: float = float("nan")
    mean_edge: float = 0.0
    hit_rate: float = float("nan")
    by_season: dict = field(default_factory=dict)

    @property
    def roi(self) -> float:
        return self.profit / self.staked if self.staked else 0.0

    @property
    def beats_market(self) -> bool:
        """The bar. Everything else is commentary."""
        return self.model_log_loss < self.market_log_loss

    def format(self) -> str:
        edge = self.market_log_loss - self.model_log_loss
        lines = [
            f"matches evaluated : {self.n_matches:,}",
            f"model  log loss   : {self.model_log_loss:.4f}",
            f"market log loss   : {self.market_log_loss:.4f}   (de-vigged closing)",
            f"difference        : {edge:+.4f}  "
            f"({'model better' if edge > 0 else 'MARKET BETTER'})",
            f"model  brier      : {self.model_brier:.4f}",
            f"market brier      : {self.market_brier:.4f}",
            "",
            f"bets placed       : {self.n_bets:,}",
            f"staked (units)    : {self.staked:,.1f}",
            f"profit (units)    : {self.profit:+,.1f}",
            f"ROI               : {self.roi:+.2%}",
            f"hit rate          : {self.hit_rate:.1%}" if self.n_bets else "hit rate          : -",
            f"mean edge on bets : {self.mean_edge:+.3f}",
        ]
        if not self.beats_market:
            lines += ["", "The model does NOT beat the market on log loss.",
                      "Any positive ROI above is noise. Do not bet this."]
        return "\n".join(lines)


def devig_pair(odds_a: float, odds_b: float) -> tuple[float, float] | None:
    """Two-way market -> fair probabilities summing to 1."""
    try:
        if not odds_a or not odds_b or odds_a <= 1.0 or odds_b <= 1.0:
            return None
        if odds_a != odds_a or odds_b != odds_b:  # NaN
            return None
    except TypeError:
        return None
    fa, fb = remove_overround([decimal_to_implied(odds_a), decimal_to_implied(odds_b)])
    return fa, fb


def run_backtest(df, prob_col: str = "model_p_a", book: str = "pinnacle",
                 min_edge: float = 0.03, staking: str = "fractional_kelly",
                 kelly_fraction: float = 0.25, label_col: str = "label_winner",
                 max_stake: float = 0.05) -> BacktestResult:
    """Score model probabilities against the closing line and simulate betting.

    One unit of bankroll is assumed constant (no compounding), so ROI is not
    flattered by a lucky early run.
    """
    import math

    res = BacktestResult()
    model_ll: list[float] = []
    market_ll: list[float] = []
    model_bs: list[float] = []
    market_bs: list[float] = []
    edges: list[float] = []
    wins = 0
    season_stats: dict = {}

    oa_col, ob_col = f"odds_a_{book}", f"odds_b_{book}"
    if oa_col not in df.columns:
        raise KeyError(f"no odds column '{oa_col}' — available books differ")

    for r in df.itertuples(index=False):
        fair = devig_pair(getattr(r, oa_col), getattr(r, ob_col))
        if fair is None:
            continue
        fa, _fb = fair
        p = float(getattr(r, prob_col))
        y = int(getattr(r, label_col))
        res.n_matches += 1

        eps = 1e-15
        model_ll.append(-(y * math.log(max(p, eps)) + (1 - y) * math.log(max(1 - p, eps))))
        market_ll.append(-(y * math.log(max(fa, eps)) + (1 - y) * math.log(max(1 - fa, eps))))
        model_bs.append((p - y) ** 2)
        market_bs.append((fa - y) ** 2)

        season = getattr(r, "season", None)
        st = season_stats.setdefault(season, {"n": 0, "bets": 0, "staked": 0.0, "profit": 0.0})
        st["n"] += 1

        # Bet the side where the model disagrees enough with the fair price.
        for side, model_p, fair_p, odds, won in (
            ("a", p, fa, getattr(r, oa_col), y == 1),
            ("b", 1 - p, 1 - fa, getattr(r, ob_col), y == 0),
        ):
            edge = model_p - fair_p
            if edge <= min_edge:
                continue
            f = min(stake_fraction(model_p, float(odds), staking, kelly_fraction), max_stake)
            if f <= 0:
                continue
            pnl = f * (float(odds) - 1.0) if won else -f
            res.n_bets += 1
            res.staked += f
            res.profit += pnl
            edges.append(edge)
            wins += int(won)
            st["bets"] += 1
            st["staked"] += f
            st["profit"] += pnl
            break  # at most one side per match

    n = len(model_ll)
    if n:
        res.model_log_loss = sum(model_ll) / n
        res.market_log_loss = sum(market_ll) / n
        res.model_brier = sum(model_bs) / n
        res.market_brier = sum(market_bs) / n
    if res.n_bets:
        res.mean_edge = sum(edges) / len(edges)
        res.hit_rate = wins / res.n_bets
    res.by_season = {
        k: {**v, "roi": (v["profit"] / v["staked"]) if v["staked"] else 0.0}
        for k, v in sorted(season_stats.items(), key=lambda kv: (kv[0] is None, kv[0]))
    }
    return res


def run_null_test(df, book: str = "pinnacle", **kw) -> BacktestResult:
    """Feed the market's own de-vigged probability back in as the 'model'.

    A correct harness produces ~0 bets and ~0% ROI: you cannot beat a market
    using nothing but that market's own opinion. If this returns real profit,
    the bug is in the backtest, not in your edge.
    """
    d = df.copy()
    fair = [devig_pair(a, b) for a, b in zip(d[f"odds_a_{book}"], d[f"odds_b_{book}"])]
    d["null_p"] = [f[0] if f else 0.5 for f in fair]
    return run_backtest(d, prob_col="null_p", book=book, **kw)
