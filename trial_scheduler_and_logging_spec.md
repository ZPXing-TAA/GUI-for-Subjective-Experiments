
TRIAL_SCHEDULER_AND_LOGGING_SPEC_MD_START

# Trial Scheduler and Logging Specification

This document defines how trials are scheduled and how experiment data is logged
for the JND-based subjective experiment system.

It complements the following documents:

- subjective_experiment_spec.md
- experiment_controller_design.md

This file focuses on runtime execution and data recording.

--------------------------------------------------

# 1. Core Concept

Each experiment session consists of multiple **trials**.

A trial compares:

Reference Video
Candidate Video

Participant chooses:

Same
Different

--------------------------------------------------

# 2. Trial Object

Internal representation of a trial:

Trial = {
    phase,
    resolution,
    fps,
    effect,
    shadow,
    candidate_path,
    reference_path
}

Example:

{
    "phase": "phase1",
    "resolution": "High",
    "fps": 45,
    "effect": "High",
    "shadow": "High",
    "candidate_path": ".../High_High_45_High_High.mp4",
    "reference_path": ".../VeryHigh_VeryHigh_60_High_High.mp4"
}

--------------------------------------------------

# 3. Trial Scheduler

The scheduler determines which trial to present next.

Main responsibilities:

- choose next configuration
- randomize presentation order
- handle branching logic (phase1 search)
- ensure valid video exists
- stop phase when decision reached

--------------------------------------------------

# 4. Trial Presentation Order

To avoid bias, presentation order should be randomized.

Two possible layouts:

Layout A:

Left  = Reference
Right = Candidate

Layout B:

Left  = Candidate
Right = Reference

Random choice per trial.

Record which layout was used.

--------------------------------------------------

# 5. Phase 1 Scheduler Logic

Goal:

Find lowest JND-safe FPS for each resolution.

Test configurations:

(resolution, fps, High, High)

Search order:

1. test fps = 45
2. if SAME → test 30
3. if SAME → test 24
4. if DIFFERENT → result = previous fps

Example flow:

Test 45
→ SAME

Test 30
→ DIFFERENT

Result = 45

--------------------------------------------------

# 6. Phase 2 Scheduler Logic

Base config:

(resolution, fps*, High, High)

Test:

(resolution, fps*, Low, High)
(resolution, fps*, High, Low)
(resolution, fps*, Low, Low)

Each candidate tested independently.

--------------------------------------------------

# 7. Training Trials

Before formal trials begin, run training trials.

Purpose:

- familiarize participant with interface
- demonstrate obvious quality differences

Recommended:

3–5 training trials.

Training results should NOT be logged as experiment data.

--------------------------------------------------

# 8. Trial Logging Structure

Each trial must be logged.

TrialRecord = {
    subject_id,
    device,
    action_type,
    scene_id,
    phase,
    trial_index,
    resolution,
    fps,
    effect,
    shadow,
    presentation_order,
    response,
    response_time,
    timestamp
}

--------------------------------------------------

# 9. Example Trial Record

{
    "subject_id": "S01",
    "device": "huaweimate",
    "action_type": "climb",
    "scene_id": "natlan_1_h1",
    "phase": "phase1",
    "trial_index": 5,
    "resolution": "High",
    "fps": 45,
    "effect": "High",
    "shadow": "High",
    "presentation_order": "candidate_left",
    "response": "Same",
    "response_time": 3.1,
    "timestamp": "2026-03-16T14:12:05"
}

--------------------------------------------------

# 10. Logging Files

Each session should produce:

1. raw_trial_log.json
2. phase1_result.json
3. phase2_result.json
4. final_jnd_safe_set.json

--------------------------------------------------

# 11. Raw Trial Log

Contains all trials in chronological order.

Example:

{
    "subject_id": "S01",
    "trials": [ ... ]
}

--------------------------------------------------

# 12. Phase 1 Result

Example:

{
    "VeryHigh": 45,
    "High": 30,
    "Medium": 30,
    "Low": null
}

null means no JND-safe FPS found.

--------------------------------------------------

# 13. Phase 2 Result

Example:

{
    "VeryHigh":[
        {"fps":45,"effect":"Low","shadow":"High"},
        {"fps":45,"effect":"High","shadow":"Low"}
    ]
}

--------------------------------------------------

# 14. Final JND-safe Set

Example:

{
    "device":"huaweimate",
    "action_type":"climb",
    "scene_id":"natlan_1_h1",
    "jnd_safe_set":[
        {"resolution":"VeryHigh","fps":45,"effect":"Low","shadow":"High"},
        {"resolution":"VeryHigh","fps":45,"effect":"High","shadow":"Low"}
    ]
}

--------------------------------------------------

# 15. Resume Support

If experiment crashes or stops early:

Controller should be able to:

- reload raw_trial_log
- reconstruct scheduler state
- continue remaining trials

--------------------------------------------------

# 16. Data Integrity Rules

Logging system must ensure:

- no trial overwritten
- timestamps always recorded
- config stored in canonical form

--------------------------------------------------

# 17. Aggregation for Analysis

Later analysis can compute:

same_ratio = SAME / total_trials

per configuration.

Example:

config_stats = {
    ("VeryHigh",45,"Low","High"): {
        "same":12,
        "different":3
    }
}

--------------------------------------------------

# 18. Recommended Output Directory

Experiment results stored under:

Results/{subject_id}/{device}/{action_type}/{scene_id}/

Example:

Results/S01/huaweimate/climb/natlan_1_h1/

--------------------------------------------------

# 19. Minimal Implementation

Minimum system should support:

- randomized presentation
- SAME / DIFFERENT input
- trial logging
- phase1 scheduler
- phase2 scheduler
- result export

--------------------------------------------------

# 20. Summary

Trial scheduler controls experiment flow.

Logging system records every trial and enables:

- reproducibility
- statistical analysis
- model training

Both are essential for reliable subjective experiments.

TRIAL_SCHEDULER_AND_LOGGING_SPEC_MD_END
