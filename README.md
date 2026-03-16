# GUI for Subjective Experiments

This repository now contains a runnable browser GUI implementing the workflow described in:

- `subjective_experiment_spec.md`
- `experiment_controller_design.md`
- `trial_scheduler_and_logging_spec.md`

## Run

```bash
python -m http.server 8000
```

Open `http://localhost:8000`.

## What is implemented

- Session metadata collection (`subject_id`, `device`, `action_type`, `scene_id`)
- Video filename parser supporting both:
  - Legacy 5-token format: `{resolution}_{redundant}_{fps}_{effect}_{shadow}.mp4`
  - Canonical 4-token format: `{resolution}_{fps}_{effect}_{shadow}.mp4`
- Canonical candidate map keyed by `(resolution, fps, effect, shadow)`
- Reference lookup by canonical config `VeryHigh|60|High|High`
- Training trials (not logged into experiment data)
- Phase 1 scheduler for lowest safe FPS search per resolution
- Phase 2 scheduler for graphics reduction trials
- Randomized left/right presentation order per trial
- Trial logging with response and response time
- Export for:
  - `raw_trial_log.json`
  - `phase1_result.json`
  - `phase2_result.json`
  - `final_jnd_safe_set.json`

## Notes

- Trials whose candidate video is missing can be skipped.
- This is a client-side implementation; selected files are used locally in-browser.
