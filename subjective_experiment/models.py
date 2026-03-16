from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


Response = Literal["Same", "Different"]
PresentationOrder = Literal["reference_first", "candidate_first"]


@dataclass(frozen=True)
class RenderConfig:
    resolution: str
    fps: int
    effect: str
    shadow: str

    def as_key(self) -> tuple[str, int, str, str]:
        return (self.resolution, self.fps, self.effect, self.shadow)


@dataclass(frozen=True)
class ExperimentUnit:
    root_dir: Path
    device: str
    action_type: str
    scene_id: str
    region: str
    scene_index: int
    route_id: int
    scene_folder: Path


@dataclass
class TrialRecord:
    subject_id: str
    device: str
    action_type: str
    scene_id: str
    phase: str
    trial_index: int
    resolution: str
    fps: int
    effect: str
    shadow: str
    presentation_order: PresentationOrder
    response: Response
    response_time: float
    timestamp: str


REFERENCE_CONFIG = RenderConfig(resolution="VeryHigh", fps=60, effect="High", shadow="High")
RESOLUTION_LEVELS = ["VeryHigh", "High", "Medium", "Low", "Lowest"]
FPS_LEVELS = [24, 30, 45, 60]
