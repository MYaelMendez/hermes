"""Tests for hermes_runtime.vscode detection."""
from __future__ import annotations

from pathlib import Path

from hermes_runtime.vscode import VSCodeRuntime, detect, _resolve_version


class FakeProcess:
    def __init__(self, *, returncode, stdout, stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _fake_subprocess_run(args, **kwargs):
    if args[-1] == "--version":
        return FakeProcess(returncode=0, stdout="1.95.0\n")
    return FakeProcess(returncode=1, stdout="", stderr="not found")


def _resolve_version_stub(args, **kwargs):
    if args[-1] == "--version":
        return FakeProcess(returncode=0, stdout="1.95.0\n")
    return FakeProcess(returncode=1, stdout="", stderr="not found")


def _fake_exists(path):
    return path.samefile(Path(r"C:\Program Files\Microsoft VS Code\Code.exe")) if str(path).endswith("Code.exe") else False


def test_detect_system_install(monkeypatch, tmp_path):
    user_appdata = tmp_path / "localappdata"
    fake_exe = user_appdata / "Programs" / "Microsoft VS Code" / "Code.exe"
    fake_exe.mkdir(parents=True, exist_ok=True)

    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(user_appdata))
    monkeypatch.setattr(Path, "exists", lambda path: Path(path) == fake_exe)
    monkeypatch.setattr("hermes_runtime.vscode.subprocess.run", _fake_subprocess_run)

    runtime = detect()
    assert runtime.installed is True
    assert Path(runtime.executable_path) == fake_exe
    assert runtime.version == "1.95.0"
    assert runtime.install_dir is not None
    assert "Microsoft VS Code" in runtime.install_dir
    assert runtime.extensions_dir is not None
    assert runtime.extensions_dir.endswith("extensions")


def test_detect_user_installed_fallback(monkeypatch, tmp_path):
    user_appdata = tmp_path / "localappdata"
    pf_exe = Path(r"C:\\Program Files\\Microsoft VS Code\\Code.exe")
    user_exe = user_appdata / "Programs" / "Microsoft VS Code" / "Code.exe"
    user_exe.mkdir(parents=True, exist_ok=True)

    def fake_exists(path):
        return Path(path) == user_exe

    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(user_appdata))
    monkeypatch.setattr(Path, "exists", fake_exists)
    monkeypatch.setattr("hermes_runtime.vscode.subprocess.run", _fake_subprocess_run)

    runtime = detect()
    assert runtime.installed is True
    assert Path(runtime.executable_path) == user_exe
    assert runtime.version == "1.95.0"
    assert runtime.user_dir == str(user_appdata / "Programs" / "Microsoft VS Code")
    assert runtime.extensions_dir == str(runtime.user_dir) + "\\extensions"


def test_detect_no_install(monkeypatch):
    monkeypatch.setattr(Path, "exists", lambda path: False)
    runtime = detect()
    assert runtime.installed is False
    assert runtime.executable_path is None
    assert runtime.version is None
    assert runtime.extensions_dir is None


def test_resolve_version_returns_first_line(monkeypatch):
    captured: list[list[str]] = []

    def fake_run(args, **kwargs):
        captured.append(args)
        return FakeProcess(returncode=0, stdout="1.95.0\nabcd\n")

    monkeypatch.setattr("hermes_runtime.vscode.subprocess.run", fake_run)
    ver = _resolve_version(Path(r"C:\Program Files\Microsoft VS Code\Code.exe"))
    assert ver == "1.95.0"


def test_resolve_version_handles_failure(monkeypatch):
    monkeypatch.setattr("hermes_runtime.vscode.subprocess.run", lambda args, **kwargs: FakeProcess(returncode=1, stdout="", stderr="error"))
    ver = _resolve_version(Path(r"C:\Program Files\Microsoft VS Code\Code.exe"))
    assert ver is None
