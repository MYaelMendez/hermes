"""Innovation: Hermes Secret Source Bridge plugin — local sovereign secret manager."""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple


DEFAULT_STORE_PATH = str(Path.home() / ".hermes" / "secrets" / "local_bridge.json")
STORE_ENV = "HERMES_SECRET_BRIDGE_PATH"
ALLOWED_KINDS = {"token", "password", "api_key", "generic"}


class _StrEnum(str):
    @property
    def value(self) -> str:
        return self


class ActionError:
    NOT_CONFIGURED: _StrEnum = _StrEnum("NOT_CONFIGURED")
    BINARY_MISSING: _StrEnum = _StrEnum("BINARY_MISSING")
    AUTH_FAILED: _StrEnum = _StrEnum("AUTH_FAILED")
    REF_INVALID: _StrEnum = _StrEnum("REF_INVALID")
    NETWORK: _StrEnum = _StrEnum("NETWORK")
    EMPTY_VALUE: _StrEnum = _StrEnum("EMPTY_VALUE")
    TIMEOUT: _StrEnum = _StrEnum("TIMEOUT")
    ACTION_NOT_ALLOWED: _StrEnum = _StrEnum("ACTION_NOT_ALLOWED")
    PAYLOAD_INVALID: _StrEnum = _StrEnum("PAYLOAD_INVALID")
    BOUNDARY: _StrEnum = _StrEnum("BOUNDARY")


@dataclass
class SecretValue:
    value: Optional[str] = None
    provider: Optional[str] = None
    input_types: Optional[list] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)

    def as_document(self) -> Dict[str, Any]:
        return {"provider": self.provider, "value_repr": f"[{len(self.value or '')} chars]", "metadata": dict(self.metadata or {})}


@dataclass
class SecretSourceResult:
    secrets: Dict[str, SecretValue] = field(default_factory=dict)
    error: str = ""
    error_kind: str = ""
    status: str = "ok"
    document: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionReferenceResult:
    secrets: Dict[str, SecretValue] = field(default_factory=dict)
    error: str = ""
    error_kind: str = ""
    document: Dict[str, Any] = field(default_factory=dict)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _to_masked(value: str) -> Tuple[str, Optional[str]]:
    if len(value) <= 2:
        return f"[{len(value)} chars]", None
    return value[:2] + "." * (len(value) - 2), None


def _validate_entry_payload(payload: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    key = payload.get("key")
    value = payload.get("value")
    kind = payload.get("kind", "generic")
    note = payload.get("note", "")
    if not isinstance(key, str) or not key.strip():
        return None, None, None, None, "key must be a non-empty string"
    kind = kind.strip().lower()
    if kind not in ALLOWED_KINDS:
        return None, None, None, None, "kind must be token|password|api_key|generic"
    if not isinstance(value, str):
        return None, None, None, None, "value must be a string"
    return key.strip(), value, kind, str(note or "").strip(), None


class BoundaryViolation(Exception):
    pass


class ActionReference:
    @staticmethod
    def validate_entry(store: Dict[str, Dict[str, Any]], payload: Dict[str, Any]) -> ActionReferenceResult:
        key, value, kind, note, err = _validate_entry_payload(payload)
        if err:
            return ActionReferenceResult(error=err, error_kind=ActionError.PAYLOAD_INVALID)
        secret_value = SecretValue(value=value, provider="local_bridge", input_types=["output"])
        return ActionReferenceResult(secrets={key: secret_value})

    @staticmethod
    def add(store: Dict[str, Dict[str, Any]], payload: Dict[str, Any]) -> ActionReferenceResult:
        key, value, kind, note, err = _validate_entry_payload(payload)
        if err:
            return ActionReferenceResult(error=err, error_kind=ActionError.PAYLOAD_INVALID)
        if "+" in key:
            return ActionReferenceResult(error="key contains invalid characters", error_kind=ActionError.PAYLOAD_INVALID)
        value_mask, mask_err = _to_masked(value)
        if mask_err:
            return ActionReferenceResult(error=mask_err, error_kind=ActionError.PAYLOAD_INVALID)
        updated_at = _utcnow()
        store[key] = {"kind": kind, "value": value, "value_mask": value_mask, "note": note, "created_at": updated_at, "updated_at": updated_at}
        return ActionReferenceResult(document={"added": [{"key": key, "kind": kind, "updated_at": updated_at}]})

    @staticmethod
    def update(store: Dict[str, Dict[str, Any]], payload: Dict[str, Any]) -> ActionReferenceResult:
        key = str(payload.get("key", "")).strip()
        if key not in store:
            return ActionReferenceResult(error="missing key", error_kind=ActionError.REF_INVALID)
        kind = str(payload.get("kind", store[key].get("kind", "generic"))).strip().lower()
        value = payload.get("value", store[key].get("value", ""))
        note = str(payload.get("note", store[key].get("note", ""))).strip()
        if kind not in ALLOWED_KINDS:
            return ActionReferenceResult(error="kind must be token|password|api_key|generic", error_kind=ActionError.PAYLOAD_INVALID)
        if not isinstance(value, str):
            return ActionReferenceResult(error="value must be a string", error_kind=ActionError.PAYLOAD_INVALID)
        value_mask, mask_err = _to_masked(value)
        if mask_err:
            return ActionReferenceResult(error=mask_err, error_kind=ActionError.PAYLOAD_INVALID)
        updated_at = _utcnow()
        rec = store[key]
        rec.update({"kind": kind, "value": value, "value_mask": value_mask, "note": note, "updated_at": updated_at})
        return ActionReferenceResult(document={"updated": [{"key": key, "kind": kind, "updated_at": updated_at}]})

    @staticmethod
    def remove(store: Dict[str, Dict[str, Any]], payload: Dict[str, Any]) -> ActionReferenceResult:
        key = str(payload.get("key", "")).strip()
        if not key:
            return ActionReferenceResult(error="key is required", error_kind=ActionError.PAYLOAD_INVALID)
        if key not in store:
            return ActionReferenceResult(error="missing key", error_kind=ActionError.REF_INVALID)
        del store[key]
        return ActionReferenceResult(document={"removed": [key]})

    @staticmethod
    def list_(store: Dict[str, Dict[str, Any]], payload: Dict[str, Any]) -> ActionReferenceResult:
        kind_filter = str(payload.get("kind", "")).strip().lower() or None
        items = []
        for key, rec in store.items():
            if kind_filter and rec.get("kind") != kind_filter:
                continue
            items.append(
                {
                    "key": key,
                    "kind": rec.get("kind"),
                    "note": rec.get("note"),
                    "updated_at": rec.get("updated_at"),
                    "created_at": rec.get("created_at"),
                }
            )
        return ActionReferenceResult(document={"selections": items})

    @staticmethod
    def reveal(store: Dict[str, Dict[str, Any]], payload: Dict[str, Any]) -> ActionReferenceResult:
        key = str(payload.get("key", "")).strip()
        if not key:
            return ActionReferenceResult(error="key is required", error_kind=ActionError.PAYLOAD_INVALID)
        if key not in store:
            return ActionReferenceResult(error="missing key", error_kind=ActionError.REF_INVALID)
        rec = store[key]
        secret_value = SecretValue(
            value=rec.get("value", ""),
            provider="local_bridge",
            input_types=["output"],
            metadata={"kind": rec.get("kind"), "note": rec.get("note"), "updated_at": rec.get("updated_at")},
        )
        return ActionReferenceResult(secrets={key: secret_value})

    @staticmethod
    def export_env(store: Dict[str, Dict[str, Any]], payload: Dict[str, Any]) -> ActionReferenceResult:
        path = str(payload.get("path", "")).strip()
        if not path:
            return ActionReferenceResult(error="path is required", error_kind=ActionError.PAYLOAD_INVALID)
        if "\x00" in path or path.strip() != path or ".." in Path(path).parts:
            return ActionReferenceResult(error="path is invalid", error_kind=ActionError.PAYLOAD_INVALID)
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            lines = [f"{key}={store[key]['value']}\n" for key in sorted(store.keys())]
            Path(path).write_text("".join(lines), encoding="utf-8")
        except OSError as exc:
            return ActionReferenceResult(error=str(exc), error_kind=ActionError.NETWORK)
        return ActionReferenceResult(document={"exported": "env", "path": path, "count": len(store)})

    @staticmethod
    def import_json(store: Dict[str, Dict[str, Any]], payload: Dict[str, Any]) -> ActionReferenceResult:
        path = str(payload.get("path", "")).strip()
        if not path:
            return ActionReferenceResult(error="path is required", error_kind=ActionError.PAYLOAD_INVALID)
        try:
            raw = Path(path).read_text(encoding="utf-8")
            payload_obj = json.loads(raw)
        except (OSError, json.JSONDecodeError) as exc:
            return ActionReferenceResult(error=str(exc), error_kind=ActionError.NETWORK)
        if not isinstance(payload_obj, dict) or "secrets" not in payload_obj:
            return ActionReferenceResult(error="invalid shape", error_kind=ActionError.PAYLOAD_INVALID)
        items = payload_obj.get("secrets", [])
        if not isinstance(items, list):
            return ActionReferenceResult(error="secrets must be an array", error_kind=ActionError.PAYLOAD_INVALID)
        updated_at = _utcnow()
        upserted = 0
        for item in items:
            if not isinstance(item, dict):
                continue
            key, value, kind, note, err = _validate_entry_payload(item)
            if err:
                return ActionReferenceResult(error=err, error_kind=ActionError.PAYLOAD_INVALID)
            store[key] = {
                "kind": kind,
                "value": value,
                "value_mask": _to_masked(value)[0],
                "note": note,
                "created_at": str(item.get("created_at", updated_at)),
                "updated_at": updated_at,
            }
            upserted += 1
        return ActionReferenceResult(document={"imported": "json", "upserted": upserted, "path": path})

    @staticmethod
    def clear(store: Dict[str, Dict[str, Any]], payload: Dict[str, Any]) -> ActionReferenceResult:
        confirm = str(payload.get("confirm", "")).strip().lower()
        if confirm != "yes":
            return ActionReferenceResult(error="confirm='yes' is required to clear all secrets", error_kind=ActionError.PAYLOAD_INVALID)
        store.clear()
        return ActionReferenceResult(document={"cleared": True})

    @staticmethod
    def stats(store: Dict[str, Dict[str, Any]], payload: Dict[str, Any]) -> ActionReferenceResult:
        counts = {kind: 0 for kind in ALLOWED_KINDS}
        for rec in store.values():
            k = str(rec.get("kind", "generic")).lower()
            if k in counts:
                counts[k] += 1
            else:
                counts["generic"] += 1
        return ActionReferenceResult(document={"counts": counts, "total": len(store)})

    @staticmethod
    def search_by_kind(store: Dict[str, Dict[str, Any]], payload: Dict[str, Any]) -> ActionReferenceResult:
        kind = str(payload.get("kind", "")).strip().lower()
        if kind not in ALLOWED_KINDS:
            return ActionReferenceResult(error="kind must be token|password|api_key|generic", error_kind=ActionError.PAYLOAD_INVALID)
        items = []
        for key, rec in store.items():
            if rec.get("kind") == kind:
                items.append(
                    {
                        "key": key,
                        "kind": rec.get("kind"),
                        "note": rec.get("note"),
                        "updated_at": rec.get("updated_at"),
                        "created_at": rec.get("created_at"),
                    }
                )
        return ActionReferenceResult(document={"selections": items})

    @staticmethod
    def bulk_upsert(store: Dict[str, Dict[str, Any]], payload: Dict[str, Any]) -> ActionReferenceResult:
        items = payload.get("items")
        if not isinstance(items, list):
            return ActionReferenceResult(error="items must be an array of {key,value,kind?,note?}", error_kind=ActionError.PAYLOAD_INVALID)
        updated_at = _utcnow()
        upserted = 0
        updated_keys = []
        for item in items:
            if not isinstance(item, dict):
                continue
            key, value, kind, note, err = _validate_entry_payload(item)
            if err:
                continue
            store[key] = {
                "kind": kind,
                "value": value,
                "value_mask": _to_masked(value)[0],
                "note": note,
                "created_at": str(item.get("created_at", updated_at)),
                "updated_at": updated_at,
            }
            upserted += 1
            updated_keys.append(key)
        return ActionReferenceResult(document={"upserted": upserted, "keys": updated_keys})

    @staticmethod
    def rotate_note(store: Dict[str, Dict[str, Any]], payload: Dict[str, Any]) -> ActionReferenceResult:
        key = str(payload.get("key", "")).strip()
        note = str(payload.get("note", "")).strip()
        if not key:
            return ActionReferenceResult(error="key is required", error_kind=ActionError.PAYLOAD_INVALID)
        if key not in store:
            return ActionReferenceResult(error="missing key", error_kind=ActionError.REF_INVALID)
        updated_at = _utcnow()
        rec = store[key]
        rec["note"] = note
        rec["updated_at"] = updated_at
        return ActionReferenceResult(document={"updated": [{"key": key, "updated_at": updated_at}]})


class LocalBridgeSecretSource:
    name = "local_bridge"
    api_version = "1"
    shape = "mapped"
    allowed_actions = {
        "validate_entry",
        "add",
        "update",
        "remove",
        "list",
        "reveal",
        "export_env",
        "import_json",
        "clear",
        "stats",
        "search_by_kind",
        "bulk_upsert",
        "rotate_note",
    }

    def __init__(self) -> None:
        self._path = Path(os.environ.get(STORE_ENV, DEFAULT_STORE_PATH))

    def is_enabled(self, cfg: Dict[str, Any]) -> bool:
        return bool(cfg.get("enabled", False))

    def override_existing(self, cfg: Dict[str, Any]) -> bool:
        return bool(cfg.get("override_existing", True))

    def protected_env_vars(self, cfg: Dict[str, Any]) -> Iterable[str]:
        return []

    def fetch_timeout_seconds(self, cfg: Dict[str, Any]) -> int:
        return int(cfg.get("timeout_seconds", 120))

    def config_schema(self) -> Dict[str, Any]:
        return {"path": "absolute store file path", "timeout_seconds": "int seconds, default 120"}

    def _load_store(self) -> Dict[str, Dict[str, Any]]:
        if not self._path.exists():
            return {}
        try:
            raw = self._path.read_text(encoding="utf-8")
            if not raw.strip():
                return {}
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def _write_store(self, store: Dict[str, Dict[str, Any]]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self._path)

    def fetch(self) -> SecretSourceResult:
        store = self._load_store()
        secrets: Dict[str, SecretValue] = {}
        invalid_keys: list = []
        for key, rec in store.items():
            if key + ":" + rec.get("kind", "") + ":" + str(rec.get("value", "")) == "":
                invalid_keys.append(key)
                continue
            if rec.get("kind") not in ALLOWED_KINDS:
                invalid_keys.append(key)
                continue
            secrets[key] = SecretValue(
                value=rec.get("value", ""),
                provider="local_bridge",
                input_types=["output"],
                metadata={"kind": rec.get("kind"), "note": rec.get("note"), "updated_at": rec.get("updated_at"), "created_at": rec.get("created_at")},
            )
        document: Dict[str, Any] = {"keys": invalid_keys}
        if invalid_keys:
            return SecretSourceResult(secrets=secrets, document=document, error="invalid entries skipped")
        return SecretSourceResult(secrets=secrets)

    def action(self, operation: str, payload: Dict[str, Any]) -> SecretSourceResult:
        store = self._load_store()
        operation = (operation or "").strip().lower()
        handler = {
            "validate_entry": ActionReference.validate_entry,
            "add": ActionReference.add,
            "update": ActionReference.update,
            "remove": ActionReference.remove,
            "list": ActionReference.list_,
            "reveal": ActionReference.reveal,
            "export_env": ActionReference.export_env,
            "import_json": ActionReference.import_json,
            "clear": ActionReference.clear,
            "stats": ActionReference.stats,
            "search_by_kind": ActionReference.search_by_kind,
            "bulk_upsert": ActionReference.bulk_upsert,
            "rotate_note": ActionReference.rotate_note,
        }.get(operation)
        if not handler:
            return SecretSourceResult(error=f"unsupported operation: {operation}", error_kind=ActionError.ACTION_NOT_ALLOWED)
        result = handler(store, payload)
        if not isinstance(result, ActionReferenceResult):
            raise BoundaryViolation("action handler returned unsupported result")
        if result.error:
            return SecretSourceResult(error=result.error, error_kind=result.error_kind, document=result.document)
        if operation not in {"validate_entry", "reveal", "list", "stats", "search_by_kind"}:
            self._write_store(store)
        secrets = {}
        for key, secret_value in result.secrets.items():
            secrets[key] = SecretValue(
                value=secret_value.value,
                provider=secret_value.provider,
                input_types=list(secret_value.input_types or []),
                metadata=dict(secret_value.metadata or {}),
            )
        return SecretSourceResult(secrets=secrets, document=result.document)


def register(ctx: Any) -> None:
    ctx.register_secret_source(LocalBridgeSecretSource())
