from __future__ import annotations

from pathlib import Path
import re
from typing import Optional

from .models import ExperimentUnit, RenderConfig

SCENE_PATTERN = re.compile(r"^(?P<region>[A-Za-z0-9]+)_(?P<scene_index>\d+)_h(?P<route_id>\d+)$")


def parse_scene_id(scene_id: str) -> dict[str, int | str]:
    m = SCENE_PATTERN.match(scene_id)
    if not m:
        raise ValueError(f"Invalid scene_id format: {scene_id}")
    return {
        "region": m.group("region"),
        "scene_index": int(m.group("scene_index")),
        "route_id": int(m.group("route_id")),
    }


def parse_experiment_unit_from_path(scene_folder: str | Path) -> ExperimentUnit:
    scene_path = Path(scene_folder).resolve()
    scene_id = scene_path.name
    action_type = scene_path.parent.name
    device = scene_path.parent.parent.name
    root_dir = scene_path.parent.parent.parent
    parsed = parse_scene_id(scene_id)
    return ExperimentUnit(
        root_dir=root_dir,
        device=device,
        action_type=action_type,
        scene_id=scene_id,
        region=str(parsed["region"]),
        scene_index=int(parsed["scene_index"]),
        route_id=int(parsed["route_id"]),
        scene_folder=scene_path,
    )


def parse_render_config_from_filename(filename: str) -> Optional[RenderConfig]:
    name = Path(filename).name
    if not name.lower().endswith(".mp4"):
        return None
    stem = Path(name).stem
    tokens = stem.split("_")
    try:
        if len(tokens) == 5:
            return RenderConfig(
                resolution=tokens[0],
                fps=int(tokens[2]),
                effect=tokens[3],
                shadow=tokens[4],
            )
        if len(tokens) == 4:
            return RenderConfig(
                resolution=tokens[0],
                fps=int(tokens[1]),
                effect=tokens[2],
                shadow=tokens[3],
            )
    except ValueError:
        return None
    return None


def build_candidate_map(scene_folder: str | Path) -> tuple[dict[tuple[str, int, str, str], Path], list[str]]:
    scene_path = Path(scene_folder)
    candidate_map: dict[tuple[str, int, str, str], Path] = {}
    warnings: list[str] = []

    for video_path in sorted(scene_path.glob("*.mp4")):
        config = parse_render_config_from_filename(video_path.name)
        if config is None:
            warnings.append(f"Invalid filename skipped: {video_path.name}")
            continue
        key = config.as_key()
        if key in candidate_map:
            warnings.append(f"Duplicate config key overwritten by: {video_path.name}")
        candidate_map[key] = video_path

    return candidate_map, warnings


def find_reference_video(candidate_map: dict[tuple[str, int, str, str], Path]) -> Path:
    reference_key = ("VeryHigh", 60, "High", "High")
    if reference_key not in candidate_map:
        raise FileNotFoundError("Reference video (VeryHigh,60,High,High) not found in candidate map")
    return candidate_map[reference_key]
