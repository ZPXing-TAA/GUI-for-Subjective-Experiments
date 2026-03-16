from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .models import Response


@dataclass
class TrialPrompt:
    phase: str
    reference_path: Path
    candidate_path: Path
    presentation_order: str
    label: str


class TrialPlayer(Protocol):
    def play_trial(self, prompt: TrialPrompt) -> Response:
        ...
