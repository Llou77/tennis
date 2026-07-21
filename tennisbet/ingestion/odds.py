"""Bookmaker odds snapshots. Reads ODDS_API_KEY from the environment.
Provider placeholder: the-odds-api. Emits tennisbet.core.contracts.OddsSnapshot.

Capture cadence matters: store multiple snapshots per match so you can later
measure yourself against the CLOSING line, not just opening prices.
"""
from __future__ import annotations

from typing import Iterable

from .base import Fetcher


class OddsFetcher(Fetcher):
    name = "odds"

    def __init__(self, bookmakers: list[str] | None = None):
        self.bookmakers = bookmakers or ["pinnacle"]

    def fetch(self, **kwargs) -> Iterable[dict]:
        raise NotImplementedError
