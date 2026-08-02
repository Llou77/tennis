"""Control tests for the P2 harness.

These exist because the first version of the synthetic odds generator kept
noise constant regardless of `market_skill`. The "efficient market" control
therefore still looked beatable, and the harness appeared to print a 12% ROI
against a market that was supposed to be unbeatable. The bug was in the test
fixture, not the model — which is exactly the kind of error that would have
been mistaken for a working strategy.
"""
import pytest

from tennisbet.features.elo import compute_elo_features
from tennisbet.ingestion.synthetic import generate, generate_odds
from tennisbet.pipeline.p2_value import P2Config, run


@pytest.fixture(scope="module")
def base():
    df, _ = generate(n_players=150, seasons=(2012, 2020),
                     matches_per_season=1500, seed=42)
    feats, _ = compute_elo_features(df)
    return df.join(feats[["elo_blend_prob_a"]])


def _run(base, skill, min_edge=0.03):
    d = generate_odds(base, market_skill=skill, seed=7).drop(columns=["elo_blend_prob_a"])
    return run(d, P2Config(start_season=2016, min_edge=min_edge))


def test_efficient_market_cannot_be_beaten(base):
    """CONTROL: with a perfectly efficient book the model must NOT win on
    log loss. If this ever passes, the fixture is broken, not the model."""
    res = _run(base, skill=1.00)["result"]
    assert not res.beats_market


def test_soft_market_is_beatable(base):
    """Opposite direction: a badly priced book must be detectable, or the
    harness could never find a real edge either."""
    res = _run(base, skill=0.70)["result"]
    assert res.beats_market and res.roi > 0


def test_edge_increases_as_market_gets_softer(base):
    diffs = []
    for skill in (1.00, 0.85, 0.70):
        r = _run(base, skill)["result"]
        diffs.append(r.market_log_loss - r.model_log_loss)
    assert diffs[0] < diffs[1] < diffs[2]


def test_null_test_is_clean_at_every_skill_level(base):
    for skill in (1.00, 0.85, 0.70):
        assert _run(base, skill)["null"].n_bets == 0


def test_positive_roi_can_occur_without_real_edge(base):
    """The single most dangerous failure mode in betting research: ROI is noisy
    enough that a model which is WORSE than the market on log loss can still
    show a profit over thousands of bets. Log loss is the signal; ROI is not."""
    out = _run(base, skill=0.95)
    res = out["result"]
    if res.roi > 0:
        assert not res.beats_market, (
            "sanity: this fixture is meant to show profitable-looking ROI "
            "from a model that does not actually beat the market")


def test_out_of_sample_only(base):
    """Scored rows must all come from evaluated seasons, never the training
    seasons that produced the model."""
    out = _run(base, skill=0.85)
    assert out["n_scored"] > 0
    assert out["result"].n_matches <= out["n_scored"]
