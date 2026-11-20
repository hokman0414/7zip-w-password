"""Adapter boundary for the founder's malware classifier.

No classifier artifact exists in this repository. The adapter defines the
contract a real model must satisfy and ships an explicit "unavailable"
implementation so reports never imply a verdict that was not computed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class ClassifierSignal:
    model_id: str
    score: float | None
    calibrated: bool
    note: str


class MalwareClassifier(Protocol):
    model_id: str

    def score(self, path: Path) -> ClassifierSignal: ...


class UnavailableClassifier:
    model_id = "none"

    def score(self, path: Path) -> ClassifierSignal:
        return ClassifierSignal(
            self.model_id,
            None,
            False,
            "No validated malware classifier is connected. Maliciousness was not assessed.",
        )
