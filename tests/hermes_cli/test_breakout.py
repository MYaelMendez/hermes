"""Tests for breakout command wiring and Breakout 001 baseline behavior."""

import json
from argparse import Namespace
from pathlib import Path

from hermes_cli import main as main_mod


def _write_breakout_blueprint(project_root: Path) -> None:
    bp = project_root / "blueprints"
    bp.mkdir(parents=True, exist_ok=True)
    (bp / "breakout-001-250-baseline.md").write_text("breakout 001 baseline\n", encoding="utf-8")
    (bp / "breakout-002-vscode-codemode.md").write_text("breakout 002 codemode\n", encoding="utf-8")
    (bp / "plus-æ-glocal-omniverse-surface.md").write_text("+æ^glocal omniverse surface\n", encoding="utf-8")


def test_cmd_breakout_001_generates_verified_manifest(monkeypatch, tmp_path):
    project_root = tmp_path / "project"
    hermes_home = tmp_path / "home"
    project_root.mkdir(parents=True, exist_ok=True)
    hermes_home.mkdir(parents=True, exist_ok=True)
    _write_breakout_blueprint(project_root)

    monkeypatch.setattr(main_mod, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(main_mod, "get_hermes_home", lambda: hermes_home)

    args = Namespace(
        breakout_id="001",
        surface="vscode",
        units=250,
        input_file=None,
        output=None,
        verify_only=False,
        learn_sync=False,
    )

    main_mod.cmd_breakout(args)

    latest = hermes_home / "breakouts" / "breakout-001" / "breakout-001.latest.json"
    assert latest.exists()

    payload = json.loads(latest.read_text(encoding="utf-8"))
    assert payload["breakout_id"] == "001"
    assert payload["unit_count"] == 250
    assert len(payload["units"]) == 250


def test_cmd_breakout_001_rejects_non_baseline_unit_count(monkeypatch, tmp_path, capsys):
    project_root = tmp_path / "project"
    hermes_home = tmp_path / "home"
    project_root.mkdir(parents=True, exist_ok=True)
    hermes_home.mkdir(parents=True, exist_ok=True)
    _write_breakout_blueprint(project_root)

    monkeypatch.setattr(main_mod, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(main_mod, "get_hermes_home", lambda: hermes_home)

    args = Namespace(
        breakout_id="001",
        surface="vscode",
        units=249,
        input_file=None,
        output=None,
        verify_only=False,
        learn_sync=False,
    )

    main_mod.cmd_breakout(args)

    output = capsys.readouterr().out
    assert "exactly 250 units" in output
    latest = hermes_home / "breakouts" / "breakout-001" / "breakout-001.latest.json"
    assert not latest.exists()


def test_cmd_breakout_002_generates_verified_manifest(monkeypatch, tmp_path):
    project_root = tmp_path / "project"
    hermes_home = tmp_path / "home"
    project_root.mkdir(parents=True, exist_ok=True)
    hermes_home.mkdir(parents=True, exist_ok=True)
    _write_breakout_blueprint(project_root)

    monkeypatch.setattr(main_mod, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(main_mod, "get_hermes_home", lambda: hermes_home)

    args = Namespace(
        breakout_id="002",
        surface="vscode",
        units=250,
        input_file=None,
        output=None,
        verify_only=False,
        learn_sync=False,
    )

    main_mod.cmd_breakout(args)

    latest = hermes_home / "breakouts" / "breakout-002" / "breakout-002.latest.json"
    assert latest.exists()

    payload = json.loads(latest.read_text(encoding="utf-8"))
    assert payload["breakout_id"] == "002"
    assert payload["unit_count"] == 250
    assert len(payload["units"]) == 250
    assert payload["units"][0]["mode"] == "codemode"

    learn_sequence = hermes_home / "learn" / "learn-sequence.json"
    assert learn_sequence.exists()
    learn_payload = json.loads(learn_sequence.read_text(encoding="utf-8"))
    assert learn_payload["breakouts"]["002"]["mode"] == "codemode"
    assert learn_payload["breakouts"]["002"]["runtime_surface"] == "vscode"


def test_cmd_breakout_002_rejects_non_baseline_unit_count(monkeypatch, tmp_path, capsys):
    project_root = tmp_path / "project"
    hermes_home = tmp_path / "home"
    project_root.mkdir(parents=True, exist_ok=True)
    hermes_home.mkdir(parents=True, exist_ok=True)
    _write_breakout_blueprint(project_root)

    monkeypatch.setattr(main_mod, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(main_mod, "get_hermes_home", lambda: hermes_home)

    args = Namespace(
        breakout_id="002",
        surface="vscode",
        units=249,
        input_file=None,
        output=None,
        verify_only=False,
        learn_sync=False,
    )

    main_mod.cmd_breakout(args)

    output = capsys.readouterr().out
    assert "exactly 250 units" in output
    latest = hermes_home / "breakouts" / "breakout-002" / "breakout-002.latest.json"
    assert not latest.exists()


def test_cmd_breakout_001_syncs_learn_when_requested(monkeypatch, tmp_path):
    project_root = tmp_path / "project"
    hermes_home = tmp_path / "home"
    project_root.mkdir(parents=True, exist_ok=True)
    hermes_home.mkdir(parents=True, exist_ok=True)
    _write_breakout_blueprint(project_root)

    monkeypatch.setattr(main_mod, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(main_mod, "get_hermes_home", lambda: hermes_home)

    args = Namespace(
        breakout_id="001",
        surface="vscode",
        units=250,
        input_file=None,
        output=None,
        verify_only=False,
        learn_sync=True,
    )

    main_mod.cmd_breakout(args)

    learn_sequence = hermes_home / "learn" / "learn-sequence.json"
    assert learn_sequence.exists()
    learn_payload = json.loads(learn_sequence.read_text(encoding="utf-8"))
    assert learn_payload["breakouts"]["001"]["unit_count"] == 250


def test_cmd_breakout_002_omniverse_surface_syncs_glocal_local_only(monkeypatch, tmp_path):
    project_root = tmp_path / "project"
    hermes_home = tmp_path / "home"
    project_root.mkdir(parents=True, exist_ok=True)
    hermes_home.mkdir(parents=True, exist_ok=True)
    _write_breakout_blueprint(project_root)

    monkeypatch.setattr(main_mod, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(main_mod, "get_hermes_home", lambda: hermes_home)

    args = Namespace(
        breakout_id="002",
        surface="omniverse",
        units=250,
        input_file=None,
        output=None,
        verify_only=False,
        learn_sync=False,
    )

    main_mod.cmd_breakout(args)

    latest = hermes_home / "breakouts" / "breakout-002" / "breakout-002.latest.json"
    assert latest.exists()
    payload = json.loads(latest.read_text(encoding="utf-8"))
    assert payload["baseline"]["runtime_surface"] == "omniverse"
    assert payload["baseline"]["surface"] == "+æ^glocal"
    assert payload["baseline"]["cloud"] is False
    assert payload["baseline"]["formations"] == 250

    learn_sequence = hermes_home / "learn" / "learn-sequence.json"
    assert learn_sequence.exists()
    learn_payload = json.loads(learn_sequence.read_text(encoding="utf-8"))
    b002 = learn_payload["breakouts"]["002"]
    assert b002["runtime_surface"] == "omniverse"
    assert b002["mode"] == "deterministic"
    assert b002["surface"] == "+æ^glocal"
    assert b002["local_only"] is True
    assert b002["cloud"] is False


def test_cmd_breakout_002_omniverse_requests_vscode_media_launch(monkeypatch, tmp_path):
    project_root = tmp_path / "project"
    hermes_home = tmp_path / "home"
    project_root.mkdir(parents=True, exist_ok=True)
    hermes_home.mkdir(parents=True, exist_ok=True)
    _write_breakout_blueprint(project_root)

    monkeypatch.setattr(main_mod, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(main_mod, "get_hermes_home", lambda: hermes_home)

    calls: list[str] = []

    def _fake_launch():
        calls.append("launch")
        return True, "ok"

    monkeypatch.setattr(main_mod, "_launch_vscode_media_workflow", _fake_launch)

    args = Namespace(
        breakout_id="002",
        surface="omniverse",
        units=250,
        input_file=None,
        output=None,
        verify_only=False,
        learn_sync=False,
        vscode_media_launch=True,
    )

    main_mod.cmd_breakout(args)
    assert calls == ["launch"]


def test_cmd_breakout_002_omniverse_skips_vscode_media_launch_when_disabled(monkeypatch, tmp_path):
    project_root = tmp_path / "project"
    hermes_home = tmp_path / "home"
    project_root.mkdir(parents=True, exist_ok=True)
    hermes_home.mkdir(parents=True, exist_ok=True)
    _write_breakout_blueprint(project_root)

    monkeypatch.setattr(main_mod, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(main_mod, "get_hermes_home", lambda: hermes_home)

    calls: list[str] = []

    def _fake_launch():
        calls.append("launch")
        return True, "ok"

    monkeypatch.setattr(main_mod, "_launch_vscode_media_workflow", _fake_launch)

    args = Namespace(
        breakout_id="002",
        surface="omniverse",
        units=250,
        input_file=None,
        output=None,
        verify_only=False,
        learn_sync=False,
        vscode_media_launch=False,
    )

    main_mod.cmd_breakout(args)
    assert calls == []
