"""News enrichment interfaces. Built LAST — most match-relevant info is already
priced into odds by match time, so this is lower ROI than structured data.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from ..core.contracts import NewsSignal


class NewsSource(ABC):
    name: str = "base"

    @abstractmethod
    def fetch(self, **kwargs) -> Iterable[dict]:
        raise NotImplementedError


class SignalExtractor(ABC):
    @abstractmethod
    def extract(self, item: dict) -> list[NewsSignal]:
        """Turn a news item into structured NewsSignal(s)."""
        raise NotImplementedError
