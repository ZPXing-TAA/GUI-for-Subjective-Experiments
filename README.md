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

- GUI is implemented with Tkinter to keep it Python-first.
- For each trial, the two compared videos are played **sequentially** (`Clip A` then `Clip B`) before response collection.
- Playback uses an external local player backend and auto-detects one of: `ffplay`, `mpv`, `vlc`.
- Outputs are saved under: `Results/{subject_id}/{device}/{action_type}/{scene_id}/`.
