"""Historical ATP matches from Jeff Sackmann's open dataset.
Source: https://github.com/JeffSackmann/tennis_atp  (CSV per year)

This is the training backbone. Filter to ALLOWED_TIERS on normalize.
"""
from __future__ import annotations

from typing import Iterable

from .base import Fetcher

RAW_BASE = "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master"


class SackmannFetcher(Fetcher):
    name = "sackmann"

    def __init__(self, from_year: int = 2000, to_year: int | None = None):
        self.from_year = from_year
        self.to_year = to_year

    def fetch(self, **kwargs) -> Iterable[dict]:
        # TODO: download atp_matches_{year}.csv for the range and yield rows.
        raise NotImplementedError("SackmannFetcher.fetch not implemented yet")


def normalize(row: dict):
    """Map a Sackmann CSV row -> tennisbet.core.contracts.RawMatch.
    TODO: map tourney_level (G/M/A) -> Tier, surface, best_of, scores, winner.
    """
    raise NotImplementedError
