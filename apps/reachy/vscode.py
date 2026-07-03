"""VS Code control plane bridge for Hermes conductor."""
from __future__ import annotations

import os
import subprocess
import webbrowser
from pathlib import Path, PureWindowsPath
from urllib.parse import quote

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

CODE_CMD = "code"


def _file_uri(path: str) -> str:
    p = Path(path).resolve()
    if os.name == "nt":
        # vscode-uri expects: vscode://file/c/Users/... or vscode://file//c/Users/...
        # normalize to absolute with POSIX-style separators
        text = str(PureWindowsPath(p).as_posix())
        if not text.startswith("///"):
            if text.startswith("//"):
                text = text[0] + "/" + text
            else:
                text = "/" + text
            text = "/" + text
        escaped = quote(text, safe="/")
        return f"vscode://file{escaped}"
    return f"vscode://file{quote(str(p), safe='/')}"


def _open_uri(uri: str) -> dict:
    try:
        opened = bool(webbrowser.open(uri, new=2))
        return {"ok": opened, "rc": 0 if opened else 1, "stdout": "opened" if opened else "", "stderr": "" if opened else "browser launch failed"}
    except Exception as e:
        return {"ok": False, "rc": 2, "stdout": "", "stderr": str(e)}


def _run(args: list[str]) -> dict:
    try:
        p = subprocess.run(
            [CODE_CMD, *args],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return {
            "ok": p.returncode == 0,
            "rc": p.returncode,
            "stdout": p.stdout.strip(),
            "stderr": p.stderr.strip(),
        }
    except Exception as e:
        return {"ok": False, "rc": 2, "stdout": "", "stderr": str(e)}


@router.post("/vscode/command")
async def vscode_command(payload: dict) -> JSONResponse:
    args = list(payload.get("args", []) or [])
    result = _run(args)
    return JSONResponse(result)


@router.post("/vscode/open")
async def vscode_open(payload: dict) -> JSONResponse:
    target = str(payload.get("path", ".")).strip()
    target_path = Path(target)
    if not target_path.exists():
        target_path = Path(".").resolve()
    try:
        uri = _file_uri(str(target_path))
        return JSONResponse(_open_uri(uri))
    except Exception as e:
        result = _run([str(target_path)])
        result["stderr"] = str(e) + ("\n" + result["stderr"] if result.get("stderr") else "")
        return JSONResponse(result)


@router.post("/vscode/uri")
async def vscode_uri(payload: dict) -> JSONResponse:
    uri = str(payload.get("uri", "")).strip()
    if not uri:
        return JSONResponse({"ok": False, "rc": 2, "stdout": "", "stderr": "missing uri"})
    if uri.lower().startswith("vscode://"):
        return JSONResponse(_open_uri(uri))
    return JSONResponse({"ok": False, "rc": 2, "stdout": "", "stderr": f"unsupported uri: {uri}"})


@router.get("/vscode/status")
async def vscode_status() -> JSONResponse:
    try:
        p = subprocess.run(
            [CODE_CMD, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return JSONResponse({
            "ok": p.returncode == 0,
            "rc": p.returncode,
            "stdout": p.stdout.strip(),
            "stderr": p.stderr.strip(),
        })
    except Exception as e:
        return JSONResponse({"ok": False, "rc": 2, "stdout": "", "stderr": str(e)})
