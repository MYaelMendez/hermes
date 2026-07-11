from __future__ import annotations

import os
import shutil
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Callable, Dict, List, Optional


_HAS_PSUTIL = True
try:  # pragma: no cover - optional dependency
    import psutil  # type: ignore
except Exception:  # pragma: no cover
    psutil = None  # type: ignore[assignment]
    _HAS_PSUTIL = False


class TaskKind(Enum):
    MACHINE = "machine"
    VLC = "vlc"
    MESH = "mesh"
    CONDUCTOR = "conductor"
    SUBAGENT = "subagent"
    IPC = "ipc"
    IDLE = "idle"


@dataclass
class Task:
    id: str
    kind: TaskKind = field(default_factory=lambda: TaskKind.IDLE)
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    max_retries: int = 0
    retries: int = 0
    created_at: float = field(default_factory=time.time)
    correlation_id: str = ""


@dataclass
class MachineVitals:
    cpu_percent: float = 0.0
    memory_total_bytes: int = 0
    memory_available_bytes: int = 0
    memory_percent: float = 0.0
    disks: List[Dict[str, Any]] = field(default_factory=list)
    writer_procs: List[str] = field(default_factory=list)
    source: str = "unknown"
    collected_at: str = ""

    @staticmethod
    def collect() -> "MachineVitals":
        cpu_percent = 0.0
        memory_total_bytes = 0
        memory_available_bytes = 0
        memory_percent = 0.0
        disks: List[Dict[str, Any]] = []
        writer_procs: List[str] = []
        source = "unknown"
        try:
            if _HAS_PSUTIL:
                cpu_percent = float(psutil.cpu_percent(interval=0.0))
                vm = psutil.virtual_memory()
                memory_total_bytes = int(vm.total)
                memory_available_bytes = int(vm.available)
                memory_percent = float(vm.percent)
                for part in psutil.disk_partitions(all=False):
                    try:
                        usage = psutil.disk_usage(part.mountpoint)
                        disks.append({
                            "mount": part.mountpoint,
                            "total_bytes": int(usage.total),
                            "used_bytes": int(usage.used),
                            "percent": float(usage.percent),
                        })
                    except Exception:
                        continue
                source = "psutil"
            else:
                raise RuntimeError("psutil unavailable")
        except Exception:
            cpu_line = _run([
                "powershell", "-NoProfile", "-Command",
                "(Get-Counter '\\Processor(_Total)\\% Processor Time').CounterSamples[0].CookedValue",
            ])
            mem_line = _run([
                "powershell", "-NoProfile", "-Command",
                "$os=Get-CimInstance Win32_OperatingSystem;'{0}:{1}' -f $os.TotalVisibleMemorySize,$os.FreePhysicalMemory",
            ])
            cpu_percent = _parse_float(cpu_line) or 0.0
            if ":" in mem_line:
                total_kb, free_kb = mem_line.split(":", 1)
                memory_total_bytes = int(float(total_kb) * 1024)
                memory_available_bytes = int(float(free_kb) * 1024)
                if memory_total_bytes > 0:
                    memory_percent = ((memory_total_bytes - memory_available_bytes) / memory_total_bytes) * 100.0
            try:
                out = subprocess.check_output(
                    ["powershell", "-NoProfile", "-Command", "Get-PSDrive -PSProvider FileSystem | Select-Object Name,Used,Free | ConvertTo-Json"],
                    stderr=subprocess.DEVNULL,
                    text=True,
                )
                data = _powershell_json(out)
                if isinstance(data, list):
                    for item in data:
                        if not isinstance(item, dict) or item.get("Name") in {"Temp", "Registry"}:
                            continue
                        used = _to_bytes(item.get("Used") or 0)
                        free = _to_bytes(item.get("Free") or 0)
                        disks.append({
                            "mount": item.get("Name", "?"),
                            "used_bytes": used,
                            "free_bytes": free,
                            "total_bytes": used + free,
                            "percent": ((used / (used + free)) * 100.0) if (used + free) > 0 else 0.0,
                        })
            except Exception:
                pass
            source = "powershell"

        writer_procs = _active_writer_procs()
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return MachineVitals(
            cpu_percent=cpu_percent,
            memory_total_bytes=memory_total_bytes,
            memory_available_bytes=memory_available_bytes,
            memory_percent=memory_percent,
            disks=disks,
            writer_procs=writer_procs,
            source=source,
            collected_at=now,
        )


@dataclass
class SurfaceSummary:
    address: str = ""
    kind: str = ""
    runtime: str = "hermes-code"
    ok: bool = False
    rc: int = 1
    pid: Optional[int] = None
    status: str = "idle"


def _run(cmd: list[str]) -> str:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True)
        return out.strip()
    except Exception:
        return ""


def _parse_float(value: str) -> float | None:
    try:
        return float(value.strip().splitlines()[0].replace(",", "."))
    except Exception:
        return None


def _powershell_json(raw: str):
    try:
        return __import__("json").loads(raw)
    except Exception:
        return None


def _to_bytes(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _active_writer_procs() -> List[str]:
    names = []
    try:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", "Get-Process | Select-Object Id,Name,Path | ConvertTo-Json"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        data = _powershell_json(out) or []
        if isinstance(data, dict):
            data = [data]
        for item in data:
            if not isinstance(item, dict):
                continue
            path = item.get("Path") or item.get("Name") or ""
            lower = path.lower()
            if any(needle in lower for needle in ["vlc", "ffmpeg", "ffplay", "wireshark", "audacity", "obs"]):
                names.append(path)
    except Exception:
        pass
    return names[:24]


class VictusSuperagent:
    MAX_CONCURRENT_TASKS = 8
    TASK_TIMEOUT_SECONDS = 60.0
    STOP_EVENT_WAIT_SECONDS = 1.0
    MESH_NAMESPACE_GLOBAL = "global"
    MESH_NAMESPACE_LOCAL = "local"

    def __init__(
        self,
        machine_limit_threshold: float = 90.0,
        runtime_state_dir: Optional[Path] = None,
    ) -> None:
        self._task_counter = 0
        self._workers: List[threading.Thread] = []
        self._queue: Queue[Task] = Queue()
        self._history: List[Dict[str, Any]] = []
        self._history_lock = threading.Lock()
        self._history_limit = 256
        self._stop = threading.Event()
        self._process_task: Callable[[Task, MachineVitals], Dict[str, Any]] = self._default_process_task
        self._machine_limit_threshold = float(machine_limit_threshold)
        self._runtime_state_dir = runtime_state_dir or _default_runtime_dir()
        try:
            self._runtime_state_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    @staticmethod
    def _schema_version() -> str:
        return "victus-superagent-v1"

    def start(self) -> None:
        for _ in range(self.MAX_CONCURRENT_TASKS):
            thread = threading.Thread(target=self._worker_loop, daemon=True)
            thread.start()
            self._workers.append(thread)

    def stop(self, wait: bool = True) -> None:
        self._stop.set()
        if wait:
            for thread in self._workers:
                thread.join(timeout=self.TASK_TIMEOUT_SECONDS)

    def submit(self, task: Task) -> Dict[str, Any]:
        if not task.id:
            task.id = self._next_task_id()
        enqueue = {
            "queued_at": time.time(),
            "accepted": True,
        }
        if self._is_machine_over_limit():
            enqueue["deferred"] = True
            enqueue["reason"] = "machine over limit"
            return enqueue
        self._queue.put_nowait(task)
        return enqueue

    def history(self, limit: int = 64) -> List[Dict[str, Any]]:
        with self._history_lock:
            items = list(self._history[-limit:])
        return items

    def gauntlet(self) -> Dict[str, Any]:
        vitals = MachineVitals.collect()
        surface = self._current_surface(vitals)
        machine_token = self._machine_token(vitals)
        mesh_token = self._mesh_token(vitals)
        fleet_token = self._fleet_token(vitals)
        return {
            "ok": True,
            "rc": 0,
            "stdout": f"{machine_token}\n{mesh_token}\n{fleet_token}\n",
            "stderr": "",
            "surface": surface,
            "machine": {
                "cpu_percent": vitals.cpu_percent,
                "memory_percent": vitals.memory_percent,
                "memory_total_bytes": vitals.memory_total_bytes,
                "memory_available_bytes": vitals.memory_available_bytes,
                "disks": vitals.disks,
                "writer_procs": vitals.writer_procs,
                "collected_at": vitals.collected_at,
                "source": vitals.source,
            },
            "mesh": {
                "glocal": {
                    "local": "pc://mesh/victus/local",
                    "global": "pc://mesh/global",
                },
                "namespaces": self._mesh_namespaces(),
            },
            "fleet": {
                "surface": "vlc://fleet",
                "max_concurrent": self.MAX_CONCURRENT_TASKS,
            },
            "schema_version": self._schema_version(),
        }

    def run_forever(self) -> None:
        self.start()
        try:
            while not self._stop.is_set():
                time.sleep(self.STOP_EVENT_WAIT_SECONDS)
        finally:
            self.stop(wait=False)

    def _worker_loop(self) -> None:
        while not self._stop.is_set():
            try:
                task = self._queue.get(timeout=self.STOP_EVENT_WAIT_SECONDS)
            except Empty:
                continue
            start = time.time()
            vitals = MachineVitals.collect()
            try:
                result = self._process_task(task, vitals)
            except Exception as exc:
                result = {
                    "ok": False,
                    "rc": 1,
                    "stdout": "",
                    "stderr": f"{exc.__class__.__name__}: {exc}",
                }
            record = {
                "task_id": task.id,
                "kind": task.kind.value,
                "priority": task.priority,
                "duration_ms": int((time.time() - start) * 1000),
                "result": result,
                "machine": {
                    "cpu_percent": vitals.cpu_percent,
                    "memory_percent": vitals.memory_percent,
                    "writer_procs": vitals.writer_procs,
                },
                "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            with self._history_lock:
                self._history.append(record)
                if len(self._history) > self._history_limit:
                    self._history = self._history[-self._history_limit:]
            self._queue.task_done()

    def _default_process_task(self, task: Task, vitals: MachineVitals) -> Dict[str, Any]:
        if task.kind == TaskKind.MACHINE:
            return {
                "ok": True,
                "rc": 0,
                "stdout": "machine",
                "stderr": "",
                "machine": {
                    "cpu_percent": vitals.cpu_percent,
                    "memory_percent": vitals.memory_percent,
                    "disks": vitals.disks,
                },
            }
        if task.kind == TaskKind.VLC:
            return self._dispatch_vlc(task.payload)
        if task.kind == TaskKind.MESH:
            return self._dispatch_mesh(task.payload)
        if task.kind == TaskKind.CONDUCTOR:
            return self._dispatch_conductor(task.payload)
        return {
            "ok": False,
            "rc": 2,
            "stdout": "",
            "stderr": f"unknown task kind: {task.kind.value}",
        }

    def _dispatch_vlc(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from apps.reachy.vlc_wrapper import vlc_fleet
            command = str(payload.get("command") or "status").strip()
            raw = f"vlc://{command}"
            if "target" in payload:
                raw = f"{raw} {payload['target']}"
            return vlc_fleet.dispatch(raw)
        except Exception as exc:
            return {"ok": False, "rc": 3, "stdout": "", "stderr": f"vlc unavailable: {exc}"}

    def _dispatch_mesh(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from apps.reachy.pc_mesh import PCMesh
            mesh = PCMesh(default_user=str(payload.get("user") or self.MESH_NAMESPACE_LOCAL))
            action = str(payload.get("action") or "list")
            if action.startswith("global"):
                node_id = str(payload.get("id") or "")
                return mesh.dispatch_global(node_id) if node_id else {"ok": False, "rc": 2, "stdout": "", "stderr": "missing id"}
            if action.startswith("user"):
                namespace = mesh.namespace()
                node_id = str(payload.get("id") or "")
                if action == "user.list":
                    return {"ok": True, "rc": 0, "stdout": "", "stderr": "", "nodes": namespace.list_nodes()}
                return namespace.dispatch(node_id) if node_id else {"ok": False, "rc": 2, "stdout": "", "stderr": "missing id"}
            return {"ok": True, "rc": 0, "stdout": "", "stderr": "", "namespaces": mesh.namespaces()}
        except Exception as exc:
            return {"ok": False, "rc": 4, "stdout": "", "stderr": f"mesh unavailable: {exc}"}

    def _dispatch_conductor(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from hermes_cli.conductor import _dispatch
            command = str(payload.get("command") or "hermes-superagent://status").strip()
            return _dispatch(command)
        except Exception as exc:
            return {"ok": False, "rc": 5, "stdout": "", "stderr": f"conductor unavailable: {exc}"}

    def _is_machine_over_limit(self) -> bool:
        try:
            vitals = MachineVitals.collect()
            return (
                vitals.cpu_percent >= self._machine_limit_threshold
                or vitals.memory_percent >= self._machine_limit_threshold
                or bool(vitals.writer_procs)
            )
        except Exception:
            return False

    def _next_task_id(self) -> str:
        self._task_counter += 1
        return f"task-{self._task_counter:06d}-{uuid.uuid4().hex[:6]}"

    def _current_surface(self, vitals: MachineVitals) -> Dict[str, Any]:
        return {
            "kind": "victus_superagent",
            "address": "pc://mesh/victus/local/victus-superagent",
            "runtime": "hermes-code",
            "machine": {
                "cpu_percent": vitals.cpu_percent,
                "memory_percent": vitals.memory_percent,
                "writer_procs": vitals.writer_procs,
            },
            "mesh": {
                "local": "pc://mesh/victus/local",
                "global": "pc://mesh/global",
            },
            "conductor": "hermes-superagent://status",
            "fleet": "vlc://fleet",
        }

    def _machine_token(self, vitals: MachineVitals) -> str:
        load = "high" if (
            vitals.cpu_percent >= self._machine_limit_threshold
            or vitals.memory_percent >= self._machine_limit_threshold
            or bool(vitals.writer_procs)
        ) else "nominal"
        return f"mech:victus:machine:load={load}:cpu={vitals.cpu_percent:.1f}:mem={vitals.memory_percent:.1f}"

    def _mesh_token(self, vitals: MachineVitals) -> str:
        return f"mech:victus:mesh:local=pc://mesh/victus/local:global=pc://mesh/global"

    def _fleet_token(self, vitals: MachineVitals) -> str:
        return f"mech:victus:fleet:surface=vlc://fleet:max_concurrent={self.MAX_CONCURRENT_TASKS}"

    def _mesh_namespaces(self) -> List[str]:
        try:
            from apps.reachy.pc_mesh import MESH
            return MESH.namespaces()
        except Exception:
            return [self.MESH_NAMESPACE_LOCAL]


def _default_runtime_dir() -> Path:
    local = os.getenv("LOCALAPPDATA", "").strip()
    if local:
        return Path(local) / "hermes" / "victus-superagent"
    return Path.home() / "AppData" / "Local" / "hermes" / "victus-superagent"
