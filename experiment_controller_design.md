# Experiment Controller Design

This document defines a controller-oriented design for implementing the JND-based subjective experiment system.

It is intended for coding agents to translate directly into Python modules, GUI handlers, logging utilities, and scheduling logic.

--------------------------------------------------

# 1. Purpose

The controller is responsible for:

1. Loading one experiment unit
2. Building a canonical candidate map from the scene folder
3. Locating the reference video
4. Running training trials
5. Running Phase 1 and Phase 2 trial scheduling
6. Recording every response
7. Producing final JND-safe results

--------------------------------------------------

# 2. Core Input

The minimal input to the controller is:

`scene_folder`
`subject_id`

Example:

`scene_folder = /Users/xingzhengpeng/CODEZONE/PCO/Power-Optimization/Recordings/huaweimate/climb/natlan_1_h1`
`subject_id = S01`

--------------------------------------------------

# 3. Controller Output

The controller must generate:

1. Raw trial logs
2. Phase 1 result
3. Phase 2 result
4. Final JND-safe set

Suggested output files:

`raw_trials/{subject_id}_{device}_{action_type}_{scene_id}.json`
`phase1/{subject_id}_{device}_{action_type}_{scene_id}.json`
`phase2/{subject_id}_{device}_{action_type}_{scene_id}.json`
`final_sets/{subject_id}_{device}_{action_type}_{scene_id}.json`

--------------------------------------------------

# 4. Core Data Structures

## 4.1 ExperimentUnit

`ExperimentUnit = {`
`    root_dir,`
`    device,`
`    action_type,`
`    scene_id,`
`    region,`
`    scene_index,`
`    route_id,`
`    scene_folder`
`}`

Example:

`{`
`  "device": "huaweimate",`
`  "action_type": "climb",`
`  "scene_id": "natlan_1_h1",`
`  "region": "natlan",`
`  "scene_index": 1,`
`  "route_id": 1`
`}`

--------------------------------------------------

## 4.2 RenderConfig

`RenderConfig = {`
`    resolution,`
`    fps,`
`    effect,`
`    shadow`
`}`

Example:

`{`
`  "resolution": "High",`
`  "fps": 24,`
`  "effect": "High",`
`  "shadow": "High"`
`}`

--------------------------------------------------

## 4.3 TrialRecord

`TrialRecord = {`
`    subject_id,`
`    device,`
`    action_type,`
`    scene_id,`
`    phase,`
`    trial_index,`
`    candidate_config,`
`    reference_config,`
`    presentation_order,`
`    response,`
`    timestamp`
`}`

Allowed response values:

`Same`
`Different`

Allowed presentation_order values:

`reference_first`
`candidate_first`

--------------------------------------------------

## 4.4 Candidate Map

`candidate_map[(resolution, fps, effect, shadow)] = video_path`

Example:

`candidate_map[("High", 24, "High", "High")] = "/.../High_High_24_High_High.mp4"`

--------------------------------------------------

# 5. Required Modules

Suggested modules:

`dataset_parser.py`
`models.py`
`experiment_controller.py`
`trial_scheduler.py`
`trial_player.py`
`logger.py`
`result_writer.py`
`config.py`

--------------------------------------------------

# 6. Required Functions

## 6.1 Dataset Parsing

`parse_experiment_unit_from_path(scene_folder) -> ExperimentUnit`

Responsibilities:

1. Parse device from folder path
2. Parse action_type from folder path
3. Parse scene_id from folder path
4. Parse region, scene_index, route_id from scene_id
5. Return ExperimentUnit

--------------------------------------------------

`parse_scene_id(scene_id) -> {region, scene_index, route_id}`

Expected scene_id format:

`{region}_{scene_index}_h{route_id}`

Example:

`natlan_1_h1 -> {region:"natlan", scene_index:1, route_id:1}`

--------------------------------------------------

`parse_render_config_from_filename(filename) -> RenderConfig or None`

Support both:

1. Legacy 5-token format:
`{resolution}_{redundant}_{fps}_{effect}_{shadow}.mp4`

2. Canonical 4-token format:
`{resolution}_{fps}_{effect}_{shadow}.mp4`

Legacy example:

`High_High_24_High_High.mp4`

Canonical example:

`High_24_High_High.mp4`

Parsing rules:

If 5 tokens:

`resolution = token[0]`
`fps = int(token[2])`
`effect = token[3]`
`shadow = token[4]`

If 4 tokens:

`resolution = token[0]`
`fps = int(token[1])`
`effect = token[2]`
`shadow = token[3]`

If invalid:

`return None`

--------------------------------------------------

`build_candidate_map(scene_folder) -> candidate_map`

Responsibilities:

1. Scan all `.mp4` files in scene_folder
2. Parse config from each filename
3. Skip invalid files with warning
4. Build canonical candidate map

--------------------------------------------------

`find_reference_video(candidate_map) -> video_path`

Reference config is always:

`("VeryHigh", 60, "High", "High")`

If missing:

Raise explicit error or return failure status.

--------------------------------------------------

# 7. Trial Player Contract

The controller should not hardcode GUI internals.

Instead, define a player interface such as:

`play_trial(reference_path, candidate_path, order) -> response`

Expected behavior:

1. Display two videos sequentially
2. Randomize order according to input
3. Block until participant submits response
4. Return either `Same` or `Different`

--------------------------------------------------

# 8. Training Phase Design

`run_training_phase(player)`

Purpose:

1. Familiarize subject with the interface
2. Show a small number of example comparisons
3. Ensure the subject understands the task

Suggested training trial count:

`2 to 4 trials`

Training trials may use:

1. Obvious difference pairs
2. Very similar pairs

Training responses should not affect final result.

--------------------------------------------------

# 9. Phase 1 Scheduling Logic

## 9.1 Goal

For each resolution, find the lowest JND-safe FPS while fixing:

`effect = High`
`shadow = High`

Allowed resolutions:

`Lowest`
`Low`
`Medium`
`High`
`VeryHigh`

Allowed FPS:

`24`
`30`
`45`
`60`

--------------------------------------------------

## 9.2 Function Contract

`run_phase1_for_resolution(resolution, candidate_map, reference_path, player, logger) -> result`

Return format:

`{`
`    "resolution": resolution,`
`    "lowest_jnd_safe_fps": int or null,`
`    "status": "FOUND" or "NOT_FOUND"`
`}`

--------------------------------------------------

## 9.3 Decision Logic

Test `(resolution, 45, High, High)` first.

Case A: response = Same

1. Test `(resolution, 30, High, High)`
2. If Same:
   - Test `(resolution, 24, High, High)`
   - If Same -> result = 24
   - If Different -> result = 30
3. If Different -> result = 45

Case B: response = Different

1. Test `(resolution, 60, High, High)`
2. If Same -> result = 60
3. If Different -> result = NOT_FOUND

--------------------------------------------------

## 9.4 Missing Candidate Handling

If a required candidate video is missing:

1. Log warning
2. Return status such as `MISSING_ASSET` or degrade gracefully
3. Do not crash the whole experiment

Suggested first-version policy:

If the tested candidate is missing, mark the resolution result as unavailable and continue with the next resolution.

--------------------------------------------------

# 10. Phase 2 Scheduling Logic

## 10.1 Goal

For each resolution where Phase 1 found `fps_star`, test additional graphics reductions.

Base config:

`(resolution, fps_star, High, High)`

Test configs:

`(resolution, fps_star, Low, High)`
`(resolution, fps_star, High, Low)`
`(resolution, fps_star, Low, Low)`

--------------------------------------------------

## 10.2 Function Contract

`run_phase2_for_resolution(resolution, fps_star, candidate_map, reference_path, player, logger) -> result`

Return format:

`{`
`  "resolution": resolution,`
`  "fps": fps_star,`
`  "phase2_results": [`
`      {"effect":"Low",  "shadow":"High", "jnd_safe": true_or_false},`
`      {"effect":"High", "shadow":"Low",  "jnd_safe": true_or_false},`
`      {"effect":"Low",  "shadow":"Low",  "jnd_safe": true_or_false}`
`  ]`
`}`

--------------------------------------------------

## 10.3 Important Rule

Phase 2 may produce multiple safe configurations.

This is expected and valid.

The controller must not force a single winner.

--------------------------------------------------

# 11. Trial Ordering

Each trial should randomize whether the reference is shown first or second.

Suggested helper:

`sample_presentation_order() -> reference_first or candidate_first`

This order must be recorded in TrialRecord.

--------------------------------------------------

# 12. Logging Design

## 12.1 Trial Logging

Each completed trial should immediately write or append a TrialRecord.

Recommended helper:

`save_trial_record(record, output_path)`

This protects against data loss if the experiment closes unexpectedly.

--------------------------------------------------

## 12.2 Phase Result Logging

At the end of each resolution:

1. Save Phase 1 resolution-level result
2. Save Phase 2 resolution-level result if available

--------------------------------------------------

## 12.3 Final Result Logging

After all resolutions complete, generate:

`save_final_result(final_result, output_path)`

Final result format:

`{`
`  "subject_id": "S01",`
`  "device": "huaweimate",`
`  "action_type": "climb",`
`  "scene_id": "natlan_1_h1",`
`  "jnd_safe_set": [...]`
`}`

--------------------------------------------------

# 13. Merge Logic

Suggested merge function:

`merge_phase_results(phase1_results, phase2_results) -> jnd_safe_set`

Suggested rule:

1. For each resolution with valid `fps_star`
2. Include any Phase 2 configuration marked safe
3. Optionally include `(resolution, fps_star, High, High)` as a baseline safe config

Recommended first-version behavior:

Include all safe configs, including the baseline Phase 1 safe config.

This keeps the output flexible for later power-based filtering.

--------------------------------------------------

# 14. Main Controller Flow

Suggested top-level function:

`run_subjective_experiment(scene_folder, subject_id, player, output_root)`

Pseudo flow:

`1. unit = parse_experiment_unit_from_path(scene_folder)`
`2. candidate_map = build_candidate_map(scene_folder)`
`3. reference_path = find_reference_video(candidate_map)`
`4. run_training_phase(player)`
`5. for resolution in ["VeryHigh", "High", "Medium", "Low", "Lowest"]:`
`6.     run_phase1_for_resolution(...)`
`7. for each valid phase1 result:`
`8.     run_phase2_for_resolution(...)`
`9. final_set = merge_phase_results(...)`
`10. save outputs`
`11. return final result`

--------------------------------------------------

# 15. GUI State Machine

Recommended state machine:

`INIT`
`TRAINING`
`PHASE1`
`PHASE2`
`FINISHED`

--------------------------------------------------

# 16. GUI Screen Responsibilities

## 16.1 Start Screen

Inputs:

`subject_id`
`scene_folder`

Button:

`Start Experiment`

--------------------------------------------------

## 16.2 Training Screen

Shows a few example trials.

Button:

`Continue`

--------------------------------------------------

## 16.3 Trial Screen

Must display:

1. Video playback area
2. Response buttons
3. Trial progress indicator

Response buttons:

`No noticeable difference`
`Visible difference`

--------------------------------------------------

## 16.4 Completion Screen

Display:

`Experiment complete`
`Data saved`

--------------------------------------------------

# 17. Error Handling Rules

1. Missing reference video -> fail fast with explicit message
2. Missing candidate video -> skip candidate and log warning
3. Invalid filename -> skip and log warning
4. Unexpected response value -> reject and require valid response
5. Partial experiment interruption -> preserve already written trial logs

--------------------------------------------------

# 18. Suggested Project Layout

`subjective_experiment/`
`├── config/`
`├── dataset_parser.py`
`├── models.py`
`├── experiment_controller.py`
`├── trial_scheduler.py`
`├── trial_player.py`
`├── logger.py`
`├── result_writer.py`
`├── gui/`
`└── outputs/`

--------------------------------------------------

# 19. First-Version Priorities

Must-have:

1. Robust dataset parsing
2. Reference lookup
3. Phase 1 scheduling
4. Phase 2 scheduling
5. Trial playing interface
6. Logging
7. Final result export

Nice-to-have later:

1. Resume interrupted experiments
2. Multi-subject aggregation
3. Rest breaks
4. Better randomization policies
5. GUI styling

--------------------------------------------------

# 20. Final Design Principle

The controller should treat:

1. folder path as experiment identity
2. filename as render configuration source
3. parsed canonical config as the only valid downstream representation

All legacy filename quirks must be handled during parsing and must never leak into the experiment logic.

END OF DESIGN
