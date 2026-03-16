from __future__ import annotations

import random
from pathlib import Path

from .models import FPS_LEVELS, RenderConfig


def sample_presentation_order() -> str:
    return random.choice(["reference_first", "candidate_first"])


def phase1_sequence() -> list[int]:
    return [45, 30, 24]


def phase2_configs(resolution: str, fps: int) -> list[RenderConfig]:
    return [
        RenderConfig(resolution=resolution, fps=fps, effect="Low", shadow="High"),
        RenderConfig(resolution=resolution, fps=fps, effect="High", shadow="Low"),
        RenderConfig(resolution=resolution, fps=fps, effect="Low", shadow="Low"),
    ]


def pick_training_pairs(candidate_map: dict[tuple[str, int, str, str], Path], count: int = 3) -> list[tuple[tuple[str, int, str, str], Path]]:
    keys = list(candidate_map.items())
    random.shuffle(keys)
    return keys[: min(count, len(keys))]


def fallback_phase1_if_45_different() -> list[int]:
    return [60]
