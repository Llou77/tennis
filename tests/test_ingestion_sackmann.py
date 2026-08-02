import csv
from pathlib import Path

from tennisbet.core.contracts import ALLOWED_TIERS, Tier
from tennisbet.ingestion.historical_sackmann import (
    build_match_table, normalize, to_raw_match,
)
from tennisbet.ingestion.tiers import classify_tier

FIXTURE = Path(__file__).parent / "fixtures" / "atp_matches_sample.csv"


def rows():
    with FIXTURE.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_tier_classification():
    assert classify_tier("G", "Australian Open") is Tier.GRAND_SLAM
    assert classify_tier("M", "Indian Wells") is Tier.ATP1000
    assert classify_tier("A", "Brisbane") is Tier.ATP250
    assert classify_tier("A", "Rotterdam") is Tier.ATP500
    # team events and out-of-scope levels are dropped
    assert classify_tier("A", "United Cup") is None
    assert classify_tier("F", "Tour Finals") is None
    assert classify_tier("D", "Davis Cup") is None


def test_united_cup_filtered_out():
    names = {normalize(r)["tourney_name"] for r in rows() if normalize(r)}
    assert "United Cup" not in names


def test_all_kept_matches_are_in_scope():
    for r in rows():
        rec = normalize(r)
        if rec is not None:
            assert Tier(rec["tier"]) in ALLOWED_TIERS


def test_canonical_player_order_is_not_winner_first():
    """player_a must be the lower player_id, NOT the winner."""
    for r in rows():
        rec = normalize(r)
        if rec is None:
            continue
        assert rec["player_a_id"] < rec["player_b_id"]
        expected = 1 if rec["winner_id"] == rec["player_a_id"] else 0
        assert rec["label_winner"] == expected


def test_label_is_not_constant():
    labels = [normalize(r)["label_winner"] for r in rows() if normalize(r)]
    assert set(labels) == {0, 1}, "canonical ordering should produce both labels"


def test_walkover_and_retirement_flags():
    recs = {normalize(r)["match_id"]: normalize(r) for r in rows() if normalize(r)}
    wo = recs["2024-0339-288"]
    assert wo["walkover"] and not wo["completed"] and wo["total_games"] is None
    ret = recs["2024-0339-277"]
    assert ret["retired"] and not ret["completed"]


def test_closeness_raw_material():
    rec = [normalize(r) for r in rows() if normalize(r) and normalize(r)["match_id"] == "2024-0339-300"][0]
    # Dimitrov 7-6 6-4 over Rune -> winner 13 games, loser 10
    assert rec["total_games"] == 23
    winner_games = rec["games_a"] if rec["label_winner"] == 1 else rec["games_b"]
    assert winner_games == 13


def test_post_stats_are_prefixed():
    rec = normalize(rows()[0])
    assert any(k.startswith("post_") for k in rec)
    # no un-prefixed serve stat leaked into the record
    assert "w_ace" not in rec and "ace_a" not in rec


def test_build_table_is_chronological():
    df = build_match_table(rows())
    assert len(df) > 0
    assert df["match_date"].is_monotonic_increasing


def test_to_raw_match_contract():
    rec = normalize(rows()[0])
    m = to_raw_match(rec)
    assert m.tier in ALLOWED_TIERS
    assert m.winner_id in (m.player_a.player_id, m.player_b.player_id)
