from __future__ import annotations

import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from .dataset_parser import (
    build_candidate_map,
    find_reference_video,
    parse_experiment_unit_from_path,
)
from .logger import append_trial_record, write_json
from .models import REFERENCE_CONFIG, RESOLUTION_LEVELS, RenderConfig, TrialRecord
from .trial_player import TrialPlayer, TrialPrompt
from .trial_scheduler import (
    fallback_phase1_if_45_different,
    phase1_sequence,
    phase2_configs,
    pick_training_pairs,
    sample_presentation_order,
)


def _trial_record_from(
    subject_id: str,
    unit,
    phase: str,
    trial_index: int,
    config: RenderConfig,
    order: str,
    response: str,
    response_time: float,
) -> TrialRecord:
    return TrialRecord(
        subject_id=subject_id,
        device=unit.device,
        action_type=unit.action_type,
        scene_id=unit.scene_id,
        phase=phase,
        trial_index=trial_index,
        resolution=config.resolution,
        fps=config.fps,
        effect=config.effect,
        shadow=config.shadow,
        presentation_order=order,
        response=response,  # type: ignore[arg-type]
        response_time=response_time,
        timestamp=datetime.now().isoformat(timespec="seconds"),
    )


def run_subjective_experiment(
    scene_folder: str | Path,
    subject_id: str,
    player: TrialPlayer,
    output_root: str | Path = "Results",
) -> dict:
    unit = parse_experiment_unit_from_path(scene_folder)
    candidate_map, warnings = build_candidate_map(scene_folder)
    reference_path = find_reference_video(candidate_map)

    output_dir = Path(output_root) / subject_id / unit.device / unit.action_type / unit.scene_id
    raw_log = output_dir / "raw_trial_log.json"
    trial_index = 0

    training_records = []
    for key, candidate in pick_training_pairs(candidate_map, count=3):
        order = sample_presentation_order()
        prompt = TrialPrompt(
            phase="training",
            reference_path=reference_path,
            candidate_path=candidate,
            presentation_order=order,
            label=f"Training config={key}",
        )
        player.play_trial(prompt)
        training_records.append({"candidate": key})

    phase1_results: dict[str, int | None] = {}
    phase2_results: dict[str, list[dict]] = {}

    for resolution in RESOLUTION_LEVELS:
        tested = []
        lowest: int | None = None
        search_ok = True

        for fps in phase1_sequence():
            config = RenderConfig(resolution, fps, "High", "High")
            key = config.as_key()
            if key not in candidate_map:
                warnings.append(f"Missing candidate in phase1: {key}")
                search_ok = False
                break
            order = sample_presentation_order()
            prompt = TrialPrompt(
                phase="phase1",
                reference_path=reference_path,
                candidate_path=candidate_map[key],
                presentation_order=order,
                label=f"{resolution} fps={fps}",
            )
            start = time.perf_counter()
            response = player.play_trial(prompt)
            elapsed = time.perf_counter() - start
            trial_index += 1
            append_trial_record(
                _trial_record_from(subject_id, unit, "phase1", trial_index, config, order, response, elapsed),
                raw_log,
            )
            tested.append((fps, response))

            if response == "Different":
                break

        if not search_ok:
            phase1_results[resolution] = None
            continue

        if tested:
            first_fps, first_resp = tested[0]
            if first_fps == 45 and first_resp == "Different":
                for fps in fallback_phase1_if_45_different():
                    config = RenderConfig(resolution, fps, "High", "High")
                    key = config.as_key()
                    if key not in candidate_map:
                        warnings.append(f"Missing candidate in phase1 fallback: {key}")
                        continue
                    order = sample_presentation_order()
                    prompt = TrialPrompt(
                        phase="phase1",
                        reference_path=reference_path,
                        candidate_path=candidate_map[key],
                        presentation_order=order,
                        label=f"{resolution} fps={fps}",
                    )
                    start = time.perf_counter()
                    response = player.play_trial(prompt)
                    elapsed = time.perf_counter() - start
                    trial_index += 1
                    append_trial_record(
                        _trial_record_from(subject_id, unit, "phase1", trial_index, config, order, response, elapsed),
                        raw_log,
                    )
                    lowest = fps if response == "Same" else None
            else:
                same_fps = [fps for fps, resp in tested if resp == "Same"]
                lowest = min(same_fps) if same_fps else None

        phase1_results[resolution] = lowest

        if lowest is None:
            continue

        safe_configs = [asdict(RenderConfig(resolution, lowest, "High", "High"))]
        for config in phase2_configs(resolution, lowest):
            key = config.as_key()
            if key not in candidate_map:
                warnings.append(f"Missing candidate in phase2: {key}")
                continue
            order = sample_presentation_order()
            prompt = TrialPrompt(
                phase="phase2",
                reference_path=reference_path,
                candidate_path=candidate_map[key],
                presentation_order=order,
                label=f"{resolution} fps={lowest} e={config.effect} s={config.shadow}",
            )
            start = time.perf_counter()
            response = player.play_trial(prompt)
            elapsed = time.perf_counter() - start
            trial_index += 1
            append_trial_record(
                _trial_record_from(subject_id, unit, "phase2", trial_index, config, order, response, elapsed),
                raw_log,
            )
            if response == "Same":
                safe_configs.append(asdict(config))

        phase2_results[resolution] = safe_configs

    final_set: list[dict] = []
    for configs in phase2_results.values():
        final_set.extend(configs)

    write_json(phase1_results, output_dir / "phase1_result.json")
    write_json(phase2_results, output_dir / "phase2_result.json")
    final_result = {
        "subject_id": subject_id,
        "device": unit.device,
        "action_type": unit.action_type,
        "scene_id": unit.scene_id,
        "jnd_safe_set": final_set,
        "warnings": warnings,
        "reference_config": asdict(REFERENCE_CONFIG),
        "training_trials": training_records,
    }
    write_json(final_result, output_dir / "final_jnd_safe_set.json")
    return final_result
