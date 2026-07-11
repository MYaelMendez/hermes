#!/usr/bin/env python3
"""Collect local computer vitals and produce actionable alerts."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _run(cmd: list[str]) -> str:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True)
        return out.strip()
    except Exception:
        return ""


def _parse_float(value: str) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def _collect_cpu_memory() -> dict[str, Any]:
    # Prefer psutil when available for stable cross-platform telemetry.
    try:
        import psutil  # type: ignore

        cpu_percent = float(psutil.cpu_percent(interval=0.5))
        vm = psutil.virtual_memory()
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": float(vm.percent),
            "memory_available_bytes": int(vm.available),
            "memory_total_bytes": int(vm.total),
            "source": "psutil",
        }
    except Exception:
        pass

    # Fallback on Windows using PowerShell counters.
    cpu_line = _run([
        "powershell",
        "-NoProfile",
        "-Command",
        "(Get-Counter '\\Processor(_Total)\\% Processor Time').CounterSamples[0].CookedValue",
    ])
    mem_line = _run([
        "powershell",
        "-NoProfile",
        "-Command",
        "$os=Get-CimInstance Win32_OperatingSystem;"
        "$used=($os.TotalVisibleMemorySize-$os.FreePhysicalMemory);"
        "$pct=($used/$os.TotalVisibleMemorySize)*100;"
        "Write-Output $pct;"
        "Write-Output $os.FreePhysicalMemory;"
        "Write-Output $os.TotalVisibleMemorySize",
    ])

    memory_percent = None
    memory_available_bytes = None
    memory_total_bytes = None

    parts = [p for p in mem_line.splitlines() if p.strip()]
    if len(parts) >= 3:
        memory_percent = _parse_float(parts[0])
        free_kib = _parse_float(parts[1])
        total_kib = _parse_float(parts[2])
        if free_kib is not None:
            memory_available_bytes = int(free_kib * 1024)
        if total_kib is not None:
            memory_total_bytes = int(total_kib * 1024)

    return {
        "cpu_percent": _parse_float(cpu_line),
        "memory_percent": memory_percent,
        "memory_available_bytes": memory_available_bytes,
        "memory_total_bytes": memory_total_bytes,
        "source": "powershell-fallback",
    }


def _collect_disk(path: Path) -> dict[str, Any]:
    usage = shutil.disk_usage(path)
    used = usage.total - usage.free
    used_percent = (used / usage.total) * 100 if usage.total else 0.0
    free_percent = 100.0 - used_percent
    return {
        "path": str(path),
        "total_bytes": int(usage.total),
        "used_bytes": int(used),
        "free_bytes": int(usage.free),
        "used_percent": float(round(used_percent, 2)),
        "free_percent": float(round(free_percent, 2)),
    }


def _collect_gpu() -> dict[str, Any] | None:
    query = "utilization.gpu,temperature.gpu,memory.used,memory.total,power.draw,name"
    out = _run([
        "nvidia-smi",
        f"--query-gpu={query}",
        "--format=csv,noheader,nounits",
    ])
    if not out:
        return None

    first = out.splitlines()[0]
    parts = [p.strip() for p in first.split(",")]
    if len(parts) < 6:
        return None

    gpu_util = _parse_float(parts[0])
    temp = _parse_float(parts[1])
    mem_used = _parse_float(parts[2])
    mem_total = _parse_float(parts[3])
    power = _parse_float(parts[4])
    name = parts[5]

    mem_percent = None
    if mem_used is not None and mem_total:
        mem_percent = (mem_used / mem_total) * 100

    return {
        "name": name,
        "utilization_percent": gpu_util,
        "temperature_c": temp,
        "memory_used_mib": mem_used,
        "memory_total_mib": mem_total,
        "memory_percent": (round(mem_percent, 2) if mem_percent is not None else None),
        "power_w": power,
    }


def _alert(level: str, metric: str, value: float | None, threshold: float, condition: str, action: str) -> dict[str, Any]:
    return {
        "level": level,
        "metric": metric,
        "value": value,
        "threshold": threshold,
        "condition": condition,
        "action": action,
    }


def _evaluate(vitals: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []

    cpu = vitals.get("cpu", {}).get("cpu_percent")
    if cpu is not None and cpu >= args.cpu_critical:
        alerts.append(_alert("critical", "cpu_percent", cpu, args.cpu_critical, ">=", "Close heavy apps; inspect top CPU processes."))
    elif cpu is not None and cpu >= args.cpu_warn:
        alerts.append(_alert("warn", "cpu_percent", cpu, args.cpu_warn, ">=", "Reduce concurrent workloads or stagger jobs."))

    mem = vitals.get("cpu", {}).get("memory_percent")
    if mem is not None and mem >= args.memory_critical:
        alerts.append(_alert("critical", "memory_percent", mem, args.memory_critical, ">=", "Restart memory-heavy apps; increase pagefile if persistent."))
    elif mem is not None and mem >= args.memory_warn:
        alerts.append(_alert("warn", "memory_percent", mem, args.memory_warn, ">=", "Free RAM and postpone non-essential tasks."))

    disk_free = vitals.get("disk", {}).get("free_percent")
    if disk_free is not None and disk_free <= args.disk_free_critical:
        alerts.append(_alert("critical", "disk_free_percent", disk_free, args.disk_free_critical, "<=", "Free disk immediately or move artifacts off-drive."))
    elif disk_free is not None and disk_free <= args.disk_free_warn:
        alerts.append(_alert("warn", "disk_free_percent", disk_free, args.disk_free_warn, "<=", "Clean caches/logs and archive old outputs."))

    gpu = vitals.get("gpu") or {}
    gpu_temp = gpu.get("temperature_c")
    if gpu_temp is not None and gpu_temp >= args.gpu_temp_critical:
        alerts.append(_alert("critical", "gpu_temperature_c", gpu_temp, args.gpu_temp_critical, ">=", "Lower load, improve cooling, and check fan profile."))
    elif gpu_temp is not None and gpu_temp >= args.gpu_temp_warn:
        alerts.append(_alert("warn", "gpu_temperature_c", gpu_temp, args.gpu_temp_warn, ">=", "Monitor thermals and reduce sustained encode/training load."))

    return alerts


def _to_markdown(payload: dict[str, Any]) -> str:
    vitals = payload["vitals"]
    cpu = vitals.get("cpu", {})
    disk = vitals.get("disk", {})
    gpu = vitals.get("gpu") or {}

    lines = [
        "# Computer Vitals",
        "",
        f"Timestamp (UTC): {payload['timestamp_utc']}",
        "",
        "## Snapshot",
        f"- CPU: {cpu.get('cpu_percent')}%",
        f"- Memory: {cpu.get('memory_percent')}%",
        f"- Disk free: {disk.get('free_percent')}% ({disk.get('path')})",
    ]
    if gpu:
        lines.append(f"- GPU: {gpu.get('name')} | util={gpu.get('utilization_percent')}% | temp={gpu.get('temperature_c')}C")
    else:
        lines.append("- GPU: unavailable")

    lines.extend(["", "## Alerts"])
    if not payload["alerts"]:
        lines.append("- none")
    else:
        for alert in payload["alerts"]:
            lines.append(
                f"- {alert['level'].upper()} {alert['metric']}: value={alert['value']} {alert['condition']} {alert['threshold']} | action: {alert['action']}"
            )

    return "\n".join(lines) + "\n"


def _default_output() -> Path:
    hermes_home = Path((Path.home() / ".hermes")).resolve()
    root = Path(__import__("os").getenv("HERMES_HOME", str(hermes_home)))
    return root / "monitor" / "latest-vitals.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect computer vitals and emit actionable alerts")
    parser.add_argument("--path", default=str(Path.cwd().anchor or Path.cwd()), help="Disk path to monitor (default: current drive root)")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format")
    parser.add_argument("--output", help="Optional output file path")
    parser.add_argument("--history", action="store_true", help="Append payload to ~/.hermes/monitor/vitals-history.jsonl")

    parser.add_argument("--cpu-warn", type=float, default=80.0)
    parser.add_argument("--cpu-critical", type=float, default=92.0)
    parser.add_argument("--memory-warn", type=float, default=80.0)
    parser.add_argument("--memory-critical", type=float, default=92.0)
    parser.add_argument("--disk-free-warn", type=float, default=15.0)
    parser.add_argument("--disk-free-critical", type=float, default=8.0)
    parser.add_argument("--gpu-temp-warn", type=float, default=80.0)
    parser.add_argument("--gpu-temp-critical", type=float, default=87.0)

    parser.add_argument("--fail-on-critical", action="store_true", help="Exit 2 if any critical alert exists")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    disk_path = Path(args.path).expanduser().resolve()

    cpu_mem = _collect_cpu_memory()
    disk = _collect_disk(disk_path)
    gpu = _collect_gpu()

    vitals = {"cpu": cpu_mem, "disk": disk, "gpu": gpu}
    payload = {
        "schema_version": 1,
        "timestamp_utc": _now_utc(),
        "vitals": vitals,
        "alerts": _evaluate(vitals, args),
    }

    output_path = Path(args.output).expanduser().resolve() if args.output else _default_output()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.format == "markdown":
        rendered = _to_markdown(payload)
        output_path.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
    else:
        rendered = json.dumps(payload, indent=2, ensure_ascii=False)
        output_path.write_text(rendered + "\n", encoding="utf-8")
        print(rendered)

    if args.history:
        history_path = output_path.parent / "vitals-history.jsonl"
        with history_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    if args.fail_on_critical and any(a.get("level") == "critical" for a in payload["alerts"]):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
