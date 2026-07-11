from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VLCRuntime:
    installed: bool
    install_path: str | None
    lua_root: str | None
    extensions_dir: str | None
    default_profiles_dir: str | None
    roaming_vlc: str | None


def _default_roaming_appdata() -> str | None:
    try:
        return os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    except Exception:
        return None


def detect() -> VLCRuntime:
    roaming_root = _default_roaming_appdata()
    roaming_vlc = None
    lua_root = None
    extensions_dir = None
    default_profiles_dir = None

    if roaming_root:
        roaming_vlc = str(Path(roaming_root) / "vlc")
        lua_root = str(Path(roaming_vlc) / "lua")
        extensions_dir = str(Path(lua_root) / "extensions")
        default_profiles_dir = str(Path(lua_root) / "skins2")

    install_candidates = [
        Path(r"C:\Program Files\VideoLAN\VLC\vlc.exe"),
        Path(r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"),
    ]
    install_path = next((str(p) for p in install_candidates if p.exists()), None)

    return VLCRuntime(
        installed=install_path is not None,
        install_path=install_path,
        lua_root=lua_root,
        extensions_dir=extensions_dir,
        default_profiles_dir=default_profiles_dir,
        roaming_vlc=roaming_vlc,
    )


def ensure_dirs(runtime: VLCRuntime) -> VLCRuntime:
    for path in [runtime.lua_root, runtime.extensions_dir, runtime.default_profiles_dir]:
        if not path:
            continue
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
    return runtime
