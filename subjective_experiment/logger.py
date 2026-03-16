from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import TrialRecord


def append_trial_record(record: TrialRecord, raw_trial_log_path: str | Path) -> None:
    path = Path(raw_trial_log_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        payload = {"subject_id": record.subject_id, "trials": []}

    payload.setdefault("trials", []).append(asdict(record))
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_json(data: dict, output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
