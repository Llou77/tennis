import math

from tennisbet.features.elo import (
    EloConfig, EloEngine, compute_elo_features, expected_score,
)


def test_expected_score_symmetry():
    assert math.isclose(expected_score(1500, 1500), 0.5)
    assert math.isclose(expected_score(1600, 1500) + expected_score(1500, 1600), 1.0)
    assert expected_score(1700, 1500) > 0.5


def test_winner_gains_loser_loses():
    e = EloEngine()
    e.update("a", "b", "hard", a_won=1)
    assert e.rating("a") > 1500 and e.rating("b") < 1500


def test_zero_sum_with_equal_k():
    e = EloEngine(cfg=EloConfig(decay=False, k_fixed=32))
    e.update("a", "b", "hard", a_won=1)
    assert math.isclose(e.rating("a") + e.rating("b"), 3000.0, abs_tol=1e-9)


def test_surface_isolation():
    e = EloEngine()
    e.update("a", "b", "clay", a_won=1)
    assert e.surface_rating("a", "clay") > 1500
    assert math.isclose(e.surface_rating("a", "grass"), 1500.0)  # untouched


def test_decaying_k_shrinks_with_experience():
    e = EloEngine(cfg=EloConfig(decay=True))
    k_new = e.k("rookie")
    for _ in range(50):
        e.update("rookie", "x", "hard", a_won=1)
    assert e.k("rookie") < k_new


def test_snapshot_is_pre_match():
    """The classic leakage bug: features must not see the result."""
    e = EloEngine()
    snap = e.snapshot("a", "b", "hard")
    assert snap["elo_a"] == 1500.0 and snap["elo_prob_a"] == 0.5
    e.update("a", "b", "hard", a_won=1)
    snap2 = e.snapshot("a", "b", "hard")
    assert snap2["elo_a"] > snap["elo_a"]  # only the NEXT match sees the update


def test_compute_elo_features_no_leakage_first_row():
    import pandas as pd
    df = pd.DataFrame([
        {"player_a_id": "a", "player_b_id": "b", "surface": "hard",
         "label_winner": 1, "walkover": False},
        {"player_a_id": "a", "player_b_id": "b", "surface": "hard",
         "label_winner": 1, "walkover": False},
    ])
    feats, _ = compute_elo_features(df)
    assert feats.loc[0, "elo_diff"] == 0.0          # nothing known yet
    assert feats.loc[1, "elo_diff"] > 0.0           # first result now reflected
    assert feats.loc[0, "elo_matches_a"] == 0.0
    assert feats.loc[1, "elo_matches_a"] == 1.0


def test_walkover_does_not_move_ratings():
    import pandas as pd
    df = pd.DataFrame([
        {"player_a_id": "a", "player_b_id": "b", "surface": "hard",
         "label_winner": 1, "walkover": True},
        {"player_a_id": "a", "player_b_id": "b", "surface": "hard",
         "label_winner": 1, "walkover": False},
    ])
    feats, _ = compute_elo_features(df)
    assert feats.loc[1, "elo_diff"] == 0.0  # walkover taught us nothing
