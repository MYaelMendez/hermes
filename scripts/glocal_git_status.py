#!/usr/bin/env python3
"""Emit glocal-git state: local execution truth + global export surfaces."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRACT_PATH = REPO_ROOT / "glocal-monorepo.json"


def read_contract() -> dict[str, Any]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def run_git(*args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=str(REPO_ROOT),
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return ""
    return completed.stdout.strip()


def git_state() -> dict[str, Any]:
    branch = run_git("rev-parse", "--abbrev-ref", "HEAD")
    commit = run_git("rev-parse", "HEAD")
    short_commit = run_git("rev-parse", "--short", "HEAD")
    porcelain = run_git("status", "--porcelain")
    return {
        "branch": branch or "unknown",
        "commit": commit or "unknown",
        "short_commit": short_commit or "unknown",
        "dirty": bool(porcelain),
        "changed_files": len([line for line in porcelain.splitlines() if line.strip()]),
    }


def main() -> None:
    contract = read_contract()
    domains = contract.get("domains", {})
    payload = {
        "schema_version": 1,
        "primitive": contract.get("primitive", "glocal-git"),
        "repo_root": str(REPO_ROOT),
        "local_truth": domains.get("local_truth", {}),
        "global_surface": domains.get("global_surface", {}),
        "git": git_state(),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
