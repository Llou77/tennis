from datetime import datetime

from tennisbet.core.contracts import OddsSnapshot, OutcomePrediction
from tennisbet.betting.value import expected_value, make_value_bet


def test_expected_value():
    assert expected_value(0.5, 2.0) == 0.0
    assert expected_value(0.6, 2.0) > 0


def test_make_value_bet_flags_edge():
    pred = OutcomePrediction(match_id="m1", p_a_win=0.65)
    odds = OddsSnapshot(match_id="m1", bookmaker="test",
                        decimal_a=2.0, decimal_b=2.0, captured_at=datetime.utcnow())
    vb = make_value_bet(pred, odds, min_edge=0.03)
    assert vb is not None and vb.side == "a" and vb.edge > 0


def test_make_value_bet_none_when_no_edge():
    pred = OutcomePrediction(match_id="m2", p_a_win=0.50)
    odds = OddsSnapshot(match_id="m2", bookmaker="test",
                        decimal_a=1.95, decimal_b=1.95, captured_at=datetime.utcnow())
    assert make_value_bet(pred, odds, min_edge=0.03) is None
