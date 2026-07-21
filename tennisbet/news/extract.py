"""Extract structured signals (injury/withdrawal/fatigue) from news text.
Start with keyword rules; upgrade to an LLM extractor behind the same
SignalExtractor interface. Output feeds PlayerState.injury_flag / features.
"""
from __future__ import annotations

from .base import SignalExtractor
from ..core.contracts import NewsSignal


class KeywordExtractor(SignalExtractor):
    def extract(self, item: dict) -> list[NewsSignal]:
        raise NotImplementedError
