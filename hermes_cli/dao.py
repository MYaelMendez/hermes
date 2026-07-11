"""DAO command surface for glocal governance status and operations."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DAO_ROOT = Path(__file__).resolve().parent.parent / "dao"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _dao_paths() -> dict[str, Path]:
    return {
        "charter": DAO_ROOT / "charter.md",
        "members": DAO_ROOT / "members.json",
        "treasury": DAO_ROOT / "treasury" / "ledger.json",
        "proposals": DAO_ROOT / "governance" / "proposals.json",
    }


def _load_members() -> dict[str, Any]:
    path = _dao_paths()["members"]
    if not path.exists():
        return {"schema_version": 1, "surface": "æ://private client^glocal", "members": []}
    return _read_json(path)


def _load_treasury() -> dict[str, Any]:
    path = _dao_paths()["treasury"]
    if not path.exists():
        return {"schema_version": 1, "currency": "artifact-credits", "entries": []}
    return _read_json(path)


def _load_proposals() -> dict[str, Any]:
    path = _dao_paths()["proposals"]
    if not path.exists():
        return {"schema_version": 1, "proposals": []}
    return _read_json(path)


def _status() -> int:
    paths = _dao_paths()
    charter = paths["charter"]
    members = paths["members"]
    treasury = paths["treasury"]
    proposals = paths["proposals"]

    missing = [str(p) for p in [charter, members, treasury, proposals] if not p.exists()]
    if missing:
        print("DAO status failed: missing required dao files")
        for item in missing:
            print(f"  - {item}")
        return 1

    members_payload = _read_json(members)
    treasury_payload = _read_json(treasury)
    proposals_payload = _read_json(proposals)

    member_count = len(members_payload.get("members", []))
    treasury_entries = len(treasury_payload.get("entries", []))
    proposal_entries = proposals_payload.get("proposals", [])
    open_proposals = [p for p in proposal_entries if str(p.get("status", "draft")) in {"draft", "review"}]

    print("Hermes DAO Status")
    print(f"Root: {DAO_ROOT}")
    print(f"Charter: {charter}")
    print(f"Surface: {members_payload.get('surface', 'unknown')}")
    print(f"Members: {member_count}")
    print(f"Treasury entries: {treasury_entries}")
    print(f"Open proposals: {len(open_proposals)}")
    return 0


def _propose(args) -> int:
    payload = _load_proposals()
    proposals = payload.setdefault("proposals", [])
    proposal_id = f"P-{len(proposals) + 1:04d}"

    proposal = {
        "proposal_id": proposal_id,
        "title": args.title,
        "description": args.description,
        "proposer": args.proposer,
        "status": "draft",
        "votes": [],
        "created_at_utc": _now_utc(),
    }
    proposals.append(proposal)
    _write_json(_dao_paths()["proposals"], payload)

    print("DAO proposal created.")
    print(f"Proposal ID: {proposal_id}")
    print(f"Title: {args.title}")
    return 0


def _vote(args) -> int:
    payload = _load_proposals()
    proposals = payload.get("proposals", [])
    proposal = next((p for p in proposals if str(p.get("proposal_id")) == args.proposal_id), None)
    if not proposal:
        print(f"Proposal not found: {args.proposal_id}")
        return 1

    votes = proposal.setdefault("votes", [])
    existing = next((v for v in votes if str(v.get("member_id")) == args.member_id), None)
    vote_record = {
        "member_id": args.member_id,
        "vote": args.vote,
        "reason": args.reason,
        "voted_at_utc": _now_utc(),
    }
    if existing is not None:
        votes[votes.index(existing)] = vote_record
    else:
        votes.append(vote_record)

    if str(proposal.get("status", "draft")) == "draft":
        proposal["status"] = "review"

    _write_json(_dao_paths()["proposals"], payload)
    print("DAO vote recorded.")
    print(f"Proposal ID: {args.proposal_id}")
    print(f"Member: {args.member_id}")
    print(f"Vote: {args.vote}")
    return 0


def _close(args) -> int:
    payload = _load_proposals()
    proposals = payload.get("proposals", [])
    proposal = next((p for p in proposals if str(p.get("proposal_id")) == args.proposal_id), None)
    if not proposal:
        print(f"Proposal not found: {args.proposal_id}")
        return 1

    votes = proposal.get("votes", [])
    yes_votes = sum(1 for v in votes if str(v.get("vote")) == "yes")
    no_votes = sum(1 for v in votes if str(v.get("vote")) == "no")

    if args.result == "auto":
        final = "accepted" if yes_votes > no_votes else "rejected"
    elif args.result == "accepted":
        final = "accepted"
    else:
        final = "rejected"

    proposal["status"] = final
    proposal["closed_at_utc"] = _now_utc()
    proposal["close_reason"] = args.reason
    proposal["vote_summary"] = {"yes": yes_votes, "no": no_votes, "abstain": sum(1 for v in votes if str(v.get("vote")) == "abstain")}

    _write_json(_dao_paths()["proposals"], payload)
    print("DAO proposal closed.")
    print(f"Proposal ID: {args.proposal_id}")
    print(f"Result: {final}")
    return 0


def _treasury_balance() -> int:
    payload = _load_treasury()
    entries = payload.get("entries", [])
    balance = 0.0
    for item in entries:
        amount = float(item.get("amount", 0))
        entry_type = str(item.get("type", "credit"))
        balance += amount if entry_type == "credit" else -amount

    print("DAO Treasury Balance")
    print(f"Currency: {payload.get('currency', 'artifact-credits')}")
    print(f"Entries: {len(entries)}")
    print(f"Balance: {balance:.2f}")
    return 0


def _treasury_entry(args) -> int:
    payload = _load_treasury()
    entries = payload.setdefault("entries", [])
    entry_id = f"T-{len(entries) + 1:04d}"

    entries.append(
        {
            "entry_id": entry_id,
            "type": args.entry_type,
            "amount": float(args.amount),
            "note": args.note,
            "reference": args.reference,
            "created_at_utc": _now_utc(),
        }
    )
    _write_json(_dao_paths()["treasury"], payload)

    print("DAO treasury entry recorded.")
    print(f"Entry ID: {entry_id}")
    print(f"Type: {args.entry_type}")
    print(f"Amount: {float(args.amount):.2f}")
    return 0


def _member_add(args) -> int:
    payload = _load_members()
    members = payload.setdefault("members", [])
    existing = next((m for m in members if str(m.get("member_id")) == args.member_id), None)
    permissions = [p.strip() for p in str(args.permissions).split(",") if p.strip()]

    member_entry = {
        "member_id": args.member_id,
        "role": args.role,
        "permissions": permissions,
        "status": args.status,
    }

    if existing is not None:
        members[members.index(existing)] = member_entry
        action = "updated"
    else:
        members.append(member_entry)
        action = "added"

    _write_json(_dao_paths()["members"], payload)
    print(f"DAO member {action}.")
    print(f"Member ID: {args.member_id}")
    return 0


def _member_list() -> int:
    payload = _load_members()
    members = payload.get("members", [])
    print("DAO Members")
    print(f"Surface: {payload.get('surface', 'unknown')}")
    print(f"Count: {len(members)}")
    for member in members:
        member_id = str(member.get("member_id", ""))
        role = str(member.get("role", "member"))
        status = str(member.get("status", "active"))
        perms = ",".join(member.get("permissions", []))
        print(f"- {member_id} | role={role} | status={status} | permissions={perms}")
    return 0


def dao_command(args) -> None:
    action = getattr(args, "dao_action", None) or "status"
    if action == "status":
        raise SystemExit(_status())
    if action == "propose":
        raise SystemExit(_propose(args))
    if action == "vote":
        raise SystemExit(_vote(args))
    if action == "close":
        raise SystemExit(_close(args))
    if action == "treasury":
        treasury_action = getattr(args, "dao_treasury_action", None)
        if treasury_action == "balance":
            raise SystemExit(_treasury_balance())
        if treasury_action == "entry":
            raise SystemExit(_treasury_entry(args))
    if action == "member":
        member_action = getattr(args, "dao_member_action", None)
        if member_action == "add":
            raise SystemExit(_member_add(args))
        if member_action == "list":
            raise SystemExit(_member_list())

    print("Usage: hermes dao <status|propose|vote|close|treasury|member> ...")
    raise SystemExit(1)
