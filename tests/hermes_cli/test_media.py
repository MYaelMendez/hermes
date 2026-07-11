"""Tests for Hermes media command surface."""

import subprocess
from argparse import Namespace
import argparse
from pathlib import Path

import hermes_cli.media as media


def test_media_plan_and_audit_pass(monkeypatch, tmp_path):
    hermes_home = tmp_path / "home"
    input_file = tmp_path / "input.txt"
    input_file.write_text("hello media\n", encoding="utf-8")

    monkeypatch.setattr(media, "get_hermes_home", lambda: hermes_home)

    manifest = tmp_path / "manifest.json"
    plan_args = Namespace(
        media_action="plan",
        engine="ffmpeg",
        action="test-plan",
        input_path=str(input_file),
        output_path=str(tmp_path / "out.mp4"),
        member_token="+æ",
        governance="none",
        manifest=str(manifest),
    )

    try:
        media.media_command(plan_args)
    except SystemExit as exc:
        assert exc.code == 0

    assert manifest.exists()

    audit_args = Namespace(media_action="audit", manifest=str(manifest))
    try:
        media.media_command(audit_args)
    except SystemExit as exc:
        assert exc.code == 0


def test_media_audit_fails_on_bad_member_token(monkeypatch, tmp_path):
    hermes_home = tmp_path / "home"
    input_file = tmp_path / "input.txt"
    input_file.write_text("hello media\n", encoding="utf-8")

    monkeypatch.setattr(media, "get_hermes_home", lambda: hermes_home)

    manifest = tmp_path / "manifest.json"
    plan_args = Namespace(
        media_action="plan",
        engine="ffmpeg",
        action="test-plan",
        input_path=str(input_file),
        output_path=str(tmp_path / "out.mp4"),
        member_token="+æ",
        governance="none",
        manifest=str(manifest),
    )

    try:
        media.media_command(plan_args)
    except SystemExit as exc:
        assert exc.code == 0

    payload = media._read_manifest(manifest)
    payload["member_token"] = "public"
    media._write_manifest(manifest, payload)

    audit_args = Namespace(media_action="audit", manifest=str(manifest))
    try:
        media.media_command(audit_args)
    except SystemExit as exc:
        assert exc.code == 1


def test_media_viewport_runs(monkeypatch, tmp_path, capsys):
    hermes_home = tmp_path / "home"
    input_file = tmp_path / "input.txt"
    input_file.write_text("hello media\n", encoding="utf-8")

    monkeypatch.setattr(media, "get_hermes_home", lambda: hermes_home)

    manifest = tmp_path / "manifest.json"
    plan_args = Namespace(
        media_action="plan",
        engine="ffmpeg",
        action="viewport-seed",
        input_path=str(input_file),
        output_path=str(tmp_path / "out.mp4"),
        member_token="+æ",
        governance="none",
        manifest=str(manifest),
    )

    try:
        media.media_command(plan_args)
    except SystemExit as exc:
        assert exc.code == 0

    viewport_args = Namespace(media_action="viewport", limit=5)
    try:
        media.media_command(viewport_args)
    except SystemExit as exc:
        assert exc.code == 0

    output = capsys.readouterr().out
    assert "Media Desktop Agentic Entrepreneurship Viewport" in output
    assert "Surface:" in output


def test_media_plan_private_client_glocal_surface_audits(monkeypatch, tmp_path):
    hermes_home = tmp_path / "home"
    input_file = tmp_path / "input.mp4"
    input_file.write_bytes(b"hello media bytes")

    monkeypatch.setattr(media, "get_hermes_home", lambda: hermes_home)

    manifest = tmp_path / "manifest-private-glocal.json"
    plan_args = Namespace(
        media_action="plan",
        engine="ffmpeg",
        action="private-client-glocal",
        input_path=str(input_file),
        output_path=str(tmp_path / "out.mp4"),
        member_token="+æ",
        governance="none",
        surface="æ://private client^glocal",
        manifest=str(manifest),
    )

    try:
        media.media_command(plan_args)
    except SystemExit as exc:
        assert exc.code == 0

    payload = media._read_manifest(manifest)
    assert payload["surface"] == "æ://private client^glocal"
    assert payload["local_only"] is True
    assert payload["runtime"] == "ae://local^ollama"
    assert payload["cloud"] is False

    audit_args = Namespace(media_action="audit", manifest=str(manifest))
    try:
        media.media_command(audit_args)
    except SystemExit as exc:
        assert exc.code == 0


def test_media_coevolve_success_with_mocked_ollama_and_ffmpeg(monkeypatch, tmp_path):
    hermes_home = tmp_path / "home"
    hermes_home.mkdir(parents=True, exist_ok=True)
    input_file = tmp_path / "input.mp4"
    input_file.write_bytes(b"fake media bytes")
    output_file = tmp_path / "out.mp4"
    output_file.write_bytes(b"x" * 2048)

    monkeypatch.setattr(media, "get_hermes_home", lambda: hermes_home)

    def fake_ollama_plan(goal, input_path, output_path, codec, fps, bitrate, model):
        return {
            "codec": codec or "h264_nvenc",
            "fps": fps,
            "bitrate": bitrate,
            "filters": "",
            "expected_output_sha256": media._sha256_file(output_file),
            "pass_criteria": {"min_output_bytes": 1},
            "retry_policy": {"max_retries": 1},
            "notes": "test plan",
        }

    def fake_run(command, **kwargs):
        class Result:
            returncode = 0
            stdout = b""
        return Result()

    monkeypatch.setattr(media, "_ollama_generate_plan", fake_ollama_plan)
    monkeypatch.setattr(media.subprocess, "run", fake_run)

    args = argparse.Namespace(
        media_action="coevolve",
        goal="optimize for mobile shortform",
        input_path=str(input_file),
        output_path=str(output_file),
        codec="h264_nvenc",
        fps=30,
        bitrate="2M",
        model="qwen2.5-coder:3b",
        retries=1,
        member_token="+æ",
        governance="none",
        manifest=str(tmp_path / "coevolve.json"),
    )

    try:
        media.media_command(args)
    except SystemExit as exc:
        assert exc.code == 0

    manifest = media._read_manifest(tmp_path / "coevolve.json")
    assert manifest["action"] == "coevolve:optimize for mobile shortform"
    assert manifest["command"][7] == "h264_nvenc"
    assert manifest["iterations"] == 1


def test_media_coevolve_fails_closed_after_bounded_retries(monkeypatch, tmp_path):
    hermes_home = tmp_path / "home"
    hermes_home.mkdir(parents=True, exist_ok=True)
    input_file = tmp_path / "input.mp4"
    input_file.write_bytes(b"fake media bytes")
    output_file = tmp_path / "out.mp4"
    output_file.write_text("")

    monkeypatch.setattr(media, "get_hermes_home", lambda: hermes_home)
    state = {"calls": 0}

    def cheap_plan(*args, **kwargs):
        return {"codec": "h264_nvenc", "fps": 30, "bitrate": "2M", "filters": "", "expected_output_sha256": "deadbeef"}

    def fake_run(command, **kwargs):
        state["calls"] += 1
        class Result:
            returncode = 1
            stdout = b"error"
        return Result()

    monkeypatch.setattr(media, "_ollama_generate_plan", cheap_plan)
    monkeypatch.setattr(subprocess, "run", fake_run)

    args = argparse.Namespace(
        media_action="coevolve",
        goal="optimize for mobile shortform",
        input_path=str(input_file),
        output_path=str(output_file),
        codec="h264_nvenc",
        fps=30,
        bitrate="2M",
        model="qwen2.5-coder:3b",
        retries=1,
        member_token="+æ",
        governance="none",
        manifest=str(tmp_path / "coevolve-fail.json"),
    )

    try:
        media.media_command(args)
    except SystemExit as exc:
        assert exc.code == 2

    assert state["calls"] == 2
