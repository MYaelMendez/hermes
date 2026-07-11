from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class VSInstallation:
    instance_id: str
    install_path: Optional[str]
    catalog_sdk_image: Optional[str]
    install_date: Optional[str]
    version: Optional[str]
    state: Optional[str]


class VSInstallerError(RuntimeError):
    ...


class VSInstaller:
    DEFAULT_INSTALLER = Path(
        r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vs_installer.exe"
    )
    DEFAULT_VSWHERE = Path(
        r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"
    )

    def __init__(
        self,
        installer: Optional[Path] = None,
        vswhere: Optional[Path] = None,
    ) -> None:
        self.installer = installer or self.DEFAULT_INSTALLER
        self.vswhere = vswhere or self.DEFAULT_VSWHERE
        if not self.installer.exists():
            raise VSInstallerError(f"vs_installer not found: {self.installer}")
        if not self.vswhere.exists():
            raise VSInstallerError(f"vswhere not found: {self.vswhere}")

    def list_installed(self) -> List[VSInstallation]:
        raw = self._run_vswhere(["-latest", "-products", "*", "-requires", "Microsoft.Component.MSBuild", "-property", "installationPath,catalog_sdk_image,installDate,productVersion,state,instanceId"])
        installs: List[VSInstallation] = []
        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("["):
                continue
            parts = line.split("|")
            if len(parts) < 6:
                continue
            installs.append(
                VSInstallation(
                    instance_id=parts[0],
                    install_path=parts[1] or None,
                    catalog_sdk_image=parts[2] or None,
                    install_date=parts[3] or None,
                    version=parts[4] or None,
                    state=parts[5] or None,
                )
            )
        if not installs:
            raw = self._run_vswhere(["-products", "*", "-property", "installationPath", "-format", "json"])
            try:
                data = json.loads(raw)
                for item in data:
                    installs.append(
                        VSInstallation(
                            instance_id=str(item.get("instanceId", "")),
                            install_path=str(item.get("installationPath")) or None,
                            catalog_sdk_image=str(item.get("catalog", {}).get("buildBranch")) or None,
                            install_date=str(item.get("installDate")) or None,
                            version=str(item.get("productVersion")) or None,
                            state=str(item.get("state")) or None,
                        )
                    )
            except json.JSONDecodeError:
                ...
        return installs

    def run_installer(
        self,
        install_path: Optional[str] = None,
        workloads: Optional[List[str]] = None,
        components: Optional[List[str]] = None,
        channel: Optional[str] = None,
        catalog: Optional[str] = None,
        wait: bool = True,
    ) -> Dict[str, Any]:
        args: List[str] = [str(self.installer), "modify"]
        if install_path:
            args.append(f'--installPath "{install_path}"')
        if channel:
            args.append(f"--channelUri {channel}")
        if catalog:
            args.append(f'--catalog {catalog}')
        if workloads:
            for w in workloads:
                args.append(f"--add {w}")
        if components:
            for c in components:
                args.append(f"---add {c}")
        args.append("--quiet")
        args.append("--wait")
        code, out, err = self._run_cmd(args, wait=wait)
        return {"ok": code == 0, "rc": code, "stdout": out, "stderr": err, "surface": {"kind": "vs_installer", "command": " ".join(args)}}

    def export_layout(
        self, layout_path: Path, channel: Optional[str] = None, lang: str = "en-US"
    ) -> Dict[str, Any]:
        cmd = [
            str(self.installer),
            "layout",
            "--lang",
            lang,
        ]
        if channel:
            cmd.append(f"--channelUri {channel}")
        cmd.append(str(layout_path))
        code, out, err = self._run_cmd(cmd)
        return {"ok": code == 0, "rc": code, "stdout": out, "stderr": err, "surface": {"kind": "vs_installer", "command": " ".join(cmd)}}

    def _run_vswhere(self, args: List[str]) -> str:
        return self._run_cmd([str(self.vswhere)] + args)[1]

    def _run_cmd(self, args: List[str], wait: bool = True) -> tuple[int, str, str]:
        cmd = " ".join(args)
        try:
            proc = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                check=False,
            )
            if wait or proc.returncode is not None:
                return proc.returncode, proc.stdout, proc.stderr
            return 0, "", ""
        except FileNotFoundError as exc:
            raise VSInstallerError(f"command not found: {exc.filename}") from exc
        except OSError as exc:
            raise VSInstallerError(str(exc)) from exc

    def to_dict(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return payload


__all__ = ["VSInstaller", "VSInstallerError", "VSInstallation"]
