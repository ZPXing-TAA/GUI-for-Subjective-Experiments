const RESOLUTIONS = ["VeryHigh", "High", "Medium", "Low", "Lowest"];
const FPS_PHASE1_ORDER = [45, 30, 24];
const REFERENCE_KEY = "VeryHigh|60|High|High";

const els = {
  subjectId: document.getElementById("subjectId"),
  device: document.getElementById("device"),
  actionType: document.getElementById("actionType"),
  sceneId: document.getElementById("sceneId"),
  videoInput: document.getElementById("videoInput"),
  parseBtn: document.getElementById("parseBtn"),
  startBtn: document.getElementById("startBtn"),
  parseSummary: document.getElementById("parseSummary"),
  trialMeta: document.getElementById("trialMeta"),
  leftTitle: document.getElementById("leftTitle"),
  rightTitle: document.getElementById("rightTitle"),
  leftVideo: document.getElementById("leftVideo"),
  rightVideo: document.getElementById("rightVideo"),
  sameBtn: document.getElementById("sameBtn"),
  differentBtn: document.getElementById("differentBtn"),
  skipBtn: document.getElementById("skipBtn"),
  resultView: document.getElementById("resultView"),
  downloadRaw: document.getElementById("downloadRaw"),
  downloadP1: document.getElementById("downloadP1"),
  downloadP2: document.getElementById("downloadP2"),
  downloadFinal: document.getElementById("downloadFinal"),
};

const state = {
  candidateMap: new Map(),
  invalidFiles: [],
  trialQueue: [],
  trainingQueue: [],
  currentTrial: null,
  startedAt: null,
  trialIndex: 0,
  rawTrials: [],
  phase1Result: {},
  phase2Result: {},
  finalSet: [],
};

function keyOf(config) {
  return `${config.resolution}|${config.fps}|${config.effect}|${config.shadow}`;
}

function parseFilename(filename) {
  const stem = filename.replace(/\.mp4$/i, "");
  const tokens = stem.split("_");
  if (tokens.length === 5) {
    const fps = Number(tokens[2]);
    if (!Number.isInteger(fps)) return null;
    return { resolution: tokens[0], fps, effect: tokens[3], shadow: tokens[4] };
  }
  if (tokens.length === 4) {
    const fps = Number(tokens[1]);
    if (!Number.isInteger(fps)) return null;
    return { resolution: tokens[0], fps, effect: tokens[2], shadow: tokens[3] };
  }
  return null;
}

function parseVideos() {
  state.candidateMap.clear();
  state.invalidFiles = [];
  const files = [...els.videoInput.files];
  for (const file of files) {
    const cfg = parseFilename(file.name);
    if (!cfg) {
      state.invalidFiles.push(file.name);
      continue;
    }
    const key = keyOf(cfg);
    state.candidateMap.set(key, { file, path: file.name, cfg });
  }

  const hasRef = state.candidateMap.has(REFERENCE_KEY);
  els.startBtn.disabled = !hasRef;

  els.parseSummary.textContent = JSON.stringify(
    {
      parsed: state.candidateMap.size,
      invalid: state.invalidFiles,
      has_reference: hasRef,
      reference: "VeryHigh_60_High_High (canonical config)",
    },
    null,
    2
  );
}

function buildTrainingQueue() {
  const examples = [
    { resolution: "Lowest", fps: 24, effect: "Low", shadow: "Low" },
    { resolution: "Low", fps: 24, effect: "Low", shadow: "High" },
    { resolution: "Medium", fps: 30, effect: "Low", shadow: "Low" },
  ];
  return examples
    .map((cfg) => buildTrial("training", cfg))
    .filter(Boolean)
    .slice(0, 5);
}

function buildPhase1Queue() {
  const queue = [];
  for (const resolution of RESOLUTIONS) {
    queue.push({ type: "phase1_resolution", resolution, idx: 0, lastSame: 60, done: false });
    state.phase1Result[resolution] = null;
  }
  return queue;
}

function buildTrial(phase, cfg) {
  const candidate = state.candidateMap.get(keyOf(cfg));
  const ref = state.candidateMap.get(REFERENCE_KEY);
  if (!ref) return null;
  return {
    phase,
    ...cfg,
    candidate_path: candidate?.path || null,
    reference_path: ref.path,
    candidate_file: candidate?.file || null,
    reference_file: ref.file,
  };
}

function randomLayout() {
  return Math.random() < 0.5 ? "reference_left" : "candidate_left";
}

function startExperiment() {
  resetRunState();
  state.trainingQueue = buildTrainingQueue();
  state.trialQueue = buildPhase1Queue();
  nextTrial();
}

function resetRunState() {
  state.currentTrial = null;
  state.startedAt = null;
  state.trialIndex = 0;
  state.rawTrials = [];
  state.phase1Result = {};
  state.phase2Result = {};
  state.finalSet = [];
  els.resultView.textContent = "";
}

function nextTrial() {
  const t = popNextTrial();
  if (!t) {
    finishAndRender();
    return;
  }
  presentTrial(t);
}

function popNextTrial() {
  if (state.trainingQueue.length) return state.trainingQueue.shift();

  while (state.trialQueue.length) {
    const head = state.trialQueue[0];
    if (head.type === "phase1_resolution") {
      if (head.done) {
        state.trialQueue.shift();
        continue;
      }
      const fps = FPS_PHASE1_ORDER[head.idx];
      if (!fps) {
        head.done = true;
        state.phase1Result[head.resolution] = head.lastSame === 60 ? null : head.lastSame;
        state.trialQueue.shift();
        continue;
      }
      const trial = buildTrial("phase1", { resolution: head.resolution, fps, effect: "High", shadow: "High" });
      trial._phase1Head = head;
      return trial;
    }
    if (head.type === "phase2") {
      state.trialQueue.shift();
      return buildTrial("phase2", head.cfg);
    }
  }

  // phase2 queue creation (once phase1 done)
  if (!Object.keys(state.phase1Result).length) return null;
  const phase2 = [];
  for (const resolution of RESOLUTIONS) {
    const safe = state.phase1Result[resolution];
    if (!safe) continue;
    phase2.push({ type: "phase2", cfg: { resolution, fps: safe, effect: "Low", shadow: "High" } });
    phase2.push({ type: "phase2", cfg: { resolution, fps: safe, effect: "High", shadow: "Low" } });
    phase2.push({ type: "phase2", cfg: { resolution, fps: safe, effect: "Low", shadow: "Low" } });
  }
  if (phase2.length) {
    state.trialQueue = phase2;
    return popNextTrial();
  }
  return null;
}

function presentTrial(trial) {
  state.currentTrial = trial;
  state.startedAt = performance.now();
  const layout = randomLayout();
  trial.presentation_order = layout;

  const isMissing = !trial.candidate_file;
  if (layout === "reference_left") {
    els.leftTitle.textContent = "Reference";
    els.rightTitle.textContent = "Candidate";
    els.leftVideo.src = URL.createObjectURL(trial.reference_file);
    els.rightVideo.src = isMissing ? "" : URL.createObjectURL(trial.candidate_file);
  } else {
    els.leftTitle.textContent = "Candidate";
    els.rightTitle.textContent = "Reference";
    els.leftVideo.src = isMissing ? "" : URL.createObjectURL(trial.candidate_file);
    els.rightVideo.src = URL.createObjectURL(trial.reference_file);
  }

  els.sameBtn.disabled = false;
  els.differentBtn.disabled = false;
  els.skipBtn.disabled = !isMissing;
  els.trialMeta.textContent = `${trial.phase.toUpperCase()} | ${trial.resolution} ${trial.fps}fps effect:${trial.effect} shadow:${trial.shadow}${
    isMissing ? " | candidate missing: can Skip" : ""
  }`;
}

function answer(response) {
  const t = state.currentTrial;
  if (!t) return;

  const rt = (performance.now() - state.startedAt) / 1000;
  const rec = {
    subject_id: els.subjectId.value || "UNKNOWN",
    device: els.device.value || "UNKNOWN",
    action_type: els.actionType.value,
    scene_id: els.sceneId.value || "UNKNOWN",
    phase: t.phase,
    trial_index: ++state.trialIndex,
    resolution: t.resolution,
    fps: t.fps,
    effect: t.effect,
    shadow: t.shadow,
    presentation_order: t.presentation_order,
    response,
    response_time: Number(rt.toFixed(3)),
    timestamp: new Date().toISOString(),
  };

  if (t.phase !== "training") {
    state.rawTrials.push(rec);
  }

  if (t.phase === "phase1") {
    const head = t._phase1Head;
    if (response === "Same") {
      head.lastSame = t.fps;
      head.idx += 1;
      if (head.idx >= FPS_PHASE1_ORDER.length) {
        head.done = true;
        state.phase1Result[head.resolution] = head.lastSame;
      }
    } else {
      head.done = true;
      state.phase1Result[head.resolution] = head.lastSame === 60 ? null : head.lastSame;
    }
  }

  if (t.phase === "phase2" && response === "Same") {
    state.phase2Result[t.resolution] ||= [];
    state.phase2Result[t.resolution].push({ fps: t.fps, effect: t.effect, shadow: t.shadow });
  }

  nextTrial();
}

function finishAndRender() {
  state.finalSet = Object.entries(state.phase2Result).flatMap(([resolution, configs]) =>
    configs.map((cfg) => ({ resolution, ...cfg }))
  );

  const finalPayload = {
    device: els.device.value || "UNKNOWN",
    action_type: els.actionType.value,
    scene_id: els.sceneId.value || "UNKNOWN",
    jnd_safe_set: state.finalSet,
  };

  els.resultView.textContent = JSON.stringify(
    {
      raw_trial_log: { subject_id: els.subjectId.value || "UNKNOWN", trials: state.rawTrials },
      phase1_result: state.phase1Result,
      phase2_result: state.phase2Result,
      final_jnd_safe_set: finalPayload,
    },
    null,
    2
  );

  const rawPayload = { subject_id: els.subjectId.value || "UNKNOWN", trials: state.rawTrials };
  setDownload(els.downloadRaw, "raw_trial_log.json", rawPayload);
  setDownload(els.downloadP1, "phase1_result.json", state.phase1Result);
  setDownload(els.downloadP2, "phase2_result.json", state.phase2Result);
  setDownload(els.downloadFinal, "final_jnd_safe_set.json", finalPayload);

  [els.sameBtn, els.differentBtn, els.skipBtn].forEach((b) => (b.disabled = true));
  els.trialMeta.textContent = "Session complete.";
}

function setDownload(button, filename, payload) {
  button.disabled = false;
  button.onclick = () => {
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };
}

els.parseBtn.addEventListener("click", parseVideos);
els.startBtn.addEventListener("click", startExperiment);
els.sameBtn.addEventListener("click", () => answer("Same"));
els.differentBtn.addEventListener("click", () => answer("Different"));
els.skipBtn.addEventListener("click", () => answer("Skipped"));
