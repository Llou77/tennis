"""Historical ATP matches from Jeff Sackmann's open dataset.
Source: https://github.com/JeffSackmann/tennis_atp (CSV per year, CC BY-NC-SA).

This is the training backbone. Produces a canonical match table where:

  * only ATP250/500/1000/GrandSlam singles matches survive (ALLOWED_TIERS);
  * players are ordered CANONICALLY (player_a = lower player_id), so the label
    is not "the first-listed player always won" — Sackmann lists winner first,
    and training on that directly would learn nothing but column order;
  * post-match statistics are prefixed `post_` so leakage is obvious on sight.
    They may only be consumed as *prior* aggregates for later matches.
"""
from __future__ import annotations

import io
import urllib.request
from pathlib import Path
from typing import Iterable, Iterator

from ..core.contracts import ALLOWED_TIERS, PlayerRef, RawMatch, Surface, Tier
from ..core.score import parse_score
from .base import Fetcher
from .tiers import classify_tier

RAW_BASE = "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master"

# Post-match stat columns (winner-side / loser-side in the source).
_STATS = ["ace", "df", "svpt", "1stIn", "1stWon", "2ndWon", "SvGms", "bpSaved", "bpFaced"]

SURFACE_MAP = {
    "hard": Surface.HARD, "clay": Surface.CLAY,
    "grass": Surface.GRASS, "carpet": Surface.CARPET,
}


class SackmannFetcher(Fetcher):
    """Downloads (and caches) atp_matches_{year}.csv.

    `cache_dir` keeps a local copy so you only download once. If you already
    have a clone of tennis_atp, point `local_dir` at it and skip the network.
    """

    name = "sackmann"

    def __init__(self, from_year: int = 2000, to_year: int | None = None,
                 cache_dir: str | Path = "data/raw/sackmann",
                 local_dir: str | Path | None = None):
        self.from_year = from_year
        self.to_year = to_year
        self.cache_dir = Path(cache_dir)
        self.local_dir = Path(local_dir) if local_dir else None

    def years(self) -> list[int]:
        import datetime as _dt
        end = self.to_year or _dt.date.today().year
        return list(range(self.from_year, end + 1))

    def _csv_text(self, year: int) -> str | None:
        fname = f"atp_matches_{year}.csv"
        if self.local_dir is not None:
            p = self.local_dir / fname
            return p.read_text(encoding="utf-8", errors="replace") if p.exists() else None
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cached = self.cache_dir / fname
        if cached.exists():
            return cached.read_text(encoding="utf-8", errors="replace")
        url = f"{RAW_BASE}/{fname}"
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                text = r.read().decode("utf-8", errors="replace")
        except Exception:
            return None
        cached.write_text(text, encoding="utf-8")
        return text

    def fetch(self, **kwargs) -> Iterator[dict]:
        import csv
        for year in self.years():
            text = self._csv_text(year)
            if not text:
                continue
            for row in csv.DictReader(io.StringIO(text)):
                row["_year"] = year
                yield row


def _f(row: dict, key: str):
    """Float or None."""
    v = row.get(key)
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _i(row: dict, key: str):
    v = _f(row, key)
    return int(v) if v is not None else None


def _parse_date(v: str):
    import datetime as _dt
    s = str(v).strip()
    if len(s) != 8 or not s.isdigit():
        return None
    try:
        return _dt.date(int(s[:4]), int(s[4:6]), int(s[6:]))
    except ValueError:
        return None


def normalize(row: dict) -> dict | None:
    """Sackmann CSV row -> canonical flat record. None if out of scope/unusable."""
    tier = classify_tier(row.get("tourney_level", ""), row.get("tourney_name", ""))
    if tier is None or tier not in ALLOWED_TIERS:
        return None

    match_date = _parse_date(row.get("tourney_date", ""))
    if match_date is None:
        return None

    w_id, l_id = str(row.get("winner_id", "")).strip(), str(row.get("loser_id", "")).strip()
    if not w_id or not l_id or w_id == l_id:
        return None

    surface = SURFACE_MAP.get(str(row.get("surface", "")).strip().lower())
    if surface is None:
        return None

    ps = parse_score(row.get("score"))

    # CANONICAL ORDER: player_a = lexicographically smaller player_id.
    # Prevents the model from trivially learning "column 1 always wins".
    a_is_winner = w_id < l_id
    a_pref, b_pref = ("winner", "loser") if a_is_winner else ("loser", "winner")

    rec = {
        "match_id": f"{row.get('tourney_id','')}-{row.get('match_num','')}",
        "tourney_id": row.get("tourney_id", ""),
        "tourney_name": row.get("tourney_name", ""),
        "tier": tier.value,
        "surface": surface.value,
        "draw_size": _i(row, "draw_size"),
        "round": row.get("round", ""),
        "best_of": _i(row, "best_of") or 3,
        "match_date": match_date,
        "player_a_id": w_id if a_is_winner else l_id,
        "player_b_id": l_id if a_is_winner else w_id,
        "player_a_name": row.get(f"{a_pref}_name", ""),
        "player_b_name": row.get(f"{b_pref}_name", ""),
        "winner_id": w_id,
        "label_winner": 1 if a_is_winner else 0,
        "score": row.get("score", ""),
        "retired": ps.retired,
        "walkover": ps.walkover,
        "completed": ps.completed,
        "minutes": _f(row, "minutes"),
    }

    # Pre-match context (known before play): rank, points, age, hand, height.
    for side, pref in (("a", a_pref), ("b", b_pref)):
        rec[f"rank_{side}"] = _i(row, f"{pref}_rank")
        rec[f"rank_pts_{side}"] = _f(row, f"{pref}_rank_points")
        rec[f"age_{side}"] = _f(row, f"{pref}_age")
        rec[f"hand_{side}"] = row.get(f"{pref}_hand", "") or "U"
        rec[f"ht_{side}"] = _f(row, f"{pref}_ht")

    # Post-match stats — prefixed to make leakage obvious.
    wl = {"winner": "w", "loser": "l"}
    for side, pref in (("a", a_pref), ("b", b_pref)):
        for stat in _STATS:
            rec[f"post_{stat}_{side}"] = _f(row, f"{wl[pref]}_{stat}")

    # Closeness raw material (only meaningful for completed matches).
    if ps.completed:
        gw, gl = ps.games_winner, ps.games_loser
        sw, sl = ps.sets_winner, ps.sets_loser
        rec["games_a"], rec["games_b"] = (gw, gl) if a_is_winner else (gl, gw)
        rec["sets_a"], rec["sets_b"] = (sw, sl) if a_is_winner else (sl, sw)
        rec["total_games"] = ps.total_games
    else:
        rec["games_a"] = rec["games_b"] = None
        rec["sets_a"] = rec["sets_b"] = None
        rec["total_games"] = None
    return rec


def to_raw_match(rec: dict) -> RawMatch:
    """Canonical record -> the RawMatch contract object."""
    return RawMatch(
        match_id=rec["match_id"], tournament=rec["tourney_name"],
        tier=Tier(rec["tier"]), surface=Surface(rec["surface"]),
        round=rec["round"], match_date=rec["match_date"],
        player_a=PlayerRef(rec["player_a_id"], rec["player_a_name"]),
        player_b=PlayerRef(rec["player_b_id"], rec["player_b_name"]),
        best_of=rec["best_of"], winner_id=rec["winner_id"],
        score=rec["score"], retired=bool(rec["retired"]),
    )


def build_match_table(rows: Iterable[dict]):
    """Normalize rows -> chronologically sorted pandas DataFrame."""
    import pandas as pd
    recs = [r for r in (normalize(row) for row in rows) if r is not None]
    if not recs:
        return pd.DataFrame()
    df = pd.DataFrame(recs)
    df["match_date"] = pd.to_datetime(df["match_date"])
    # Chronological order is REQUIRED: Elo and every walk-forward split rely on it.
    df = df.sort_values(["match_date", "tourney_id", "match_id"]).reset_index(drop=True)
    return df
