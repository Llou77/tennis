"""Synthetic ATP-shaped tour generator.

Why this exists: the real dataset needs network access, but the pipeline must be
verifiable anywhere (CI, an offline laptop, a locked-down sandbox). This builds a
fake tour with a KNOWN latent skill structure, so tests can assert that the
pipeline actually recovers signal — and, just as importantly, that it does NOT
find signal where none exists.

It emits the same canonical schema as `historical_sackmann.build_match_table`.
"""
from __future__ import annotations

import datetime as _dt

SURFACES = ["hard", "clay", "grass"]
TIERS = ["ATP250", "ATP500", "ATP1000", "GrandSlam"]
_TIER_P = [0.55, 0.2, 0.18, 0.07]


def generate(n_players: int = 200, seasons: tuple[int, int] = (2010, 2024),
             matches_per_season: int = 2200, seed: int = 42):
    """Return (df, truth) where truth holds the latent skills used to generate."""
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(seed)
    pids = [f"P{i:04d}" for i in range(n_players)]

    # Latent skill: overall + per-surface deviation. Elo should approximate this.
    skill = rng.normal(0.0, 1.0, n_players)
    surf_dev = {s: rng.normal(0.0, 0.45, n_players) for s in SURFACES}
    # Slow career arc so ratings have something to track over time.
    drift = rng.normal(0.0, 0.05, n_players)

    rows = []
    y0, y1 = seasons
    for season in range(y0, y1 + 1):
        t = season - y0
        eff = skill + drift * t
        for m in range(matches_per_season):
            i, j = rng.choice(n_players, size=2, replace=False)
            surf = SURFACES[rng.choice(len(SURFACES), p=[0.55, 0.33, 0.12])]
            tier = TIERS[rng.choice(len(TIERS), p=_TIER_P)]
            best_of = 5 if tier == "GrandSlam" else 3

            si = eff[i] + surf_dev[surf][i]
            sj = eff[j] + surf_dev[surf][j]
            p_i = 1.0 / (1.0 + np.exp(-(si - sj)))
            i_won = bool(rng.random() < p_i)

            a_id, b_id = (pids[i], pids[j]) if pids[i] < pids[j] else (pids[j], pids[i])
            a_is_i = a_id == pids[i]
            label = int(i_won == a_is_i)

            # Closeness: tighter matches when skills are near-equal.
            gap = abs(si - sj)
            sets_needed = 3 if best_of == 5 else 2
            loser_sets = int(rng.random() < max(0.05, 0.45 - 0.15 * gap)) + \
                         (1 if best_of == 5 and rng.random() < max(0.03, 0.25 - 0.1 * gap) else 0)
            loser_sets = min(loser_sets, sets_needed - 1)
            n_sets = sets_needed + loser_sets
            gw = 6 * sets_needed + int(rng.integers(0, 3))
            gl = int(round(6 * loser_sets + max(0, rng.normal(3.4 - 0.5 * gap, 1.2)) * sets_needed))
            gl = max(0, min(gl, gw - 1))

            day = _dt.date(season, 1, 1) + _dt.timedelta(days=int(rng.integers(0, 330)))
            rows.append({
                "match_id": f"S{season}-{m}",
                "tourney_id": f"S{season}-T{m // 60}",
                "tourney_name": f"Synthetic {tier} {m // 60}",
                "tier": tier, "surface": surf, "draw_size": 32,
                "round": "R32", "best_of": best_of, "match_date": day,
                "player_a_id": a_id, "player_b_id": b_id,
                "player_a_name": a_id, "player_b_name": b_id,
                "winner_id": pids[i] if i_won else pids[j],
                "label_winner": label,
                "score": "", "retired": False, "walkover": False, "completed": True,
                "minutes": float(60 + 20 * n_sets),
                "rank_a": None, "rank_b": None,
                "games_a": gw if label == 1 else gl,
                "games_b": gl if label == 1 else gw,
                "sets_a": sets_needed if label == 1 else loser_sets,
                "sets_b": loser_sets if label == 1 else sets_needed,
                "total_games": gw + gl,
            })

    df = pd.DataFrame(rows)
    df["match_date"] = pd.to_datetime(df["match_date"])
    df = df.sort_values(["match_date", "match_id"]).reset_index(drop=True)
    # Rank proxy derived from latent skill (lower number = stronger), as the real
    # feed would provide. Deliberately noisy.
    order = {pid: r + 1 for r, pid in enumerate(
        sorted(pids, key=lambda p: -skill[pids.index(p)]))}
    df["rank_a"] = df["player_a_id"].map(order).astype(float)
    df["rank_b"] = df["player_b_id"].map(order).astype(float)
    truth = pd.DataFrame({"player_id": pids, "skill": skill})
    return df, truth
