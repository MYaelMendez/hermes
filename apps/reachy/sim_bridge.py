"""Simulator bridge for hermes-reachy."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

REPO = Path(__file__).resolve().parents[2]
SIM_DIR = REPO / "simulation"
SIM_DIR.mkdir(exist_ok=True)
RUNTIME_FILE = SIM_DIR / "runs.jsonl"


class Contract(BaseModel):
    contract_id: str | None = None
    intent: str
    mode: str = "simulator"
    dao_approved: bool = False
    created_at: str | None = None


class RunResult(BaseModel):
    run_id: str
    contract_id: str
    outcome: dict[str, Any]
    telemetry: dict[str, Any]
    attestation_hash: str
    created_at: str


router = APIRouter()


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def append_run(record: dict) -> None:
    with RUNTIME_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=True) + "\n")


@router.post("/sim/contract")
async def sim_contract(contract: Contract) -> dict[str, object]:
    contract.created_at = now_iso()
    if not contract.contract_id:
        contract.contract_id = sha256_hex(contract.intent + contract.created_at)
    payload = {
        "ok": True,
        "contract": contract.model_dump(),
    }
    return payload


@router.post("/sim/run")
async def sim_run(contract: Contract) -> dict[str, object]:
    created_at = now_iso()
    run_id = sha256_hex(contract.intent + created_at)
    outcome = {"status": "ok", "surface": "simulator"}
    telemetry = {
        "command": "sim_run",
        "contract_id": contract.contract_id or sha256_hex(contract.intent + created_at),
        "effector": "simulator",
    }
    attestation = sha256_hex(json.dumps({"run_id": run_id, **outcome, **telemetry}, ensure_ascii=True, sort_keys=True))
    record = {
        "run_id": run_id,
        "contract_id": telemetry["contract_id"],
        "outcome": outcome,
        "telemetry": telemetry,
        "attestation_hash": attestation,
        "created_at": created_at,
    }
    append_run(record)
    return {
        "ok": True,
        "run": RunResult(run_id=run_id, contract_id=record["contract_id"], outcome=outcome, telemetry=telemetry, attestation_hash=attestation, created_at=created_at).model_dump(),
    }


@router.get("/sim/status")
async def sim_status() -> dict[str, object]:
    latest = None
    if RUNTIME_FILE.exists():
        lines = RUNTIME_FILE.read_text(encoding="utf-8").splitlines()
        if lines:
            latest = json.loads(lines[-1])
    return {"ok": True, "latest": latest}
