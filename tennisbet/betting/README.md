# betting

Compares calibrated model probabilities against de-vigged bookmaker odds and
flags value bets with a staking plan.

In: `OutcomePrediction` + `OddsSnapshot`. Out: `ValueBet`.
`odds_utils` and `staking` are pure/tested; `value.py` wires them together.
Run standalone: `python -m tennisbet value`.
