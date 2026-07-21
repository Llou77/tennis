"""Predictor interface shared by outcome and closeness models.
Every model is versioned and can save/load itself, so you can iterate on one
model family without disturbing anything that consumes its predictions.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class Predictor(ABC):
    version: str = "unversioned"

    @abstractmethod
    def fit(self, X, y):
        raise NotImplementedError

    @abstractmethod
    def predict(self, X):
        raise NotImplementedError

    def save(self, path: str):
        raise NotImplementedError

    @classmethod
    def load(cls, path: str):
        raise NotImplementedError
