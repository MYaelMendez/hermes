from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from hermes_runtime.victus_superagent import MachineVitals, Task, TaskKind, VictusSuperagent


def test_machine_vitals_collects_without_psutil(monkeypatch):
    def _fake_run(cmd):
        if cmd[0] == "powershell":
            ps_cmd = " ".join(cmd)
            if "Processor(_Total)" in ps_cmd:
                return "42"
            if "Win32_OperatingSystem" in ps_cmd:
                return "4096000:2048000"
            if "Get-PSDrive" in ps_cmd:
                return "[]"
        return ""

    monkeypatch.setattr("hermes_runtime.victus_superagent._run", _fake_run)
    monkeypatch.setattr("hermes_runtime.victus_superagent._HAS_PSUTIL", False)
    vitals = MachineVitals.collect()
    assert 0 <= vitals.cpu_percent <= 100
    assert vitals.memory_total_bytes > 0
    assert isinstance(vitals.disks, list)


def test_victus_superagent_gauntlet_returns_surface():
    agent = VictusSuperagent()
    response = agent.gauntlet()
    assert response["ok"] is True
    assert response["surface"]["kind"] == "victus_superagent"
    assert response["surface"]["runtime"] == "hermes-code"
    assert "machine" in response["surface"]
    assert "mesh" in response["surface"]
    assert "fleet" in response["surface"]


def test_submit_processes_task(monkeypatch):
    agent = VictusSuperagent()
    processed = []

    def fake_process(task: Task, vitals: MachineVitals) -> dict[str, object]:
        processed.append({"id": task.id, "kind": task.kind.value})
        return {"ok": True, "rc": 0, "stdout": task.id, "stderr": ""}

    def fake_over_limit() -> bool:
        return False

    monkeypatch.setattr(agent, "_process_task", fake_process)
    monkeypatch.setattr(agent, "_is_machine_over_limit", fake_over_limit)
    agent.start()
    try:
        result = agent.submit(Task(id="task-1", kind=TaskKind.MACHINE, payload={}))
        assert result.get("accepted") is True
        deadline = time.time() + 2
        while not processed and time.time() < deadline:
            time.sleep(0.05)
        assert processed and processed[0]["id"] == "task-1"
    finally:
        agent.stop(wait=False)
