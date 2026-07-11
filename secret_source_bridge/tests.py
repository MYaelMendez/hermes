"""Conformance + behavior tests for local_bridge secret-source plugin."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from secret_source_bridge import LocalBridgeSecretSource, ActionError


@pytest.fixture
def plugin(tmp_path: Path):
    store = tmp_path / "store.json"
    p = LocalBridgeSecretSource()
    p._path = store
    return p


class TestConformanceProfile:
    def test_malformed_add_returns_payload_invalid(self, plugin):
        res = plugin.action("add", {"value": "x"})
        assert res.error != ""
        assert res.error_kind == ActionError.PAYLOAD_INVALID

    def test_unknown_action_returns_not_allowed(self, plugin):
        res = plugin.action("__unknown__", {})
        assert res.error_kind == ActionError.ACTION_NOT_ALLOWED
        assert res.error

    def test_valid_add_succeeds(self, plugin):
        res = plugin.action("add", {"key": "NPM_TOKEN", "value": "abc", "kind": "token", "note": "opensourceware"})
        assert res.error == ""

    def test_remove_missing_key_returns_ref_invalid(self, plugin):
        res = plugin.action("remove", {"key": "absent"})
        assert res.error_kind == ActionError.REF_INVALID

    def test_list_never_returns_raw_values(self, plugin):
        plugin.action("add", {"key": "A", "value": "secret1", "kind": "token"})
        plugin.action("add", {"key": "B", "value": "secret2", "kind": "password"})
        res = plugin.action("list", {})
        assert res.error == ""
        assert res.document["selections"][0].get("value") is None
        assert res.document["selections"][0]["key"] == "A"

    def test_fetch_round_trip(self, plugin):
        plugin.action("add", {"key": "NPM_TOKEN", "value": "npmpass", "kind": "token", "note": "publish"})
        fetched = plugin.fetch()
        assert "NPM_TOKEN" in fetched.secrets
        assert fetched.secrets["NPM_TOKEN"].value == "npmpass"
        assert fetched.secrets["NPM_TOKEN"].provider == "local_bridge"

    def test_positive_timeout_budget(self, plugin):
        assert plugin.fetch_timeout_seconds({}) >= 1

    def test_clear_requires_explicit_confirm(self, plugin):
        plugin.action("add", {"key": "X", "value": "v"})
        res = plugin.action("clear", {})
        assert res.error != ""
        res = plugin.action("clear", {"confirm": "yes"})
        assert res.error == ""

    def test_invalid_kind_rejected(self, plugin):
        res = plugin.action("add", {"key": "X", "value": "v", "kind": "raw"})
        assert res.error != ""
        assert res.error_kind == ActionError.PAYLOAD_INVALID

    def test_search_by_kind_empty_selection(self, plugin):
        plugin.action("add", {"key": "X", "value": "v", "kind": "token"})
        res = plugin.action("search_by_kind", {"kind": "password"})
        assert res.error == ""
        assert res.document["selections"] == []


class TestActionContract:
    def test_add_update_remove_flow(self, plugin):
        res = plugin.action("add", {"key": "X", "value": "1", "kind": "generic"})
        assert res.error == ""
        res = plugin.action("update", {"key": "X", "value": "2", "note": "rotated"})
        assert res.error == ""
        assert plugin.fetch().secrets["X"].value == "2"
        res = plugin.action("remove", {"key": "X"})
        assert res.error == ""
        assert "X" not in plugin.fetch().secrets

    def test_reveal_boundary_is_explicit(self, plugin):
        plugin.action("add", {"key": "X", "value": "v", "kind": "token"})
        res = plugin.action("reveal", {"key": "X"})
        assert res.error == ""
        assert res.secrets["X"].value == "v"

    def test_export_env_writes_file(self, plugin, tmp_path: Path):
        plugin.action("add", {"key": "X", "value": "abc", "kind": "generic"})
        out = tmp_path / "secrets.env"
        res = plugin.action("export_env", {"path": str(out)})
        assert res.error == ""
        assert res.document["path"] == str(out)
        content = out.read_text(encoding="utf-8")
        assert content == "X=abc\n"

    def test_import_json_merges_payload(self, plugin, tmp_path: Path):
        payload = {
            "schema": "hermes.secret.source.bridge.v1",
            "secrets": [
                {"key": "X", "value": "v1", "kind": "token", "note": "n"},
                {"key": "Y", "value": "v2", "note": "m"},
            ],
        }
        src = tmp_path / "in.json"
        src.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        res = plugin.action("import_json", {"path": str(src)})
        assert res.error == ""
        assert len(plugin.fetch().secrets) == 2

    def test_stats_counts_by_kind(self, plugin):
        plugin.action("add", {"key": "X", "value": "v", "kind": "token"})
        plugin.action("add", {"key": "Y", "value": "v", "kind": "password"})
        plugin.action("add", {"key": "Z", "value": "v", "kind": "generic"})
        res = plugin.action("stats", {})
        assert res.error == ""
        counts = res.document.get("counts", {})
        assert counts.get("token") == 1
        assert counts.get("password") == 1
        assert counts.get("generic") == 1

    def test_rotate_note_updates_timestamp(self, plugin):
        plugin.action("add", {"key": "X", "value": "v", "kind": "generic", "note": "old"})
        res = plugin.action("rotate_note", {"key": "X", "note": "rotated"})
        assert res.error == ""
        rec = plugin._load_store()["X"]
        assert rec["note"] == "rotated"
        assert rec["updated_at"] != "old"

    def test_bulk_upsert(self, plugin):
        items = [
            {"key": "X", "value": "v1", "kind": "token"},
            {"key": "Y", "value": "v2", "kind": "password", "note": "n"},
            {"key": "", "value": "skip"},
        ]
        res = plugin.action("bulk_upsert", {"items": items})
        assert res.error == ""
        assert res.document["upserted"] == 2
        assert plugin.fetch().secrets["Y"].metadata["note"] == "n"

    def test_validate_entry_returns_secret_without_saving(self, plugin):
        res = plugin.action("validate_entry", {"key": "X", "value": "v", "kind": "token"})
        assert res.error == ""
        assert "X" in res.secrets
        assert len(plugin.fetch().secrets) == 0


class TestEdgeContract:
    def test_boundary_never_leaks_values_in_list(self, plugin):
        plugin.action("add", {"key": "SECRET", "value": "raw", "kind": "api_key"})
        res = plugin.action("list", {})
        payload = json.dumps(res.document)
        assert "raw" not in payload

    def test_fetch_document_repr_masks_raw_value(self, plugin):
        plugin.action("add", {"key": "A", "value": "raw", "kind": "token"})
        fetched = plugin.fetch()
        docs = {k: v.as_document() for k, v in fetched.secrets.items()}
        assert docs["A"]["value_repr"] != "raw"
        assert docs["A"]["provider"] == "local_bridge"
