"""Inter-module data contracts. THIS is the spine of the modular design.

Every arrow between modules is one of these dataclasses. Pure stdlib so it
imports with zero dependencies and stays cheap to test.

Flow:
  RawMatch (ingestion) + PlayerState (features)
      -> MatchFeatures (features)
      -> OutcomePrediction + ClosenessPrediction (models)
      -> combined with OddsSnapshot (ingestion)
      -> ValueBet (betting)
  NewsSignal (news) enriches PlayerState / MatchFeatures.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional


class Surface(str, Enum):
    HARD = "hard"
    CLAY = "clay"
    GRASS = "grass"
    CARPET = "carpet"


class Tier(str, Enum):
    ATP250 = "ATP250"
    ATP500 = "ATP500"
    ATP1000 = "ATP1000"
    GRAND_SLAM = "GrandSlam"


# Hard scope rule for the whole project.
ALLOWED_TIERS = frozenset({Tier.ATP250, Tier.ATP500, Tier.ATP1000, Tier.GRAND_SLAM})


@dataclass(frozen=True)
class PlayerRef:
    player_id: str
    name: str


@dataclass
class RawMatch:
    match_id: str
    tournament: str
    tier: Tier
    surface: Surface
    round: str
    match_date: date
    player_a: PlayerRef
    player_b: PlayerRef
    best_of: int = 3
    # Result fields stay None until the match is played.
    winner_id: Optional[str] = None
    score: Optional[str] = None
    retired: bool = False
    raw: dict = field(default_factory=dict)  # source-specific extras


@dataclass
class PlayerState:
    """A player's state as of a given date (feature inputs)."""
    player_id: str
    as_of: date
    elo_overall: float = 1500.0
    elo_surface: float = 1500.0
    rank: Optional[int] = None
    matches_last_14d: int = 0
    days_since_last_match: Optional[int] = None
    injury_flag: bool = False           # set by the news module
    notes: dict = field(default_factory=dict)


@dataclass
class MatchFeatures:
    """Flat, model-ready feature vector for one match."""
    match_id: str
    features: dict = field(default_factory=dict)   # name -> numeric value
    # Labels (filled only for historical/training rows)
    label_winner: Optional[int] = None             # 1 if player_a won else 0
    label_closeness: Optional[float] = None


@dataclass
class OutcomePrediction:
    match_id: str
    p_a_win: float
    model_version: str = "unversioned"


@dataclass
class ClosenessPrediction:
    match_id: str
    label_name: str            # which closeness definition this refers to
    value: float               # predicted closeness on that label's scale
    model_version: str = "unversioned"


@dataclass
class OddsSnapshot:
    match_id: str
    bookmaker: str
    decimal_a: float
    decimal_b: float
    captured_at: datetime


@dataclass
class ValueBet:
    match_id: str
    side: str                  # "a" or "b"
    bookmaker: str
    model_p: float
    decimal_odds: float
    edge: float                # model_p - implied_p (after de-vig)
    expected_value: float      # model_p * decimal_odds - 1
    stake_fraction: float      # fraction of bankroll to wager


@dataclass
class NewsSignal:
    kind: str                  # injury | withdrawal | fatigue | personal | form
    severity: float            # 0..1
    confidence: float          # 0..1
    text: str
    source_url: str
    published_at: Optional[datetime] = None
    player_id: Optional[str] = None
    match_id: Optional[str] = None
