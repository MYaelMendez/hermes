from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from apps.reachy.windows_desktop import WindowsDesktop


@pytest.fixture()
def desktop(monkeypatch):
    desktop = WindowsDesktop()
    user32 = MagicMock()
    kernel32 = MagicMock()
    monkeypatch.setattr("apps.reachy.windows_desktop.user32", user32)
    monkeypatch.setattr("apps.reachy.windows_desktop.kernel32", kernel32)
    monkeypatch.setattr("apps.reachy.windows_desktop.ctypes", MagicMock())
    desktop.user32 = user32
    desktop.kernel32 = kernel32
    return desktop, user32, kernel32


def test_enumerate_windows(desktop):
    desktop_obj, user32, _ = desktop
    user32.IsWindowVisible.return_value = True
    user32.GetWindowTextLengthW.side_effect = lambda hwnd: 4 if hwnd == 1 else 0
    user32.GetWindowTextW.side_effect = lambda hwnd, buf, n: 0 if hwnd == 1 else 0
    user32.GetClassNameW.return_value = 4
    user32.GetWindowThreadProcessId.side_effect = lambda hwnd, pidptr: MagicMock()
    user32.GetWindowRect.return_value = 1
    wins = desktop_obj.enumerate()
    assert isinstance(wins, list)
    assert user32.EnumWindows.called


def test_focus_window(desktop):
    desktop_obj, user32, _ = desktop
    user32.IsWindowVisible.return_value = True
    user32.GetWindowTextLengthW.return_value = 3
    user32.GetWindowTextW.return_value = 3
    user32.GetClassNameW.return_value = 4
    user32.GetWindowThreadProcessId.side_effect = lambda hwnd, pidptr: None
    user32.GetWindowRect.return_value = 1
    user32.ShowWindow.return_value = 1
    user32.SetForegroundWindow.return_value = 1

    class FakeWin:
        hwnd = 123
        title = "vlc"
    desktop_obj.enumerate = MagicMock(return_value=[FakeWin()])
    result = desktop_obj.focus("vlc")
    assert result.ok is True
    assert result.surface["action"] == "focus"


def test_minimize_all(desktop):
    desktop_obj, user32, _ = desktop
    result = desktop_obj.minimize_all()
    assert result.ok is True
    assert result.stdout == "minimize_all"


def test_type_text(desktop):
    desktop_obj, user32, _ = desktop
    user32.SendInput.return_value = 1
    result = desktop_obj.type_text("ab")
    assert result.ok is True
    assert result.stdout == "ab"
    assert user32.SendInput.call_count == 2


def test_launch_success(desktop, monkeypatch, tmp_path):
    desktop_obj, user32, _ = desktop
    target = tmp_path / "fake_app.exe"
    target.write_text("x")
    monkeypatch.setattr(Path, "exists", lambda self: False, raising=False)
    result = desktop_obj.launch(str(target))
    assert result.ok is False
    assert "executable not found" in result.stderr

