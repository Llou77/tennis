"""Match-time weather by venue (open-meteo or similar). Emits per-match
conditions (temp, humidity, wind) consumed by features.context.
Matters mostly for outdoor courts; indoor matches get neutral values.
"""
from __future__ import annotations

from typing import Iterable

from .base import Fetcher


class WeatherFetcher(Fetcher):
    name = "weather"

    def fetch(self, **kwargs) -> Iterable[dict]:
        raise NotImplementedError
