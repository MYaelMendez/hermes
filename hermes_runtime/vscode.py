"""VS Code runtime detector for Hermes.

OS-aware, deterministic detector for local VS Code installs on Windows. Checks
common system and user install locations and returns a normalized runtime record
(installed, version if discoverable, executable path or None).

No external API calls or credentials.
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VSCodeRuntime:
    installed: bool
    executable_path: str | None
    version: str | None
    install_dir: str | None
    user_dir: str | None
    extensions_dir: str | None


def _default_local_appdata() -> str | None:
    try:
        return os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    except Exception:
        return None


_INSTALL_CANDIDATES = (
    Path(r"C:\Program Files\Microsoft VS Code\Code.exe"),
    Path(r"C:\Program Files (x86)\Microsoft VS Code\Code.exe"),
)


def _resolve_version(executable: Path) -> str | None:
    try:
        result = subprocess.run(
            [str(executable), "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            shell=False,
        )
        if result.returncode == 0:
            return result.stdout.strip().splitlines()[0] or None
    except Exception:
        pass
    return None


def detect() -> VSCodeRuntime:
    executable_path: str | None = None
    install_dir: str | None = None
    version: str | None = None

    for candidate in _INSTALL_CANDIDATES:
        if candidate.exists():
            executable_path = str(candidate)
            install_dir = str(candidate.parent)
            version = _resolve_version(candidate)
            break

    if not executable_path:
        localappdata = _default_local_appdata()
        if localappdata:
            user_exe = Path(localappdata) / "Programs" / "Microsoft VS Code" / "Code.exe"
            if user_exe.exists():
                executable_path = str(user_exe)
                install_dir = str(user_exe.parent)
                version = _resolve_version(user_exe)

    installed = executable_path is not None

    user_dir: str | None = None
    extensions_dir: str | None = None

    if installed:
        localappdata = _default_local_appdata()
        if localappdata:
            user_dir = str(Path(localappdata) / "Programs" / "Microsoft VS Code")
            extensions_dir = str(Path(user_dir) / "extensions")

    return VSCodeRuntime(
        installed=installed,
        executable_path=executable_path,
        version=version,
        install_dir=install_dir,
        user_dir=user_dir,
        extensions_dir=extensions_dir,
    )
