import math

import numpy as np
import pandas as pd
import pytest

from tennisbet.betting.backtest import devig_pair, run_backtest, run_null_test


def market(n=4000, seed=0, vig=0.05, model_noise=0.0, market_bias=0.0):
    """Simulated two-way market.

    `market_bias` shifts the bookmaker's opinion away from the truth in log-odds
    space — that mispricing is the ONLY thing a true-probability model can
    profit from. With bias 0 and proportional vig, de-vigging recovers the true
    probability exactly, so a perfect model ties the market and finds no bets.
    That is the correct answer, not a bug: an efficient market cannot be beaten
    by knowing what it already knows.
    """
    rng = np.random.default_rng(seed)
    p_true = np.clip(rng.beta(2.5, 2.5, n), 0.10, 0.90)
    y = rng.binomial(1, p_true)

    logit_t = np.log(p_true / (1 - p_true))
    p_book = 1 / (1 + np.exp(-(logit_t + rng.normal(market_bias, abs(market_bias), n))
                             )) if market_bias else p_true
    over = 1.0 + vig
    odds_a = 1.0 / (p_book * over)
    odds_b = 1.0 / ((1 - p_book) * over)

    p_model = (1 / (1 + np.exp(-(logit_t + rng.normal(0, model_noise, n))))
               if model_noise > 0 else p_true)
    return pd.DataFrame({
        "label_winner": y, "odds_a_pinnacle": odds_a, "odds_b_pinnacle": odds_b,
        "model_p_a": p_model, "season": rng.integers(2015, 2021, n),
    })


def test_devig_sums_to_one():
    fa, fb = devig_pair(2.0, 2.0)
    assert math.isclose(fa + fb, 1.0) and math.isclose(fa, 0.5)


def test_devig_rejects_garbage():
    for bad in [(0, 2.0), (None, 2.0), (float("nan"), 2.0), (1.0, 2.0)]:
        assert devig_pair(*bad) is None


def test_null_test_produces_no_edge():
    """The harness's own self-check: a market cannot beat itself."""
    res = run_null_test(market())
    assert res.n_bets == 0
    assert abs(res.roi) < 1e-9


def test_efficient_market_offers_no_edge_even_to_a_perfect_model():
    """Knowing the true probability is worthless if the market already does."""
    res = run_backtest(market(n=20000, vig=0.05, market_bias=0.0), min_edge=0.02)
    assert res.n_bets == 0
    assert math.isclose(res.model_log_loss, res.market_log_loss, rel_tol=1e-9)


def test_perfect_model_beats_a_biased_market():
    """If the harness cannot find edge against a demonstrably mispriced market,
    it could never find a real one either."""
    res = run_backtest(market(n=20000, vig=0.05, market_bias=0.5), min_edge=0.02)
    assert res.beats_market
    assert res.n_bets > 0 and res.roi > 0


def test_market_beats_a_noisy_model():
    res = run_backtest(market(model_noise=0.8))
    assert not res.beats_market
    assert "does NOT beat the market" in res.format()


def test_vig_removal_is_real():
    """Zero vig + efficient market + true model -> no manufactured edge."""
    assert run_backtest(market(n=5000, vig=0.0), min_edge=0.01).n_bets == 0


def test_higher_min_edge_means_fewer_bets():
    df = market(n=8000, model_noise=0.3)
    assert run_backtest(df, min_edge=0.10).n_bets <= run_backtest(df, min_edge=0.02).n_bets


def test_one_bet_per_match_max():
    res = run_backtest(market(n=3000, model_noise=0.5), min_edge=0.01)
    assert res.n_bets <= res.n_matches


def test_invalid_odds_rows_are_skipped():
    df = market(n=500)
    df.loc[0:99, "odds_a_pinnacle"] = np.nan
    res = run_backtest(df)
    assert res.n_matches == 400


def test_unknown_book_raises():
    with pytest.raises(KeyError):
        run_backtest(market(n=10), book="nosuchbook")


def test_by_season_breakdown():
    res = run_backtest(market(n=3000, model_noise=0.4), min_edge=0.02)
    assert len(res.by_season) > 1 and all("roi" in v for v in res.by_season.values())


def test_stake_is_capped():
    res = run_backtest(market(n=2000, market_bias=1.5), min_edge=0.02, max_stake=0.05)
    if res.n_bets:
        assert res.staked <= res.n_bets * 0.05 + 1e-9
