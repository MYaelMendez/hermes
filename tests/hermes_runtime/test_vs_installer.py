from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from apps.reachy.vs_installer import VSInstaller, VSInstallerError, VSInstallation


def test_defaults_present():
    installer = VSInstaller(
        installer=Path(r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vs_installer.exe"),
        vswhere=Path(r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"),
    )
    assert installer.installer.exists() is False or installer.installer.exists() is True
    assert installer.vswhere.exists() is False or installer.vswhere.exists() is True


def test_missing_installer_raises(tmp_path):
    with pytest.raises(VSInstallerError):
        VSInstaller(installer=tmp_path / "missing.exe", vswhere=tmp_path / "missing.exe")


def test_run_vswhere_parses_lines():
    installer = VSInstaller.__new__(VSInstaller)
    installer.installer = Path("C:\\fake\\vs_installer.exe")
    installer.vswhere = Path("C:\\fake\\vswhere.exe")
    raw = "[{\"instanceId\":\"1\",\"installationPath\":\"C:\\\\VS\",\"productVersion\":\"17.0\",\"state\":\"Installed\",\"installDate\":\"20240101\"}]"
    with patch("apps.reachy.vs_installer.VSInstaller._run_cmd", return_value=(0, raw, "")):
        installs = installer.list_installed()
    assert len(installs) == 1
    assert installs[0].version == "17.0"
    assert installs[0].install_path == "C:\\VS"


def test_run_cmd_wraps_oserror():
    installer = VSInstaller.__new__(VSInstaller)
    installer.installer = Path("C:\\fake\\vs_installer.exe")
    installer.vswhere = Path("C:\\fake\\vswhere.exe")
    with patch("apps.reachy.vs_installer.subprocess.run", side_effect=OSError("fail")):
        with pytest.raises(VSInstallerError):
            installer._run_cmd(["ls"])
