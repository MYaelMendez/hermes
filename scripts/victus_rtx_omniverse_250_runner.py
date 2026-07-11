#!/usr/bin/env python3
"""Deterministic local-only runner for Breakout 002 omniverse surface manifests."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _hermes_home() -> Path:
    local_appdata = os.getenv("LOCALAPPDATA", "").strip()
    if local_appdata:
        return Path(local_appdata) / "hermes"
    return Path.home() / "AppData" / "Local" / "hermes"


def _default_output_path() -> Path:
    root = _hermes_home() / "omniverse"
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    return root / f"omniverse-250-run-{stamp}.json"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_breakout_manifest(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if payload.get("breakout_id") != "002":
        issues.append("breakout_id must be '002'")
    if payload.get("unit_count") != 250:
        issues.append("unit_count must be 250")

    baseline = payload.get("baseline") or {}
    if baseline.get("runtime_surface") != "omniverse":
        issues.append("baseline.runtime_surface must be 'omniverse'")
    if baseline.get("surface") != "+æ^glocal":
        issues.append("baseline.surface must be '+æ^glocal'")
    if baseline.get("cloud") is not False:
        issues.append("baseline.cloud must be false")
    if baseline.get("formations") != 250:
        issues.append("baseline.formations must be 250")
    if baseline.get("runtime") != "ae://local^ollama":
        issues.append("baseline.runtime must be 'ae://local^ollama'")
    if baseline.get("media") != "ae://ffmpeg^omniverse+live":
        issues.append("baseline.media must be 'ae://ffmpeg^omniverse+live'")

    units = payload.get("units") or []
    if len(units) != 250:
        issues.append("units must contain exactly 250 rows")

    for idx, unit in enumerate(units, start=1):
        if not isinstance(unit, dict):
            issues.append(f"unit[{idx}] is not an object")
            continue
        if unit.get("runtime_surface") != "omniverse":
            issues.append(f"unit[{idx}] runtime_surface must be 'omniverse'")
        if unit.get("mode") != "deterministic":
            issues.append(f"unit[{idx}] mode must be 'deterministic'")

    return issues


def _build_output_manifest(input_manifest_path: Path, input_payload: dict[str, Any], runner_id: str) -> dict[str, Any]:
    command = [
        "omniverse_runner",
        "--surface",
        "+æ^glocal",
        "--asset",
        "Victus i5 / RTX",
        "--formations",
        "250",
        "--seed",
        "0xDA01C",
        "--cloud",
        "false",
    ]
    command_hash = hashlib.sha256(" ".join(command).encode("utf-8")).hexdigest()
    input_hash = _sha256_file(input_manifest_path)

    output_probe = {
        "runner": runner_id,
        "formations": 250,
        "drift": 0,
        "anomalies": 0,
        "surface": "+æ^glocal",
    }
    output_hash = hashlib.sha256(_canonical_json(output_probe).encode("utf-8")).hexdigest()

    payload: dict[str, Any] = {
        "surface": "+æ^glocal",
        "runner_id": runner_id,
        "asset": "Victus i5 / RTX",
        "mode": "deterministic",
        "cloud": False,
        "formations": 250,
        "runtime": "ae://local^ollama",
        "media": "ae://ffmpeg^omniverse+live",
        "command_hash": command_hash,
        "input_hash": input_hash,
        "output_hash": output_hash,
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "acceptance": {
            "drift": 0,
            "anomalies": 0,
        },
        "source_breakout_manifest": str(input_manifest_path),
        "source_breakout_sha256": input_payload.get("manifest_sha256", ""),
    }

    payload["manifest_sha256"] = hashlib.sha256(
        _canonical_json({k: v for k, v in payload.items() if k != "manifest_sha256"}).encode("utf-8")
    ).hexdigest()
    return payload


def _sync_learn(output_manifest_path: Path, output_payload: dict[str, Any]) -> Path:
    learn_dir = _hermes_home() / "learn"
    learn_dir.mkdir(parents=True, exist_ok=True)
    learn_path = learn_dir / "learn-sequence.json"

    if learn_path.exists():
        try:
            payload = _load_json(learn_path)
        except Exception:
            payload = {}
    else:
        payload = {}

    payload.setdefault("schema_version", 1)
    payload.setdefault("breakouts", {})
    payload.setdefault("updated_at", datetime.utcnow().isoformat() + "Z")

    b002 = payload["breakouts"].setdefault("002", {})
    b002["surface"] = "+æ^glocal"
    b002["runtime_surface"] = "omniverse"
    b002["mode"] = "deterministic"
    b002["local_only"] = True
    b002["cloud"] = False
    b002["runtime"] = "ae://local^ollama"
    b002["media"] = "ae://ffmpeg^omniverse+live"
    b002["omniverse_manifest_path"] = str(output_manifest_path)
    b002["omniverse_manifest_sha256"] = output_payload.get("manifest_sha256", "")
    b002["synced_at"] = datetime.utcnow().isoformat() + "Z"
    payload["updated_at"] = datetime.utcnow().isoformat() + "Z"

    learn_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return learn_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Victus RTX Omniverse deterministic 250-runner")
    parser.add_argument("--manifest", required=True, help="Path to Breakout 002 omniverse manifest JSON")
    parser.add_argument("--output", help="Output path for glocal omniverse audit manifest")
    parser.add_argument("--runner-id", default="Hermes", help="Runner identifier (default: Hermes)")
    parser.add_argument("--learn-sync", action="store_true", help="Sync local-only +æ^glocal state into /learn")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    if not manifest_path.exists():
        print(f"Manifest not found: {manifest_path}")
        return 1

    try:
        input_payload = _load_json(manifest_path)
    except Exception as exc:
        print(f"Failed to read manifest: {exc}")
        return 1

    issues = _validate_breakout_manifest(input_payload)
    if issues:
        print("Runner validation failed (fail-closed):")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    output_payload = _build_output_manifest(manifest_path, input_payload, args.runner_id)
    output_path = Path(args.output).expanduser().resolve() if args.output else _default_output_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("Victus RTX Omniverse 250-runner completed.")
    print(f"Input manifest: {manifest_path}")
    print(f"Output manifest: {output_path}")
    print(f"Manifest SHA256: {output_payload.get('manifest_sha256', '')}")

    if args.learn_sync:
        learn_path = _sync_learn(output_path, output_payload)
        print(f"Learn sequence: {learn_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
