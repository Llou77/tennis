"""Tournament tier classification for Sackmann data.

Sackmann's `tourney_level` does NOT separate ATP250 from ATP500 — both are "A".
Both are in scope, but tier is a useful feature, so we split "A" using a curated
name list. The list is approximate and shifts over the years (Doha moved 250->500
in 2024, Hamburg 500->250 in 2009 etc.); treat tier as a noisy feature, never as
a hard filter beyond in-scope/out-of-scope.
"""
from __future__ import annotations

from ..core.contracts import Tier

# Sackmann tourney_level codes
LEVEL_GRAND_SLAM = "G"
LEVEL_MASTERS = "M"
LEVEL_ATP = "A"          # 250 + 500 mixed
LEVEL_FINALS = "F"       # Tour Finals — out of scope
LEVEL_DAVIS_CUP = "D"    # out of scope

# Curated ATP500 names (lowercased substrings).
ATP500_NAMES = {
    "rotterdam", "dubai", "acapulco", "rio de janeiro", "barcelona",
    "hamburg", "washington", "beijing", "tokyo", "vienna", "basel",
    "halle", "queen's club", "queens club", "london", "astana", "doha",
    "memphis", "valencia", "kuala lumpur", "china open", "japan open",
}

# Team/exhibition/other events that carry level "A" or "G" but are NOT
# standard ATP250+ singles draws.
EXCLUDED_NAMES = {
    "united cup", "atp cup", "laver cup", "davis cup", "olympics",
    "olympic", "hopman cup", "nextgen", "next gen", "world team cup",
    "grand slam cup",
}


def is_excluded_event(tourney_name: str) -> bool:
    n = (tourney_name or "").strip().lower()
    return any(bad in n for bad in EXCLUDED_NAMES)


def classify_tier(tourney_level: str, tourney_name: str) -> Tier | None:
    """Return the Tier, or None if the event is out of scope."""
    if is_excluded_event(tourney_name):
        return None
    lvl = (tourney_level or "").strip().upper()
    if lvl == LEVEL_GRAND_SLAM:
        return Tier.GRAND_SLAM
    if lvl == LEVEL_MASTERS:
        return Tier.ATP1000
    if lvl == LEVEL_ATP:
        n = (tourney_name or "").strip().lower()
        return Tier.ATP500 if any(k in n for k in ATP500_NAMES) else Tier.ATP250
    # F (Finals), D (Davis Cup), C/S (Challenger/ITF), O (Olympics) -> out of scope
    return None
