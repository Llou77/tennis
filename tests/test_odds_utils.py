import math

from tennisbet.betting.odds_utils import (
    american_to_decimal, decimal_to_implied, implied_to_decimal,
    overround, remove_overround,
)
from tennisbet.betting.staking import kelly_fraction, stake_fraction


def test_decimal_implied_roundtrip():
    assert math.isclose(decimal_to_implied(2.0), 0.5)
    assert math.isclose(implied_to_decimal(0.25), 4.0)


def test_american_to_decimal():
    assert math.isclose(american_to_decimal(100), 2.0)
    assert math.isclose(american_to_decimal(-200), 1.5)


def test_overround_and_devig():
    implied = [decimal_to_implied(1.8), decimal_to_implied(2.1)]
    assert overround(implied) > 0  # bookmaker margin exists
    fair = remove_overround(implied)
    assert math.isclose(sum(fair), 1.0)


def test_kelly():
    # fair coin at even money -> zero edge -> zero stake
    assert math.isclose(kelly_fraction(0.5, 2.0), 0.0)
    # positive edge -> positive stake
    assert kelly_fraction(0.6, 2.0) > 0
    assert stake_fraction(0.6, 2.0, "fractional_kelly", 0.25) < kelly_fraction(0.6, 2.0)
