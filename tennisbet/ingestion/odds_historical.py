"""Historical ATP odds from tennis-data.co.uk (free, 2001-present).

Per-season Excel files. Odds columns of interest:

    PSW / PSL    Pinnacle       — sharpest book; the closest thing to a true
                                  closing line in a free dataset
    B365W/B365L  Bet365         — softer, wider margin
    MaxW / MaxL  best available across books (Oddsportal)
    AvgW / AvgL  market average

**Honest caveat about "closing".** The site states odds "generally represent the
most recent before play starts". That is *approximately* closing, not verified
closing. Any CLV number computed from it inherits that uncertainty — treat
results as indicative, not as a settled answer. Pinnacle coverage also thins out
in the early years.

Columns are winner/loser oriented (like Sackmann), so the loader carries both
names through and `linking` maps them onto canonical player_a/player_b.
"""
from __future__ import annotations

from pathlib import Path

BASE_URL = "http://www.tennis-data.co.uk"

# bookmaker -> (winner column, loser column)
BOOKMAKERS = {
    "pinnacle": ("PSW", "PSL"),
    "bet365": ("B365W", "B365L"),
    "max": ("MaxW", "MaxL"),
    "avg": ("AvgW", "AvgL"),
}

SERIES_TIER = {
    "grand slam": "GrandSlam",
    "masters 1000": "ATP1000",
    "masters": "ATP1000",
    "atp500": "ATP500",
    "international gold": "ATP500",
    "atp250": "ATP250",
    "international": "ATP250",
}

# Not standard ATP250+ singles draws.
EXCLUDED_SERIES = {"masters cup", "atp finals", "tour finals"}


def season_url(year: int) -> str:
    ext = "xlsx" if year >= 2013 else "xls"
    return f"{BASE_URL}/{year}/{year}.{ext}"


def classify_series(series: str) -> str | None:
    s = str(series or "").strip().lower()
    if not s or any(x in s for x in EXCLUDED_SERIES):
        return None
    for key, tier in SERIES_TIER.items():
        if key in s:
            return tier
    return None


def load_season(year: int, cache_dir: str | Path = "data/raw/tennisdata",
                local_dir: str | Path | None = None):
    """Return the raw season DataFrame, downloading+caching if needed."""
    import pandas as pd
    fname = f"{year}.{'xlsx' if year >= 2013 else 'xls'}"
    if local_dir:
        p = Path(local_dir) / fname
        if not p.exists():
            return pd.DataFrame()
        return pd.read_excel(p)
    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / fname
    if not path.exists():
        import urllib.request
        req = urllib.request.Request(season_url(year),
                                     headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                path.write_bytes(r.read())
        except Exception:
            return pd.DataFrame()
    return pd.read_excel(path)


def normalize_odds_frame(raw):
    """Raw tennis-data season -> canonical odds records (still winner/loser)."""
    import pandas as pd
    if raw is None or len(raw) == 0:
        return pd.DataFrame()
    df = raw.copy()
    df.columns = [str(c).strip() for c in df.columns]

    out = pd.DataFrame({
        "odds_date": pd.to_datetime(df.get("Date"), errors="coerce"),
        "tournament": df.get("Tournament"),
        "location": df.get("Location"),
        "series": df.get("Series"),
        "surface": df.get("Surface", pd.Series(dtype=object)).astype(str).str.lower(),
        "round": df.get("Round"),
        "best_of": pd.to_numeric(df.get("Best of"), errors="coerce"),
        "winner_name": df.get("Winner"),
        "loser_name": df.get("Loser"),
        "comment": df.get("Comment"),
    })
    for book, (wc, lc) in BOOKMAKERS.items():
        out[f"odds_w_{book}"] = pd.to_numeric(df.get(wc), errors="coerce")
        out[f"odds_l_{book}"] = pd.to_numeric(df.get(lc), errors="coerce")

    out["tier"] = out["series"].map(classify_series)
    out = out[out["tier"].notna()]
    out = out[out["odds_date"].notna()]
    out = out[out["winner_name"].notna() & out["loser_name"].notna()]
    return out.reset_index(drop=True)


def load_odds(years, cache_dir: str | Path = "data/raw/tennisdata",
              local_dir: str | Path | None = None):
    import pandas as pd
    frames = []
    for y in years:
        f = normalize_odds_frame(load_season(y, cache_dir, local_dir))
        if len(f):
            f["season"] = y
            frames.append(f)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
