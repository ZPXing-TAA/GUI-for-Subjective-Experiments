from __future__ import annotations

from pathlib import Path

from subjective_experiment.dataset_parser import (
    build_candidate_map,
    find_reference_video,
    parse_render_config_from_filename,
    parse_scene_id,
)
from subjective_experiment.experiment_controller import run_subjective_experiment
from subjective_experiment.trial_player import TrialPrompt


class MockPlayer:
    def play_trial(self, prompt: TrialPrompt) -> str:
        key_text = prompt.candidate_path.name
        if "_24_" in key_text or "_Low_Low" in key_text:
            return "Different"
        return "Same"


def touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")


def test_scene_id_parse() -> None:
    parsed = parse_scene_id("natlan_1_h1")
    assert parsed["region"] == "natlan"
    assert parsed["scene_index"] == 1
    assert parsed["route_id"] == 1


def test_render_filename_parse_both_formats() -> None:
    cfg1 = parse_render_config_from_filename("High_High_24_High_High.mp4")
    cfg2 = parse_render_config_from_filename("High_24_High_High.mp4")
    assert cfg1 and cfg1.fps == 24
    assert cfg2 and cfg2.fps == 24


def test_controller_writes_outputs(tmp_path: Path) -> None:
    scene = tmp_path / "Recordings" / "huaweimate" / "climb" / "natlan_1_h1"
    filenames = [
        "VeryHigh_VeryHigh_60_High_High.mp4",
        "VeryHigh_High_45_High_High.mp4",
        "VeryHigh_High_30_High_High.mp4",
        "VeryHigh_High_24_High_High.mp4",
        "VeryHigh_High_30_Low_High.mp4",
        "VeryHigh_High_30_High_Low.mp4",
        "VeryHigh_High_30_Low_Low.mp4",
    ]
    for f in filenames:
        touch(scene / f)

    cmap, _ = build_candidate_map(scene)
    assert find_reference_video(cmap).name == "VeryHigh_VeryHigh_60_High_High.mp4"

    out_root = tmp_path / "Results"
    result = run_subjective_experiment(scene, "S01", MockPlayer(), out_root)
    assert result["subject_id"] == "S01"
    final_file = out_root / "S01" / "huaweimate" / "climb" / "natlan_1_h1" / "final_jnd_safe_set.json"
    assert final_file.exists()
