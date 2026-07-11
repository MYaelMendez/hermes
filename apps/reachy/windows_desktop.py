from __future__ import annotations

import ctypes
import subprocess
import ctypes.wintypes as wt
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from hermes_runtime.computer_use import user32, kernel32, _INPUT, _INPUT_UNION, _KEYBDINPUT, _MOUSEINPUT
from hermes_runtime.computer_use import (
    INPUT_MOUSE,
    INPUT_KEYBOARD,
    KEYEVENTF_KEYUP,
    KEYEVENTF_UNICODE,
    MOUSEEVENTF_LEFTDOWN,
    MOUSEEVENTF_LEFTUP,
    MOUSEEVENTF_MOVE,
    MOUSEEVENTF_ABSOLUTE,
    VK_LWIN,
)


@dataclass
class WinWindow:
    hwnd: int
    title: str
    cls: str
    pid: int
    rect: tuple[int, int, int, int]
    visible: bool


@dataclass
class DesktopControlResult:
    ok: bool
    stdout: str = ""
    stderr: str = ""
    surface: dict = field(default_factory=dict)


class WindowsDesktop:
    def enumerate(self) -> List[WinWindow]:
        results: List[WinWindow] = []

        @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
        def callback(hwnd, _):
            length = user32.GetWindowTextLengthW(hwnd)
            title = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, title, length + 1)
            cls = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls, 256)
            pid = wt.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            rect = wt.RECT()
            visible = bool(user32.IsWindowVisible(hwnd))
            if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                bbox = (rect.left, rect.top, rect.right, rect.bottom)
            else:
                bbox = (0, 0, 0, 0)
            results.append(WinWindow(hwnd=hwnd, title=title.value or "", cls=cls.value or "", pid=pid.value, rect=bbox, visible=visible))
            return True

        user32.EnumWindows(callback, 0)
        return results

    def focus(self, title: str) -> DesktopControlResult:
        wins = [w for w in self.enumerate() if title.lower() in w.title.lower()]
        if not wins:
            return DesktopControlResult(ok=False, stderr="window not found", surface={"kind": "windows_desktop", "action": "focus"})
        win = wins[0]
        user32.ShowWindow(win.hwnd, 9)
        user32.SetForegroundWindow(win.hwnd)
        return DesktopControlResult(ok=True, stdout=win.title, surface={"kind": "windows_desktop", "action": "focus", "title": win.title, "hwnd": win.hwnd})

    def minimize_all(self) -> DesktopControlResult:
        user32.keybd_event(wt.WORD(VK_LWIN), wt.WORD(0), wt.DWORD(0), wt.DWORD(0))
        user32.keybd_event(wt.WORD(VK_LWIN), wt.WORD(0), wt.DWORD(KEYEVENTF_KEYUP), wt.DWORD(0))
        return DesktopControlResult(ok=True, stdout="minimize_all", surface={"kind": "windows_desktop", "action": "minimize_all"})

    def send_hotkey(self, keys: List[str]) -> DesktopControlResult:
        for key in keys:
            user32.keybd_event(wt.WORD(self._vk(key)), wt.WORD(0), wt.DWORD(0), wt.DWORD(0))
        for key in reversed(keys):
            user32.keybd_event(wt.WORD(self._vk(key)), wt.WORD(0), wt.DWORD(KEYEVENTF_KEYUP), wt.DWORD(0))
        return DesktopControlResult(ok=True, stdout="+".join(keys), surface={"kind": "windows_desktop", "action": "hotkey", "keys": keys})

    def type_text(self, text: str) -> DesktopControlResult:
        for ch in text:
            if ch == "\n":
                self.send_hotkey(["enter"])
                continue
            if ch == "\t":
                self.send_hotkey(["tab"])
                continue
            inp = _INPUT(
                type=wt.DWORD(INPUT_KEYBOARD),
                union=_INPUT_UNION(
                    ki=_KEYBDINPUT(
                        wVk=wt.WORD(0),
                        wScan=wt.WORD(ord(ch)),
                        dwFlags=wt.DWORD(KEYEVENTF_UNICODE),
                        time=wt.DWORD(0),
                        dwExtraInfo=ctypes.c_ulonglong(0),
                    )
                ),
            )
            user32.SendInput(wt.DWORD(1), ctypes.byref(inp), ctypes.sizeof(_INPUT))
        return DesktopControlResult(ok=True, stdout=text, surface={"kind": "windows_desktop", "action": "type"})

    def launch(self, path: str, args: str = "") -> DesktopControlResult:
        if not Path(path).exists():
            return DesktopControlResult(ok=False, stderr="executable not found", surface={"kind": "windows_desktop", "action": "launch"})
        try:
            import os as _os
            _os.startfile(path) if not args else subprocess.Popen([path] + args.split())
            return DesktopControlResult(ok=True, stdout=path, surface={"kind": "windows_desktop", "action": "launch", "path": path})
        except Exception as exc:
            return DesktopControlResult(ok=False, stderr=str(exc), surface={"kind": "windows_desktop", "action": "launch"})

    @staticmethod
    def _vk(key: str) -> int:
        if len(key) == 1:
            return ctypes.windll.user32.VkKeyScanW(ord(key)) & 0xFF
        mapping = {
            "enter": 0x0D, "esc": 0x1B, "space": 0x20, "tab": 0x09,
            "ctrl": 0x11, "alt": 0x12, "shift": 0x10, "win": 0x5B,
            "left": 0x25, "up": 0x26, "right": 0x27, "down": 0x28,
        }
        return mapping.get(key.lower(), 0)

    def dispatch(self, cmd: str) -> DesktopControlResult:
        text = (cmd or "").strip()
        if not text.startswith("computer://"):
            return DesktopControlResult(ok=False, stderr="missing computer:// cmd")
        body = text[len("computer://"):]
        if body.startswith("app "):
            app = body[4:].strip().lower()
            return self._launch_system_app(app)
        if body.startswith("type "):
            return self.type_text(body[5:])
        if body.startswith("hotkey "):
            return self.send_hotkey(body[7:].split("+"))
        if body == "minimize_all":
            return self.minimize_all()
        if body == "enumerate":
            self.enumerate()
            return DesktopControlResult(ok=True, stdout="enumerated", surface={"kind": "windows_desktop", "action": "enumerate"})
        return DesktopControlResult(ok=False, stderr=f"unknown computer:// command: {body}")

    def _launch_system_app(self, app: str) -> DesktopControlResult:
        shell = r"C:\WINDOWS\system32\shell32.dll"
        start_menu = r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs"
        launchers = {
            "notepad": r"C:\WINDOWS\system32\notepad.exe",
            "calc": r"C:\WINDOWS\system32\calc.exe",
            "mspaint": r"C:\WINDOWS\system32\mspaint.exe",
            "write": shell,
            "paint": shell,
            "explorer": shell,
            "terminal": self._start_menu_exe(start_menu, [
                "Accessories", "Windows Terminal.lnk"
            ]) or r"C:\WINDOWS\system32\wt.exe",
        }
        if app in launchers:
            path = launchers[app]
            if path == shell and app in {"write", "paint", "explorer"}:
                ctypes.windll.shell32.ShellExecuteW(None, "open", "shell:AppsFolder\\Microsoft.WindowsCalculator_8wekyb3d8bbwe!App", None, None, 1) if app == "calc" else None
                if app == "calc":
                    return DesktopControlResult(ok=True, stdout="shell:AppsFolder calculator", surface={"kind": "windows_desktop", "action": "app", "app": app})
                ctypes.windll.shell32.ShellExecuteW(None, "open", app, None, None, 1)
                return DesktopControlResult(ok=True, stdout=app, surface={"kind": "windows_desktop", "action": "app", "app": app})
            return self.launch(path)
        return self.launch(self._start_menu_exe(start_menu, app.split("\\")) or shell)

    @staticmethod
    def _start_menu_exe(root: str, parts: list[str]) -> str:
        current = Path(root)
        for part in parts:
            current = current / part
            if not current.exists():
                return ""
        return str(current)
