from __future__ import annotations

import shutil
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from subjective_experiment.experiment_controller import run_subjective_experiment
from subjective_experiment.trial_player import TrialPlayer, TrialPrompt


class ExternalVideoPlayer:
    """Launches local video files in an external player process (blocking)."""

    def __init__(self) -> None:
        self._player_cmd = self._detect_player()

    @staticmethod
    def _detect_player() -> list[str] | None:
        candidates = [
            ["ffplay", "-autoexit", "-loglevel", "quiet"],
            ["mpv", "--really-quiet", "--force-window=yes", "--no-terminal"],
            ["vlc", "--play-and-exit", "--quiet"],
        ]
        for candidate in candidates:
            if shutil.which(candidate[0]):
                return candidate
        return None

    @property
    def available(self) -> bool:
        return self._player_cmd is not None

    @property
    def player_name(self) -> str:
        return self._player_cmd[0] if self._player_cmd else "none"

    def play_blocking(self, video_path: Path) -> None:
        if self._player_cmd is None:
            raise RuntimeError(
                "No supported video player found. Install one of: ffplay, mpv, vlc."
            )
        cmd = [*self._player_cmd, str(video_path)]
        subprocess.run(cmd, check=True)


class TkTrialPlayer(TrialPlayer):
    def __init__(self, root: tk.Tk, status_var: tk.StringVar) -> None:
        self.root = root
        self.status_var = status_var
        self.response_var = tk.StringVar(value="")
        self.current_prompt: TrialPrompt | None = None
        self.video_player = ExternalVideoPlayer()

        self.phase_var = tk.StringVar(value="Phase: -")
        self.order_var = tk.StringVar(value="Order: -")
        self.reference_var = tk.StringVar(value="Reference: -")
        self.candidate_var = tk.StringVar(value="Candidate: -")
        self.player_var = tk.StringVar(value=f"Video backend: {self.video_player.player_name}")

    def bind_widgets(self, frame: ttk.Frame) -> None:
        ttk.Label(frame, textvariable=self.phase_var).grid(row=0, column=0, sticky="w")
        ttk.Label(frame, textvariable=self.order_var).grid(row=1, column=0, sticky="w")
        ttk.Label(frame, textvariable=self.reference_var, wraplength=760).grid(row=2, column=0, sticky="w")
        ttk.Label(frame, textvariable=self.candidate_var, wraplength=760).grid(row=3, column=0, sticky="w")
        ttk.Label(frame, textvariable=self.player_var).grid(row=4, column=0, sticky="w")

        ttk.Label(
            frame,
            text=(
                "On each trial, videos are opened and played sequentially (Clip A then Clip B). "
                "Close each player window after playback if needed, then answer."
            ),
            wraplength=760,
        ).grid(row=5, column=0, sticky="w", pady=(6, 0))

        btns = ttk.Frame(frame)
        btns.grid(row=6, column=0, pady=10, sticky="w")
        ttk.Button(btns, text="No noticeable difference (Same)", command=lambda: self._set_response("Same")).grid(row=0, column=0, padx=4)
        ttk.Button(btns, text="Visible difference (Different)", command=lambda: self._set_response("Different")).grid(row=0, column=1, padx=4)

    def _set_response(self, val: str) -> None:
        self.response_var.set(val)

    def _play_trial_videos(self, prompt: TrialPrompt) -> None:
        if prompt.presentation_order == "reference_first":
            first_path, second_path = prompt.reference_path, prompt.candidate_path
        else:
            first_path, second_path = prompt.candidate_path, prompt.reference_path

        self.reference_var.set(f"Clip A: {first_path}")
        self.candidate_var.set(f"Clip B: {second_path}")
        self.status_var.set("Playing Clip A...")
        self.video_player.play_blocking(first_path)

        self.status_var.set("Playing Clip B...")
        self.video_player.play_blocking(second_path)
        self.status_var.set("Playback done. Respond with Same or Different...")

    def play_trial(self, prompt: TrialPrompt) -> str:
        self.current_prompt = prompt
        self.phase_var.set(f"Phase: {prompt.phase} | {prompt.label}")
        self.order_var.set(f"Presentation Order: {prompt.presentation_order}")

        if not self.video_player.available:
            raise RuntimeError(
                "No video player backend detected. Install ffplay, mpv, or vlc to run trials."
            )

        self._play_trial_videos(prompt)

        self.response_var.set("")
        self.root.wait_variable(self.response_var)
        response = self.response_var.get()
        self.status_var.set(f"Recorded response: {response}")
        return response


class SubjectiveExperimentApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Subjective Experiment GUI")
        self.root.geometry("900x560")

        self.subject_id = tk.StringVar()
        self.scene_folder = tk.StringVar()
        self.status = tk.StringVar(value="Fill subject and scene folder, then click Start.")

        main = ttk.Frame(root, padding=10)
        main.pack(fill="both", expand=True)

        form = ttk.LabelFrame(main, text="Start Screen", padding=10)
        form.pack(fill="x")
        ttk.Label(form, text="Subject ID:").grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.subject_id, width=20).grid(row=0, column=1, sticky="w", padx=5)
        ttk.Label(form, text="Scene Folder:").grid(row=1, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.scene_folder, width=70).grid(row=1, column=1, sticky="w", padx=5)
        ttk.Button(form, text="Browse", command=self._browse).grid(row=1, column=2, padx=5)
        ttk.Button(form, text="Start Experiment", command=self._start).grid(row=0, column=2, padx=5)

        trial_frame = ttk.LabelFrame(main, text="Trial Screen", padding=10)
        trial_frame.pack(fill="both", expand=True, pady=10)
        self.player = TkTrialPlayer(root, self.status)
        self.player.bind_widgets(trial_frame)

        ttk.Label(main, textvariable=self.status).pack(fill="x")

    def _browse(self) -> None:
        folder = filedialog.askdirectory()
        if folder:
            self.scene_folder.set(folder)

    def _start(self) -> None:
        if not self.subject_id.get().strip() or not self.scene_folder.get().strip():
            messagebox.showerror("Missing Input", "Please set both Subject ID and Scene Folder.")
            return

        scene_path = Path(self.scene_folder.get())
        if not scene_path.exists():
            messagebox.showerror("Invalid Folder", "Scene folder does not exist.")
            return

        self.status.set("Running training + phase1 + phase2...")
        threading.Thread(target=self._run_experiment_thread, daemon=True).start()

    def _run_experiment_thread(self) -> None:
        try:
            result = run_subjective_experiment(
                scene_folder=self.scene_folder.get(),
                subject_id=self.subject_id.get().strip(),
                player=self.player,
            )
            self.root.after(0, lambda: messagebox.showinfo("Completed", f"Experiment complete. Saved {len(result['jnd_safe_set'])} safe configs."))
            self.root.after(0, lambda: self.status.set("Experiment complete. Data saved."))
        except Exception as exc:  # runtime UI boundary
            self.root.after(0, lambda: messagebox.showerror("Experiment Error", str(exc)))
            self.root.after(0, lambda: self.status.set(f"Error: {exc}"))


def main() -> None:
    root = tk.Tk()
    SubjectiveExperimentApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
