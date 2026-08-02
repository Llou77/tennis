"""Tennis score parsing. Pure stdlib, heavily tested.

Sackmann `score` strings look like:
    "6-4 3-6 7-6(5)"      normal
    "6-4 7-6(8)"          tiebreak with点 detail
    "W/O"                 walkover (never played)
    "6-4 2-0 RET"         retirement mid-match
    "6-4 6-4 DEF"         default
    ""/"Unfinished"       unusable

Downstream (closeness labels especially) must NOT treat walkovers and
retirements as genuine competitive results, hence the flags.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_SET_RE = re.compile(r"^(\d{1,2})-(\d{1,2})(?:\((\d{1,2})\))?$")
_ABANDON = {"RET", "RET.", "DEF", "DEF.", "W/O", "WO", "ABN", "ABD"}


@dataclass
class ParsedScore:
    """games[i] = (games won by winner, games won by loser) in set i."""
    sets: list[tuple[int, int]] = field(default_factory=list)
    walkover: bool = False
    retired: bool = False
    parseable: bool = True

    @property
    def completed(self) -> bool:
        """True only for matches played to a normal finish."""
        return self.parseable and not self.walkover and not self.retired and bool(self.sets)

    @property
    def games_winner(self) -> int:
        return sum(s[0] for s in self.sets)

    @property
    def games_loser(self) -> int:
        return sum(s[1] for s in self.sets)

    @property
    def total_games(self) -> int:
        return self.games_winner + self.games_loser

    @property
    def sets_winner(self) -> int:
        return sum(1 for a, b in self.sets if a > b)

    @property
    def sets_loser(self) -> int:
        return sum(1 for a, b in self.sets if b > a)


def parse_score(score: str | None) -> ParsedScore:
    if not score or not str(score).strip():
        return ParsedScore(parseable=False)
    raw = str(score).strip()
    upper = raw.upper()

    if "W/O" in upper or upper.strip() in {"WO", "WALKOVER"}:
        return ParsedScore(walkover=True)

    retired = any(tok in upper for tok in ("RET", "DEF", "ABN", "ABD"))
    if "UNFINISHED" in upper or "IN PROGRESS" in upper:
        return ParsedScore(parseable=False)

    sets: list[tuple[int, int]] = []
    for tok in raw.split():
        t = tok.strip().upper().rstrip(".")
        if t in _ABANDON:
            continue
        m = _SET_RE.match(tok.strip())
        if m:
            sets.append((int(m.group(1)), int(m.group(2))))
        # anything else (stray junk) is ignored rather than failing the row

    if not sets:
        return ParsedScore(parseable=False, retired=retired)
    return ParsedScore(sets=sets, retired=retired)
