from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from apps.reachy.vlc_runtime import detect, ensure_dirs


@dataclass
class VLCNode:
    """Canonical fleet node record."""
    name: str
    address: str = ""
    pid: int | None = None
    target: str = ""
    role: str = "local"
    runtime: str = "hermes-code"
    status_text: str = "idle"
    last_seen: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "address": self.address,
            "pid": self.pid,
            "target": self.target,
            "role": self.role,
            "runtime": self.runtime,
            "status": self.status_text,
            "last_seen": self.last_seen,
            "ok": bool(self.pid and Path(self.target).exists() if self.target else self.pid is not None),
        }


class VLCController:
    process = None
    _pid = None
    _last_target = None
    _target: str = r"C:\Users\yaelm\Videos\hermes_demo.mp4"

    @classmethod
    def _alive(cls) -> bool:
        if cls.process is not None:
            try:
                if cls.process.pid and cls.process.poll() is None:
                    return True
            except Exception:
                pass
        if cls._pid:
            try:
                out = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {cls._pid}", "/FO", "CSV"],
                    capture_output=True,
                    text=True,
                    shell=False,
                )
                if cls._pid in (out.stdout or ""):
                    return True
            except Exception:
                pass
        return False

    @classmethod
    def _send(cls, vk: int) -> None:
        try:
            import ctypes

            ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
            time.sleep(0.05)
            ctypes.windll.user32.keybd_event(vk, 0, 2, 0)
        except Exception:
            pass

    @classmethod
    def _launch(cls, target: str) -> None:
        if cls._alive():
            return
        candidates = [
            r"C:\Program Files\VideoLAN\VLC\vlc.exe",
            "vlc",
        ]
        argv = None
        for candidate in candidates:
            try:
                argv = [candidate]
                if target:
                    argv += [target]
                cls.process = subprocess.Popen(
                    argv,
                    shell=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                cls._pid = cls.process.pid
                return
            except Exception:
                argv = None
                cls.process = None
                cls._pid = None
        raise RuntimeError("vlc executable not found")

    @classmethod
    def play(cls, target: str | None = None) -> dict:
        target = target or cls._target
        cls._last_target = target
        if target and Path(target).exists():
            cls._launch(target)
        else:
            cls._launch(None)
        time.sleep(0.8)
        return cls.status()

    @classmethod
    def stop(cls) -> dict:
        cls._send(0x1B)
        return cls.status()

    @classmethod
    def fullscreen(cls) -> dict:
        cls._send(0x0D)
        return cls.status()

    @classmethod
    def status(cls) -> dict:
        running = cls._alive()
        target = cls._last_target or cls._target
        stdout = f"vlc://status pid={cls._pid or 'none'} target={target}\n"
        return {
            "ok": running or target is not None,
            "rc": 0,
            "stdout": stdout,
            "stderr": "",
            "running": running,
            "pid": cls._pid,
            "target": target,
            "runtime": "hermes-code",
        }


class VLCFleet:
    _nodes: dict[str, tuple[VLCController, VLCNode]]

    def __init__(self) -> None:
        runtime = detect()
        ensure_dirs(runtime)
        default_node = VLCNode(
            name="victus-local",
            address="pc://mesh/victus/local/vlc",
            role="local",
            runtime="hermes-code",
        )
        self._nodes = {
            "victus-local": (VLCController(), default_node),
        }

    @staticmethod
    def _mech_token(kind: str, node: str) -> str:
        return f"mech:vlc:{kind}:node={node}:runtime=hermes-code"

    def _fleet_status(self) -> dict:
        members = []
        for name, (controller, node) in self._nodes.items():
            controller_status = controller.status()
            node.pid = controller_status.get("pid")
            node.target = controller_status.get("target", node.target)
            node.status_text = "running" if controller_status.get("running") else "idle"
            node.last_seen = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            members.append(node.to_dict())
        return {
            "ok": True,
            "rc": 0,
            "stdout": "vlc://fleet status members={}\n".format(len(members)),
            "stderr": "",
            "surface": {
                "kind": "vlc_fleet",
                "address": "vlc://fleet",
                "runtime": "hermes-code",
                "members": members,
                "glocal": {
                    "local": "pc://mesh/victus/local/vlc",
                    "global": "pc://mesh/global/vlc",
                },
            },
            "token": self._mech_token("status", "fleet"),
        }

    def _fleet_play(self, target: str) -> dict:
        controller, node = self._nodes["victus-local"]
        result = controller.play(target)
        node.pid = result.get("pid")
        node.target = result.get("target", node.target)
        node.status_text = "running" if result.get("running") else "idle"
        node.last_seen = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return {
            "ok": result.get("ok", False),
            "rc": result.get("rc", 0),
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "surface": {
                "kind": "vlc_fleet",
                "address": f"vlc://fleet/play/{node.name}",
                "runtime": "hermes-code",
                "node": node.to_dict(),
                "glocal": {
                    "local": "pc://mesh/victus/local/vlc",
                    "global": "pc://mesh/global/vlc",
                },
            },
            "token": self._mech_token("play", node.name),
        }

    def _fleet_command(self, command: str, args: str) -> dict:
        if command == "status":
            return self._fleet_status()
        if command == "play":
            target = args or self._nodes["victus-local"][1].target
            return self._fleet_play(target)
        if command == "stop":
            controller, node = self._nodes["victus-local"]
            result = controller.stop()
            node.status_text = "idle"
            node.last_seen = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            return {
                "ok": result.get("ok", False),
                "rc": result.get("rc", 0),
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "surface": {
                    "kind": "vlc_fleet",
                    "address": "vlc://fleet/stop",
                    "runtime": "hermes-code",
                    "node": node.to_dict(),
                    "glocal": {
                        "local": "pc://mesh/victus/local/vlc",
                        "global": "pc://mesh/global/vlc",
                    },
                },
                "token": self._mech_token("stop", node.name),
            }
        if command == "fullscreen":
            controller, node = self._nodes["victus-local"]
            result = controller.fullscreen()
            node.last_seen = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            return {
                "ok": result.get("ok", False),
                "rc": result.get("rc", 0),
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "surface": {
                    "kind": "vlc_fleet",
                    "address": "vlc://fleet/fullscreen",
                    "runtime": "hermes-code",
                    "node": node.to_dict(),
                    "glocal": {
                        "local": "pc://mesh/victus/local/vlc",
                        "global": "pc://mesh/global/vlc",
                    },
                },
                "token": self._mech_token("fullscreen", node.name),
            }
        if command == "runtime":
            node = self._nodes["victus-local"][1]
            node.status_text = "agentic-runtime"
            node.last_seen = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            return {
                "ok": True,
                "rc": 0,
                "stdout": "vlc://runtime agentic=vlc+superagent version=0.1\n",
                "stderr": "",
                "surface": {
                    "kind": "vlc_fleet",
                    "address": "vlc://runtime",
                    "runtime": "hermes-code",
                    "node": node.to_dict(),
                    "glocal": {
                        "local": "pc://mesh/victus/local/vlc",
                        "global": "pc://mesh/global/vlc",
                    },
                },
                "token": self._mech_token("runtime", node.name),
            }
        return {
            "ok": False,
            "rc": 2,
            "stdout": "",
            "stderr": f"unknown fleet command: {command}",
            "surface": {
                "kind": "vlc_fleet",
                "address": "vlc://fleet",
                "runtime": "hermes-code",
            },
            "token": self._mech_token("error", "fleet"),
        }

    def dispatch(self, raw: str) -> dict:
        action = raw.split("vlc://", 1)[1].strip() if "vlc://" in raw else ""
        command = action.split()[0] if action.split() else "status"
        args = action.split(" ", 1)[1].strip() if " " in action else ""

        if command == "fleet":
            sub = args.split()[0] if args.split() else "status"
            return self._fleet_command(sub, args.split(" ", 1)[1].strip() if " " in args else "")

        if command in {"play", "stop", "status", "fullscreen", "runtime"}:
            target_node = "victus-local"
            node_entry = self._nodes[target_node]
            ctl = node_entry.controller
            if command == "play":
                result = ctl.play(args or None)
            elif command == "stop":
                result = ctl.stop()
            elif command == "fullscreen":
                result = ctl.fullscreen()
            elif command == "runtime":
                node_entry.node.status_text = "agentic-runtime"
                node_entry.node.last_seen = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                return {
                    "ok": True,
                    "rc": 0,
                    "stdout": "vlc://runtime agentic=vlc+superagent version=0.1\n",
                    "stderr": "",
                    "surface": {
                        "kind": "vlc_node",
                        "address": "vlc://runtime",
                        "runtime": "hermes-code",
                        "node": node_entry.node.to_dict(),
                    },
                    "token": self._mech_token("runtime", target_node),
                }
            else:
                result = ctl.status()

            result.setdefault("stdout", result.get("stdout", ""))
            result.setdefault("stderr", result.get("stderr", ""))
            result.setdefault("rc", result.get("rc", 0))
            node_entry.node.pid = result.get("pid")
            node_entry.node.target = result.get("target", node_entry.node.target)
            node_entry.node.status_text = "running" if result.get("running") else "idle"
            node_entry.node.last_seen = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            surface = result.setdefault("surface", {})
            surface.setdefault("kind", "vlc_node")
            surface.setdefault("address", raw)
            surface.setdefault("runtime", "hermes-code")
            surface.setdefault("node", node_entry.node.to_dict())
            return result

        return {
            "ok": False,
            "rc": 2,
            "stdout": "",
            "stderr": f"unknown vlc command: {command}",
            "surface": {
                "kind": "vlc_fleet",
                "address": raw,
                "runtime": "hermes-code",
            },
            "token": self._mech_token("error", "fleet"),
        }


vlc_fleet = VLCFleet()
