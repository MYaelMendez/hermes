# Hermes Code Player / llm.store VLC Skin Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Rebuild VLC Media Player’s installer/runtime state into a Hermes-controlled local surface and design a llm.store skin that treats VLC as Chromium-like runtime for LLMs/SLMs/agents/media.

**Architecture:**
- Hermes conductor owns auth/runtime/state/install path on Victus.
- VLC becomes the host viewport via Lua extension + optional HTTP interface + native control wrapper.
- llm.store skin shows models/agents as first-class “channels” alongside video/audio.
- Extension/cmd layer bridges `vlc://`, `ffmpeg://`, `vscode://`, `mcp://`, `sim://`, `pc://`.

**Tech Stack:** Python 3.11, VLC Lua extensions, libvlcopt HTTP interface, Windows native control, Hermes conductor dispatcher, Tauri later if needed.

---

## Task 1: Inspect runtime spec files and installer surface

- Modify: `C:\æ\hermes-fork\hermes_cli\conductor.py`
- Create: `C:\æ\hermes-fork\apps\reachy\vlc_runtime.py`
- Test: targeted pytest on conductor

Step 1: locate VLC install path and appdata Lua folder on Victus.

Command:
```
python - <<'PY'
from pathlib import Path
for p in [Path(r"C:\Program Files\VideoLAN\VLC\vlc.exe"), Path(r"C:\Users\yaelm\AppData\Roaming\vlc\lua\extensions")]:
    print(p, p.exists(), p)
PY
```

Step 2: create VLC runtime state class, cached shallow inspection.

Expected result: class reports install presence and writable Lua ext path.

Step 3: verify pytest still reports 11 passed.

---

## Task 2: Add Hermes `vlc://runtime` dispatcher surface

- Modify: `C:\æ\hermes-fork\hermes_cli\conductor.py`
- Test: add targeted test for new dispatcher route

Step 1: add `vlc://runtime status`, `vlc://runtime path`, and `vlc://runtime install` route.

Step 2: register in `_DISPATCHER` and emit `mech_lang` tokens.

Step 3: run pytest.

Expected: 11 passed with new schema visible in conductor output.

---

## Task 3: Create installer hook module for VLC runtime state

- Create: `C:\æ\hermes-fork\apps\reachy\vlc_runtime.py`
- Modify: bridge mount if desired to expose `/vlc/runtime`

Step 1: implement detection helpers:
- install path lookup
- Lua extension folder creation
- presence check for `vlc.exe`

Step 2: add Hermes-side status object:
```
{
  "ok": true,
  "installed": bool,
  "install_path": str|None,
  "lua_extensions": str|None,
  "runtime": "hermes-code"
}
```

Step 3: run pytest on conductor only if this module has direct tests; otherwise mark creative-surface exempt per user conventions.

---

## Task 4: Wire `/vlc/runtime` live on 7860 Hermes Code bridge

- Modify: `C:\æ\hermes-fork\apps\reachy\app.py`

Step 1: add FastAPI endpoints:
- GET `/vlc/runtime`
- POST `/vlc/runtime/install`

Step 2: reuse `vlc_runtime.py` for all filesystem decisions; no inline code in `app.py`.

Step 3: reload bridge once the port-conflict issue is resolved by managing a single running process.

Step 4: smoke test:
```
curl -s http://127.0.0.1:7860/vlc/runtime
```

Expected: JSON runtime state with install path and Lua path.

---

## Task 5: Create llm.store VLC skin concept spec

- Create: `C:\æ\hermes-fork\templates\llm-store-vlc-skin.md`

Step 1: document home layout mapping; examples:
- left: media queue
- center: runtime/viewport
- right: model/agent/control panel

Step 2: define llm.store UX semantics as media analog:
- channel = model/SLM
- playlist = agent task queue
- bookmark = toolcall/trace
- metadata = capability card + mech_lang token

Step 3: store concept in repo for later implementation.

---

## Task 6: Begin packaging wrapper for installer runtime state

- Create: `C:\æ\hermes-fork\apps\reachy\vlc_wrapper.py`
- Modify: `C:\æ\hermes-fork\hermes_cli\conductor.py`

Step 1: move `VLCController` launch/status/control into shared wrapper class.

Step 2: conductor keeps dispatcher functions but delegates to module.

Step 3: pytest conductor still 11 passed.

---

## Commit cadence
- After each completed subtask: `git add <files>` then `git commit -m "feat: <subtask description>"`
- No broad refactors; keep style matching surrounding code.

---

## Verification commands
```
cd C:/æ/hermes-fork && python -m pytest tests/hermes_cli/test_conductor.py -q --timeout=60
```

## Notes
- Windows path handling should use `pathlib`.
- No future runtime service paths should be hardcoded elsewhere without reusing `vlc_runtime.py`.
- Keep scalar governance exemptions scoped.
