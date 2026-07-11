#!/usr/bin/env python3
"""Emit a high-signal local context map for Hermes glocal monorepo operation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent


def sha256_text(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_map() -> dict[str, Any]:
    contract_path = REPO_ROOT / "glocal-monorepo.json"
    contract = read_json(contract_path)

    control = contract.get("control_plane", {})
    control_files = {
        key: str(REPO_ROOT / rel_path)
        for key, rel_path in control.items()
    }

    control_hashes: dict[str, str] = {}
    for key, rel_path in control.items():
        file_path = REPO_ROOT / rel_path
        if file_path.exists():
            control_hashes[key] = sha256_text(file_path)

    submission_path = REPO_ROOT / "contest-submission"
    submission_files = []
    if submission_path.exists():
        for p in sorted(submission_path.rglob("*")):
            if p.is_file():
                submission_files.append(str(p.relative_to(REPO_ROOT)).replace("\\", "/"))

    return {
        "schema_version": 1,
        "repo_root": str(REPO_ROOT),
        "contract": {
            "path": "glocal-monorepo.json",
            "sha256": sha256_text(contract_path) if contract_path.exists() else None,
        },
        "primitive": contract.get("primitive", "glocal-git"),
        "mode": contract.get("mode", "local-first"),
        "domains": contract.get("domains", {}),
        "surfaces": contract.get("surfaces", []),
        "runtime": contract.get("runtime", {}),
        "workspaces": contract.get("workspaces", []),
        "control_plane": {
            "files": control_files,
            "sha256": control_hashes,
        },
        "submission": {
            "path": "contest-submission",
            "file_count": len(submission_files),
            "files": submission_files,
        },
        "verification_commands": [
            "python -m pytest tests/hermes_cli/test_media.py -q",
            "cd vscode-remote-use && npm run compile",
            "cd vscode-remote-use && npx @vscode/vsce package",
        ],
    }


def main() -> None:
    payload = build_map()
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
