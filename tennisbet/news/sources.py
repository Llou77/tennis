"""Concrete news feeds (RSS / news API). Stubs for now."""
from __future__ import annotations

from typing import Iterable

from .base import NewsSource


class RSSNewsSource(NewsSource):
    name = "rss"

    def __init__(self, feeds: list[str] | None = None):
        self.feeds = feeds or []

    def fetch(self, **kwargs) -> Iterable[dict]:
        raise NotImplementedError
