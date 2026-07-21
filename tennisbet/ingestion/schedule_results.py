"""Upcoming schedule + live/finished results for the current season.
Feeds both prediction (upcoming) and label backfill (finished).
Provider TBD (official ATP feed / a results API).
"""
from __future__ import annotations

from typing import Iterable

from .base import Fetcher


class ScheduleResultsFetcher(Fetcher):
    name = "schedule_results"

    def fetch(self, **kwargs) -> Iterable[dict]:
        raise NotImplementedError
