#!/usr/bin/env python3
"""Register local ML experiment runs in ml/experiments/registry.json."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "ml" / "experiments" / "registry.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def load_registry() -> dict:
    if not REGISTRY_PATH.exists():
        return {"schema_version": 1, "runs": []}
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def to_repo_relative(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT.resolve())).replace("\\", "/")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Register a local ML run")
    parser.add_argument("--name", required=True, help="Run name")
    parser.add_argument("--config", required=True, help="Path to run config JSON")
    parser.add_argument("--metrics", required=True, help="Path to metrics JSON")
    parser.add_argument("--notes", default="", help="Optional notes")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    config_path = (REPO_ROOT / args.config).resolve() if not Path(args.config).is_absolute() else Path(args.config)
    metrics_path = (REPO_ROOT / args.metrics).resolve() if not Path(args.metrics).is_absolute() else Path(args.metrics)

    if not config_path.exists():
        print(f"Config file not found: {config_path}")
        return 1
    if not metrics_path.exists():
        print(f"Metrics file not found: {metrics_path}")
        return 1

    config_payload = json.loads(config_path.read_text(encoding="utf-8"))
    metrics_payload = json.loads(metrics_path.read_text(encoding="utf-8"))

    registry = load_registry()
    runs = registry.setdefault("runs", [])

    run_id = f"run-{len(runs) + 1:04d}"
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    run_entry = {
        "run_id": run_id,
        "created_at_utc": now,
        "name": args.name,
        "config": {
            "path": to_repo_relative(config_path),
            "sha256": sha256_file(config_path),
            "payload": config_payload,
        },
        "metrics": {
            "path": to_repo_relative(metrics_path),
            "sha256": sha256_file(metrics_path),
            "payload": metrics_payload,
        },
        "notes": args.notes,
    }

    runs.append(run_entry)
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("ML run registered.")
    print(f"Run ID: {run_id}")
    print(f"Registry: {REGISTRY_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
