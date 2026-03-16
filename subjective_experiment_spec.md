# Subjective Experiment Specification

This document defines the dataset structure, filename parsing rules, and experiment logic for the JND-based subjective experiment system used in the Perception-aware Game Power Optimization project.

The specification is written to be easily interpreted by coding agents.

--------------------------------------------------

# 1. Dataset Root Structure

All recordings are stored under:

`Recordings/`

Full path example:

`Recordings/{device}/{action_type}/{scene_id}/`

Example:

`Recordings/huaweimate/climb/natlan_1_h1/`

Meaning:

device = huaweimate  
action_type = climb  
scene_id = natlan_1_h1

--------------------------------------------------

# 2. Experiment Unit

Each subjective experiment operates on a single **experiment unit**.

Definition:

`ExperimentUnit = (device, action_type, scene_id)`

Example:

`(huaweimate, climb, natlan_1_h1)`

All videos used in the experiment are located inside:

`Recordings/{device}/{action_type}/{scene_id}/`

--------------------------------------------------

# 3. Scene ID Format

Scene IDs follow this naming rule:

`{region}_{scene_index}_h{route_id}`

Example:

`natlan_1_h1`

Meaning:

region = natlan  
scene_index = 1  
route_id = 1

route_id corresponds to the route script used during recording (e.g. 1.py).

--------------------------------------------------

# 4. Action Types

Possible action types include:

`move`
`run`
`climb`
`swim`
`glide`
`combat`

Each action type uses the same scene naming logic.

--------------------------------------------------

# 5. Video Filename Format (Current Dataset)

Current filenames follow a **legacy 5-token format**:

`{resolution}_{redundant}_{fps}_{effect}_{shadow}.mp4`

Example:

`High_High_24_High_High.mp4`

Token interpretation:

`token[0] = resolution`
`token[1] = redundant (ignored)`
`token[2] = fps`
`token[3] = effect`
`token[4] = shadow`

Effective parsed configuration:

`resolution = High`
`fps = 24`
`effect = High`
`shadow = High`

The second token must be ignored.

--------------------------------------------------

# 6. Future Canonical Filename Format

Future recordings should use the simplified format:

`{resolution}_{fps}_{effect}_{shadow}.mp4`

Example:

`VeryHigh_60_High_High.mp4`
`Medium_30_Low_High.mp4`
`Lowest_24_Low_Low.mp4`

The experiment controller must support both formats.

--------------------------------------------------

# 7. Resolution Levels

Allowed resolution values:

`Lowest`
`Low`
`Medium`
`High`
`VeryHigh`

--------------------------------------------------

# 8. FPS Levels

Allowed fps values:

`24`
`30`
`45`
`60`

--------------------------------------------------

# 9. Graphics Parameters

Effect levels:

`Low`
`High`

Shadow levels:

`Low`
`High`

--------------------------------------------------

# 10. Canonical RenderConfig Structure

After parsing filenames, every video must be represented internally as:

`RenderConfig = { resolution, fps, effect, shadow }`

Example:

`{"resolution": "High", "fps": 24, "effect": "High", "shadow": "High"}`

All experiment logic must use this canonical structure.

--------------------------------------------------

# 11. Reference Video

Reference configuration is always:

`resolution = VeryHigh`
`fps = 60`
`effect = High`
`shadow = High`

Example filename:

`VeryHigh_VeryHigh_60_High_High.mp4`

or

`VeryHigh_60_High_High.mp4`

The controller must locate the reference video using the canonical configuration rather than a hardcoded filename.

--------------------------------------------------

# 12. Candidate Map

All parsed videos should be stored in a candidate map:

`candidate_map[(resolution, fps, effect, shadow)] = video_path`

Example:

`candidate_map[("High",24,"High","High")] = ".../High_High_24_High_High.mp4"`

This allows experiment logic to be independent of filenames.

--------------------------------------------------

# 13. Parsing Logic

Filename parsing algorithm:

`name = remove_extension(filename)`
`tokens = split(name,"_")`

`if token_count == 5:`
`    resolution = tokens[0]`
`    fps = int(tokens[2])`
`    effect = tokens[3]`
`    shadow = tokens[4]`
`elif token_count == 4:`
`    resolution = tokens[0]`
`    fps = int(tokens[1])`
`    effect = tokens[2]`
`    shadow = tokens[3]`
`else:`
`    mark file invalid`

--------------------------------------------------

# 14. Subjective Experiment Goal

For each experiment unit, determine which render configurations are visually indistinguishable from the reference video.

The result is a **JND-safe set**.

The result does not need to be a single configuration.

--------------------------------------------------

# 15. Trial Structure

Each trial presents two videos:

`Reference Video`
`Candidate Video`

Participant response options:

`Same`
`Different`

Meaning:

Same = no noticeable difference  
Different = noticeable difference

--------------------------------------------------

# 16. Phase 1 (FPS Search)

Goal:

Find the lowest JND-safe FPS for each resolution.

Fixed parameters:

`effect = High`
`shadow = High`

Test configurations:

`(resolution, fps, High, High)`

FPS candidates:

`24`
`30`
`45`
`60`

Binary-search style procedure:

1. Test 45
2. If SAME -> test 30
3. If SAME -> test 24
4. If DIFFERENT -> fallback to previous level

Example result:

`resolution = VeryHigh`
`lowest_safe_fps = 45`

--------------------------------------------------

# 17. Phase 2 (Graphics Reduction)

After Phase 1 finds a safe FPS:

`(resolution, fps*, High, High)`

Test graphics reductions:

`(resolution, fps*, Low, High)`
`(resolution, fps*, High, Low)`
`(resolution, fps*, Low, Low)`

If participants report SAME, the configuration is considered JND-safe.

--------------------------------------------------

# 18. Final Output

Each experiment unit should produce:

`{ device, action_type, scene_id, jnd_safe_set:[RenderConfig...] }`

Example:

`{"device":"huaweimate","action_type":"climb","scene_id":"natlan_1_h1","jnd_safe_set":[{"resolution":"VeryHigh","fps":45,"effect":"Low","shadow":"High"},{"resolution":"VeryHigh","fps":45,"effect":"High","shadow":"Low"}]}`

--------------------------------------------------

# 19. Experiment Logging

Each trial should record:

`TrialRecord = { subject_id, device, action_type, scene_id, phase, trial_index, candidate_config, presentation_order, response, timestamp }`

--------------------------------------------------

# 20. Required Controller Functions

The experiment controller should implement:

`parse_experiment_unit_from_path()`
`parse_scene_id()`
`parse_render_config_from_filename()`
`build_candidate_map()`
`find_reference_video()`
`run_training_phase()`
`run_phase1()`
`run_phase2()`
`save_trial_record()`
`save_final_result()`

--------------------------------------------------

# 21. Minimal Experiment Workflow

Input:

`scene_folder`
`subject_id`

Process:

`parse metadata`
`build candidate map`
`identify reference video`
`run training trials`
`run phase 1`
`run phase 2`
`store logs`
`output JND-safe set`

--------------------------------------------------

# 22. Design Principles

1. Folder path defines experiment unit.
2. Filename defines render configuration.
3. Legacy redundant tokens must be ignored.
4. All logic must operate on canonical parsed configs.
5. Missing files must not crash the system.

--------------------------------------------------

END OF SPECIFICATION
