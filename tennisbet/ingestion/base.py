"""Fetcher interface. Every data source implements this and nothing else
outside the module needs to know how it works.

Contract: fetch() returns an iterable of dicts (source-native rows). The
matching normalizer turns those into tennisbet.core.contracts objects.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable


class Fetcher(ABC):
    name: str = "base"

    @abstractmethod
    def fetch(self, **kwargs) -> Iterable[dict]:
        """Return raw rows from the source."""
        raise NotImplementedError
