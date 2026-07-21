"""End-to-end orchestration. Wires modules together ONLY through contracts,
so each stage can be run or replaced independently.

    ingest -> features -> outcome + closeness -> + odds -> value bets
                                   ^ news enrichment feeds features/state
"""
from __future__ import annotations

from typing import Iterable

from ..core.contracts import OddsSnapshot, RawMatch, ValueBet
from ..features.build import build_features
from ..models.outcome.model import OutcomeModel
from ..betting.value import make_value_bet


def run_predictions(matches: Iterable[RawMatch],
                    odds_by_match: dict[str, OddsSnapshot],
                    min_edge: float = 0.03) -> list[ValueBet]:
    """Reference wiring. Individual stages are stubbed until each module is
    implemented, but the data flow and contracts are fixed here."""
    model = OutcomeModel()
    bets: list[ValueBet] = []
    for m in matches:
        mf = build_features(m)
        pred = model.predict_match(mf)
        odds = odds_by_match.get(m.match_id)
        if odds is None:
            continue
        vb = make_value_bet(pred, odds, min_edge=min_edge)
        if vb is not None:
            bets.append(vb)
    return bets
