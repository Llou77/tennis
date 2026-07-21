from datetime import date

from tennisbet.core.contracts import (
    ALLOWED_TIERS, MatchFeatures, PlayerRef, RawMatch, Surface, Tier,
)


def test_allowed_tiers():
    assert Tier.ATP250 in ALLOWED_TIERS
    assert len(ALLOWED_TIERS) == 4


def test_rawmatch_defaults():
    m = RawMatch(
        match_id="x", tournament="Test Open", tier=Tier.ATP500,
        surface=Surface.HARD, round="R32", match_date=date(2026, 1, 1),
        player_a=PlayerRef("a", "A"), player_b=PlayerRef("b", "B"),
    )
    assert m.best_of == 3 and m.winner_id is None


def test_matchfeatures():
    mf = MatchFeatures(match_id="x", features={"elo_diff": 42.0})
    assert mf.features["elo_diff"] == 42.0
