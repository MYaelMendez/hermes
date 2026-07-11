"""Tests for the coremode operator snapshot command."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DAO_ROOT = REPO_ROOT / "dao"


def test_codemode_returns_expected_top_level_keys():
    from scripts.coremode import build_payload

    payload = build_payload()
    for key in {
        "schema_version",
        "command",
        "generated_utc",
        "glocal",
        "dao",
        "integrity",
        "vitals",
        "namespaces",
    }:
        assert key in payload


def test_codemode_dao_status_fields():
    from scripts.coremode import build_payload

    payload = build_payload()
    dao = payload["dao"]
    assert dao["root"] == str(REPO_ROOT / "dao")
    assert dao["surface"] == "æ://private client^glocal"
    assert isinstance(dao["members"], int)
    assert isinstance(dao["treasury_entries"], int)
    assert isinstance(dao["open_proposals"], int)


def test_codemode_integrity_is_pass():
    from scripts.coremode import build_payload

    payload = build_payload()
    assert payload["integrity"]["ok"] is True


def test_codemode_namespaces_include_dao_surface():
    from scripts.coremode import build_payload

    payload = build_payload()
    uris = [ns["uri"] for ns in payload["namespaces"]]
    assert "æ://HERMES-AGENT^media" in uris
    assert "æ://private client^glocal" in uris
    assert "æ://glocal^skills/agentic-entrepreneurship/dao" in uris
