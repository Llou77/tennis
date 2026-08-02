"""Elo ratings: overall + surface-specific.

The strongest cheap signal in tennis modeling. Two design choices worth knowing:

1. **Decaying K.** A fixed K treats a 19-year-old's 5th match like Djokovic's
   1200th. K = k_shape / (matches_played + k_offset) ** k_decay lets new players
   move fast and settle down. (FiveThirtyEight-style; defaults from that family.)
2. **Leak-free by construction.** `EloEngine.process` snapshots features BEFORE
   applying the update for that match. Ratings therefore only ever encode the
   past. Feed matches in chronological order — `build_match_table` guarantees it.

Surface Elo is kept in a separate table per surface and blended at feature time:
    blend = (1 - w) * overall + w * surface
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .base import FeatureBuilder

INITIAL_RATING = 1500.0


def expected_score(rating_a: float, rating_b: float) -> float:
    """Classic Elo expectation: P(A beats B)."""
    return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))


@dataclass
class EloConfig:
    initial: float = INITIAL_RATING
    surface_weight: float = 0.5     # blend weight on surface-specific rating
    decay: bool = True              # decaying K vs fixed
    k_fixed: float = 32.0
    k_shape: float = 250.0
    k_offset: float = 5.0
    k_decay: float = 0.4


@dataclass
class EloEngine:
    cfg: EloConfig = field(default_factory=EloConfig)
    overall: dict[str, float] = field(default_factory=dict)
    surface: dict[tuple[str, str], float] = field(default_factory=dict)
    played: dict[str, int] = field(default_factory=dict)
    played_surface: dict[tuple[str, str], int] = field(default_factory=dict)

    # ---- accessors -------------------------------------------------
    def rating(self, pid: str) -> float:
        return self.overall.get(pid, self.cfg.initial)

    def surface_rating(self, pid: str, surf: str) -> float:
        return self.surface.get((pid, surf), self.cfg.initial)

    def n_played(self, pid: str) -> int:
        return self.played.get(pid, 0)

    def k(self, pid: str) -> float:
        if not self.cfg.decay:
            return self.cfg.k_fixed
        n = self.played.get(pid, 0)
        return self.cfg.k_shape / ((n + self.cfg.k_offset) ** self.cfg.k_decay)

    def blend(self, pid: str, surf: str) -> float:
        w = self.cfg.surface_weight
        return (1.0 - w) * self.rating(pid) + w * self.surface_rating(pid, surf)

    # ---- the two halves: snapshot, then update ---------------------
    def snapshot(self, a_id: str, b_id: str, surf: str) -> dict:
        """PRE-match features. Must be called before `update`."""
        ea, eb = self.rating(a_id), self.rating(b_id)
        sa, sb = self.surface_rating(a_id, surf), self.surface_rating(b_id, surf)
        ba, bb = self.blend(a_id, surf), self.blend(b_id, surf)
        return {
            "elo_a": ea, "elo_b": eb, "elo_diff": ea - eb,
            "elo_surf_a": sa, "elo_surf_b": sb, "elo_surf_diff": sa - sb,
            "elo_blend_a": ba, "elo_blend_b": bb, "elo_blend_diff": ba - bb,
            "elo_prob_a": expected_score(ea, eb),
            "elo_surf_prob_a": expected_score(sa, sb),
            "elo_blend_prob_a": expected_score(ba, bb),
            "elo_matches_a": float(self.n_played(a_id)),
            "elo_matches_b": float(self.n_played(b_id)),
            "elo_matches_min": float(min(self.n_played(a_id), self.n_played(b_id))),
        }

    def update(self, a_id: str, b_id: str, surf: str, a_won: int) -> None:
        """Apply the result. Overall and surface tables move independently."""
        sa = float(a_won)
        # overall
        ea = expected_score(self.rating(a_id), self.rating(b_id))
        ka, kb = self.k(a_id), self.k(b_id)
        ra, rb = self.rating(a_id), self.rating(b_id)
        self.overall[a_id] = ra + ka * (sa - ea)
        self.overall[b_id] = rb + kb * ((1.0 - sa) - (1.0 - ea))
        # surface
        esa = expected_score(self.surface_rating(a_id, surf), self.surface_rating(b_id, surf))
        rsa, rsb = self.surface_rating(a_id, surf), self.surface_rating(b_id, surf)
        self.surface[(a_id, surf)] = rsa + ka * (sa - esa)
        self.surface[(b_id, surf)] = rsb + kb * ((1.0 - sa) - (1.0 - esa))
        # counters
        self.played[a_id] = self.played.get(a_id, 0) + 1
        self.played[b_id] = self.played.get(b_id, 0) + 1
        self.played_surface[(a_id, surf)] = self.played_surface.get((a_id, surf), 0) + 1
        self.played_surface[(b_id, surf)] = self.played_surface.get((b_id, surf), 0) + 1


def compute_elo_features(df, cfg: EloConfig | None = None):
    """Walk a chronologically sorted match table once, emitting pre-match Elo
    features for every row. Returns a DataFrame aligned to `df.index`.

    Walkovers are skipped for RATING UPDATES (no tennis was played) but still
    receive features, so they can be predicted on if you ever want to.
    """
    import pandas as pd

    cfg = cfg or EloConfig()
    engine = EloEngine(cfg=cfg)
    out: list[dict] = []
    for row in df.itertuples(index=False):
        surf = row.surface
        feats = engine.snapshot(row.player_a_id, row.player_b_id, surf)
        out.append(feats)
        if not bool(getattr(row, "walkover", False)):
            engine.update(row.player_a_id, row.player_b_id, surf, int(row.label_winner))
    return pd.DataFrame(out, index=df.index), engine


class EloFeatureBuilder(FeatureBuilder):
    """Contract-facing wrapper around a live EloEngine (for single matches)."""

    name = "elo"

    def __init__(self, engine: EloEngine | None = None, cfg: EloConfig | None = None):
        self.engine = engine or EloEngine(cfg=cfg or EloConfig())

    def build(self, match, **ctx) -> dict:
        return self.engine.snapshot(
            match.player_a.player_id, match.player_b.player_id, match.surface.value
        )
