"""Operator control plane for glocal runtime: codemode snapshot."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _to_int(value: Any) -> Any:
    try:
        return int(value)
    except Exception:
        return value


def _dao_status() -> dict[str, Any]:
    try:
        from hermes_cli.dao import _status as _dao_status_inner  # type: ignore[attr-defined]
    except Exception:
        _ensure_path()
        from hermes_cli.dao import _status as _dao_status_inner  # type: ignore[attr-defined]
    if not callable(_dao_status_inner):
        class _Shim:
            @staticmethod
            def main() -> int:
                return _legacy_dao_status()
        _dao_status_inner = _Shim.main
    raw: dict[str, Any] = {"_wrapper": _dao_status_inner()}
    if isinstance(raw, dict) and "root" in raw:
        return raw
    return _legacy_dao_status()


def _ensure_path() -> None:
    root_str = str(REPO_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def _legacy_dao_status() -> dict[str, Any]:
    try:
        from hermes_cli.dao import (  # type: ignore[import]
            _dao_paths,
            _load_members,
            _load_treasury,
            _load_proposals,
        )
    except Exception:
        _ensure_path()
        from hermes_cli.dao import (  # type: ignore[import]
            _dao_paths,
            _load_members,
            _load_treasury,
            _load_proposals,
        )
    paths = _dao_paths()
    charter = paths.get("charter")
    members = paths.get("members")
    treasury = paths.get("treasury")
    proposals = paths.get("proposals")
    members_payload = _load_members()
    treasury_payload = _load_treasury()
    proposals_payload = _load_proposals()
    member_count = len(members_payload.get("members", []))
    treasury_entries = len(treasury_payload.get("entries", []))
    open_proposals = [p for p in proposals_payload.get("proposals", []) if str(p.get("status", "draft")) in {"draft", "review"}]
    return {
        "root": str(REPO_ROOT / "dao"),
        "charter": str(charter) if charter else None,
        "surface": members_payload.get("surface", "unknown"),
        "members": member_count,
        "treasury_entries": treasury_entries,
        "open_proposals": len(open_proposals),
    }


def _run_main(script_name: str, *args: str) -> dict[str, Any] | None:
    module_path = REPO_ROOT / script_name
    command = [sys.executable, str(module_path), *args]
    try:
        completed = subprocess.run(
            command,
            cwd=str(REPO_ROOT),
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(completed.stdout)
    except Exception:
        return None


def _glocal_status() -> dict[str, Any]:
    payload = _run_main("scripts/glocal_git_status.py")
    if payload is None:
        return {"error": "glocal status unavailable"}
    return payload


def _context_map() -> dict[str, Any]:
    payload = _run_main("scripts/glocal_context_map.py")
    if payload is None:
        return {"error": "glocal context map unavailable"}
    return payload


def _integrity_status() -> dict[str, Any]:
    script = REPO_ROOT / "scripts" / "verify_submission_integrity.py"
    command = [sys.executable, str(script)]
    try:
        completed = subprocess.run(
            command,
            cwd=str(REPO_ROOT),
            check=True,
            capture_output=True,
            text=True,
        )
        return {"ok": True, "stdout": completed.stdout.strip()}
    except subprocess.CalledProcessError as exc:
        return {
            "ok": False,
            "returncode": exc.returncode,
            "stdout": exc.stdout.strip(),
            "stderr": exc.stderr.strip(),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _vitals_snapshot() -> dict[str, Any]:
    return _run_main("scripts/computer_vitals.py") or {"error": "vitals unavailable"}


def build_payload() -> dict[str, Any]:
    glocal = _glocal_status()
    dao = _dao_status()
    integrity = _integrity_status()
    vitals = _vitals_snapshot()
    raw_namespaces = _context_map()
    namespaces = [
        {
            "uri": "æ://HERMES-AGENT^media",
            "path": "hermes_cli/media.py",
            "test": "tests/hermes_cli/test_media.py",
        },
        {
            "uri": "æ://private client^glocal",
            "path": "C:/æ",
            "surface": "agentic.html + dao + store",
        },
    ]
    if "error" not in raw_namespaces:
        domains = raw_namespaces.get("domains", {})
        if domains.get("dao") and "æ://glocal^skills/agentic-entrepreneurship/dao" not in [ns.get("uri") for ns in namespaces]:
            namespaces.append({
                "uri": "æ://glocal^skills/agentic-entrepreneurship/dao",
                "path": "C:/æ/agentic-entrepreneurship/dao/index.html",
            })
    return {
        "schema_version": 1,
        "command": "hermes coremode",
        "generated_utc": _now_utc(),
        "glocal": glocal,
        "dao": dao,
        "integrity": integrity,
        "vitals": vitals,
        "namespaces": namespaces,
    }


def main() -> int:
    payload = build_payload()
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
