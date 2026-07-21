"""Value detection: compare calibrated model probability to de-vigged odds."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from ..core.contracts import OddsSnapshot, OutcomePrediction, ValueBet
from .odds_utils import decimal_to_implied, remove_overround
from .staking import stake_fraction


def expected_value(model_p: float, decimal_odds: float) -> float:
    """EV per unit staked."""
    return model_p * decimal_odds - 1.0


def edge_vs_implied(model_p: float, decimal_odds: float) -> float:
    return model_p - decimal_to_implied(decimal_odds)


def make_value_bet(pred: OutcomePrediction, odds: OddsSnapshot,
                   min_edge: float = 0.03, staking: str = "fractional_kelly",
                   kelly_fraction: float = 0.25) -> Optional[ValueBet]:
    """Return a ValueBet for the side with positive edge over min_edge, else None.
    De-vigs the two-way market first so the comparison is apples-to-apples."""
    fair = remove_overround([decimal_to_implied(odds.decimal_a),
                             decimal_to_implied(odds.decimal_b)])
    for side, model_p, dec in (("a", pred.p_a_win, odds.decimal_a),
                               ("b", 1.0 - pred.p_a_win, odds.decimal_b)):
        edge = model_p - fair[0 if side == "a" else 1]
        if edge > min_edge:
            return ValueBet(
                match_id=pred.match_id, side=side, bookmaker=odds.bookmaker,
                model_p=model_p, decimal_odds=dec, edge=edge,
                expected_value=expected_value(model_p, dec),
                stake_fraction=stake_fraction(model_p, dec, staking, kelly_fraction),
            )
    return None
