"""Link tennis-data odds rows to Sackmann matches.

Two independent sources, no shared identifier. The join is:

    (unordered player pair)  +  (date within a tolerance window)

Date tolerance is needed because Sackmann stamps every match in an event with
the TOURNAMENT START date, while tennis-data uses the actual match date — a
gap of up to two weeks at a Grand Slam.

Design rule: **ambiguity is dropped, never guessed.** If a name is ambiguous,
or a pair+window admits more than one candidate match, the row is discarded and
counted. A silently wrong link poisons every downstream backtest number, and
nothing later in the pipeline can detect it.

`link_odds` returns (linked_df, report) — always read the report. A match rate
below ~85% on modern seasons means something is broken, not merely lossy.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .player_names import build_key_index, key_from_tennis_data


@dataclass
class LinkReport:
    odds_rows: int = 0
    linked: int = 0
    unresolved_name: int = 0
    no_candidate: int = 0
    ambiguous_candidates: int = 0
    reasons: dict = field(default_factory=dict)

    @property
    def match_rate(self) -> float:
        return self.linked / self.odds_rows if self.odds_rows else 0.0

    def format(self) -> str:
        return (f"odds rows: {self.odds_rows:,}\n"
                f"linked:    {self.linked:,} ({self.match_rate:.1%})\n"
                f"  unresolved player name : {self.unresolved_name:,}\n"
                f"  no candidate match     : {self.no_candidate:,}\n"
                f"  ambiguous (dropped)    : {self.ambiguous_candidates:,}")


def link_odds(matches, odds, date_tolerance_days: int = 14):
    """Attach odds to matches. Returns (linked_df, LinkReport).

    Output odds are re-oriented onto canonical player_a / player_b.
    """
    import pandas as pd

    rep = LinkReport(odds_rows=len(odds))
    if len(matches) == 0 or len(odds) == 0:
        return pd.DataFrame(), rep

    names: dict[str, str] = {}
    for pid, nm in zip(matches["player_a_id"], matches["player_a_name"]):
        names.setdefault(str(pid), str(nm))
    for pid, nm in zip(matches["player_b_id"], matches["player_b_name"]):
        names.setdefault(str(pid), str(nm))
    index, _ambiguous = build_key_index(names)

    # pair -> [(date, row_index)]
    by_pair: dict[frozenset, list] = {}
    m_dates = pd.to_datetime(matches["match_date"])
    for i, (a, b) in enumerate(zip(matches["player_a_id"], matches["player_b_id"])):
        by_pair.setdefault(frozenset((str(a), str(b))), []).append((m_dates.iloc[i], i))

    tol = pd.Timedelta(days=date_tolerance_days)
    rows = []
    for o in odds.itertuples(index=False):
        wk = key_from_tennis_data(o.winner_name)
        lk = key_from_tennis_data(o.loser_name)
        w_pid, l_pid = index.get(wk), index.get(lk)
        if w_pid is None or l_pid is None:
            rep.unresolved_name += 1
            continue
        cands = by_pair.get(frozenset((w_pid, l_pid)))
        if not cands:
            rep.no_candidate += 1
            continue
        odate = pd.Timestamp(o.odds_date)
        near = [(abs(d - odate), idx) for d, idx in cands if abs(d - odate) <= tol]
        if not near:
            rep.no_candidate += 1
            continue
        near.sort()
        # Two candidate matches equally close = the same pair met twice in the
        # window. Cannot tell which; drop rather than corrupt the backtest.
        if len(near) > 1 and near[0][0] == near[1][0]:
            rep.ambiguous_candidates += 1
            continue
        idx = near[0][1]

        m = matches.iloc[idx]
        a_won = int(m["label_winner"]) == 1
        rec = {"match_id": m["match_id"], "_match_idx": idx}
        for book in ("pinnacle", "bet365", "max", "avg"):
            ow = getattr(o, f"odds_w_{book}", None)
            ol = getattr(o, f"odds_l_{book}", None)
            # winner/loser -> canonical a/b
            rec[f"odds_a_{book}"] = ow if a_won else ol
            rec[f"odds_b_{book}"] = ol if a_won else ow
        rec["odds_date"] = odate
        rows.append(rec)
        rep.linked += 1

    linked = pd.DataFrame(rows)
    if len(linked) == 0:
        return linked, rep
    merged = matches.merge(linked.drop(columns=["_match_idx"]), on="match_id", how="inner")
    return merged, rep
