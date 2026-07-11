"""Reachy Mini local-first operator surface for HuggingFace Space."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from apps.reachy.sim_bridge import router as sim_router
from apps.reachy.vscode import router as vscode_router
from apps.reachy.mcp_tools import router as mcp_tools_router
from apps.reachy.ae_coding_conductor import router as ae_coding_router
from apps.reachy.vlc_wrapper import VLCController, vlc_fleet
from apps.reachy.vs_installer import VSInstaller
from apps.reachy.windows_desktop import WindowsDesktop
from hermes_cli.conductor import run_hermes
from hermes_runtime.victus_superagent import VictusSuperagent

REPO = Path(__file__).resolve().parents[2]


def require_template(path: str) -> str:
    target = REPO / path
    if not target.exists():
        raise FileNotFoundError(f"template not found: {target}")
    return target.read_text(encoding="utf-8")


INDEX = require_template("templates/hermes-reachy-marketplace.html")
LOCAL_AI = require_template("templates/hermes-local-ai.html")


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


@dataclass
class ReachyState:
    reachable: bool = False
    effector: str = "idle"
    telemetry: dict[str, object] | None = None
    updated: str = now_iso()


state = ReachyState()
app = FastAPI(title="Hermes Reachy", version="0.3")
app.include_router(sim_router)
app.include_router(vscode_router)
app.include_router(mcp_tools_router)
app.include_router(ae_coding_router)
STATIC_ROOT = Path(__file__).resolve().parents[2] / "apps" / "reachy"
app.mount("/static", StaticFiles(directory=str(STATIC_ROOT)), name="reachy-static")

superagent = VictusSuperagent()
_installer = VSInstaller()
_desktop = WindowsDesktop()


@app.get("/", response_class=HTMLResponse)
async def index(_: Request) -> HTMLResponse:
    return HTMLResponse(INDEX)


@app.get("/local-ai", response_class=HTMLResponse)
async def local_ai(_: Request) -> HTMLResponse:
    return HTMLResponse(LOCAL_AI)


@app.post("/reachy/probe")
async def reachy_probe() -> JSONResponse:
    state.reachable = True
    state.effector = "idle"
    state.telemetry = {"command": "probe", "surface": "local"}
    state.updated = now_iso()
    return JSONResponse({"ok": True, "state": asdict(state)})


@app.post("/reachy/panel")
async def reachy_panel() -> JSONResponse:
    state.reachable = True
    state.effector = "panel_open"
    state.telemetry = {"command": "panel", "surface": "local"}
    state.updated = now_iso()
    return JSONResponse({"ok": True, "state": asdict(state)})


@app.post("/reachy/status")
async def reachy_status() -> JSONResponse:
    return JSONResponse({"ok": True, "state": asdict(state)})


@app.post("/conductor")
async def conductor(payload: dict) -> JSONResponse:
    cmd = str(payload.get("cmd", "")).strip()
    args = list(payload.get("args", []) or [])
    if not cmd:
        return JSONResponse({"ok": False, "rc": 2, "stdout": "", "stderr": "missing cmd"})
    try:
        from hermes_cli.conductor import run as conductor_run, _serialize_mech_lang, _is_scheme_cmd
    except Exception as e:
        return JSONResponse({"ok": False, "rc": 3, "stdout": "", "stderr": f"conductor unavailable: {e}"})
    if _is_scheme_cmd(cmd):
        return JSONResponse(_serialize_mech_lang(conductor_run(cmd, args)))
    return JSONResponse(conductor_run(cmd, args))


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"ok": True, "service": "hermes-reachy"})


@app.post("/vlc/play")
async def vlc_play(payload: dict) -> JSONResponse:
    target = str((payload or {}).get("target", "")).strip()
    if not target:
        return JSONResponse({
            "ok": False,
            "rc": 2,
            "stdout": "",
            "stderr": "missing target",
            "surface": {
                "kind": "vlc_surface",
                "address": "vlc://play/",
                "target": "",
                "runtime": "hermes-code",
            },
        })
    try:
        result = VLCController.play(target)
    except Exception as e:
        return JSONResponse({
            "ok": False,
            "rc": 1,
            "stdout": "",
            "stderr": str(e),
            "surface": {
                "kind": "vlc_surface",
                "address": f"vlc://play/{target}",
                "target": target,
                "runtime": "hermes-code",
            },
        })
    surface = {
        "kind": "vlc_surface",
        "address": f"vlc://play/{result.get('target', target)}",
        "target": result.get("target", target),
        "runtime": result.get("runtime", "hermes-code"),
    }
    return JSONResponse({
        "ok": bool(result.get("ok")),
        "rc": int(result.get("rc", 0)),
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
        "surface": surface,
    })


@app.post("/vlc/fleet/status")
async def vlc_fleet_status() -> JSONResponse:
    return JSONResponse(vlc_fleet.dispatch("vlc://fleet status"))


@app.post("/vlc/fleet/play")
async def vlc_fleet_play(payload: dict) -> JSONResponse:
    target = str((payload or {}).get("target", "")).strip()
    return JSONResponse(vlc_fleet.dispatch(f"vlc://fleet play {target}".strip()))


@app.post("/vlc/fleet/stop")
async def vlc_fleet_stop() -> JSONResponse:
    return JSONResponse(vlc_fleet.dispatch("vlc://fleet stop"))


@app.post("/vlc/fleet/fullscreen")
async def vlc_fleet_fullscreen() -> JSONResponse:
    return JSONResponse(vlc_fleet.dispatch("vlc://fleet fullscreen"))


@app.post("/vlc/fleet/runtime")
async def vlc_fleet_runtime() -> JSONResponse:
    return JSONResponse(vlc_fleet.dispatch("vlc://fleet runtime"))


@app.post("/vitals")
async def vitals_collect(payload: dict | None = None) -> JSONResponse:
    return JSONResponse(superagent.gauntlet())


@app.post("/vitals/history")
async def vitals_history() -> JSONResponse:
    return JSONResponse({"ok": True, "history": superagent.history(limit=128)})


@app.post("/vitals/throttle")
async def vitals_throttle(payload: dict) -> JSONResponse:
    cpu_max = float((payload or {}).get("cpu_max", 90.0))
    memory_max = float((payload or {}).get("memory_max", 90.0))
    superagent._machine_limit_threshold = max(cpu_max, memory_max)
    return JSONResponse({
        "ok": True,
        "machine_limit_threshold": superagent._machine_limit_threshold,
        "surface": {"kind": "vitals", "action": "throttle"},
    })


@app.post("/windows/control")
async def windows_control(payload: dict) -> JSONResponse:
    cmd = str((payload or {}).get("cmd", "")).strip()
    if not cmd.startswith("computer://"):
        return JSONResponse({"ok": False, "rc": 2, "stdout": "", "stderr": "missing computer:// cmd"})
    if "enumerate" in cmd:
        return JSONResponse(_serialize(_desktop.enumerate()))
    return JSONResponse(_desktop.dispatch(cmd))


@app.post("/windows/enumerate")
async def windows_enumerate() -> JSONResponse:
    return JSONResponse(_serialize(_desktop.enumerate()))


@app.post("/windows/focus")
async def windows_focus(payload: dict) -> JSONResponse:
    title = str((payload or {}).get("title", "")).strip()
    if not title:
        return JSONResponse({"ok": False, "rc": 2, "stdout": "", "stderr": "missing title"})
    return JSONResponse(_serialize(_desktop.focus(title)))


@app.post("/windows/type")
async def windows_type(payload: dict) -> JSONResponse:
    text = str((payload or {}).get("text", "")).strip()
    return JSONResponse(_serialize(_desktop.type_text(text)))


@app.post("/vs/list")
async def vs_list() -> JSONResponse:
    try:
        installs = _installer.list_installed()
    except Exception as exc:
        return JSONResponse({"ok": False, "stderr": str(exc), "installs": []})
    return JSONResponse({
        "ok": True,
        "installs": [_serialize_install(i) for i in installs],
    })


@app.post("/vs/install")
async def vs_install(payload: dict) -> JSONResponse:
    payload = payload or {}
    try:
        cmd = str(payload.get("cmd", "modify")).strip()
        log = str(payload.get("log", "")).strip()
        workload = _to_list(payload.get("workloads", []))
        component = _to_list(payload.get("components", []))
        channel = str(payload.get("channel", "release")).strip()
        install_path = str(payload.get("install_path", "")).strip() or None
        result = _installer.run_installer(
            cmd=cmd,
            log=log or None,
            workloads=workload or None,
            components=component or None,
            channel=channel or None,
            install_path=install_path,
        )
    except Exception as exc:
        return JSONResponse({"ok": False, "rc": 3, "stderr": str(exc), "surface": _vs_surface()})
    output = _serialize(result) if not isinstance(result, str) else {"ok": True, "stdout": result}
    output.setdefault("surface", _vs_surface())
    return JSONResponse(output)


def _vs_surface() -> dict:
    return {"kind": "vs_installer", "runtime": "hermes-code", "address": "vs://"}


def _serialize(value: object) -> object:
    try:
        from dataclasses import asdict as _asdict
        if hasattr(value, "__dataclass_fields__"):
            return _asdict(value)
        if isinstance(value, list):
            return [_serialize(item) for item in value]
    except Exception:
        pass
    return value


def _serialize_install(install: "apps.reachy.vs_installer.VSInstallation") -> dict:
    return {
        "instance_id": install.instance_id,
        "install_path": install.install_path,
        "catalog_sdk_image": install.catalog_sdk_image,
        "install_date": install.install_date,
        "version": install.version,
        "state": install.state,
    }


def _to_list(value: object) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
