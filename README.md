# GUI for Subjective Experiments

Python-based baseline implementation of the JND subjective experiment system described by:

- `subjective_experiment_spec.md`
- `experiment_controller_design.md`
- `trial_scheduler_and_logging_spec.md`

## Run GUI

```bash
python run_gui.py
```

## Run tests

```bash
python -m pytest -q
```

## Notes

- GUI is implemented with Tkinter to keep it Python-only.
- Trial screen currently shows randomized presentation order and clip paths; response buttons collect `Same` / `Different`.
- Outputs are saved under: `Results/{subject_id}/{device}/{action_type}/{scene_id}/`.
