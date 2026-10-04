"""keeper_store — the on-disk memory substrate.

The laptop IS the memory. MEMORY.md is a 2,200-char cache injected into every
turn; that is the right shape for a handful of always-true facts and the wrong
shape for everything else. This module is the other half: an append-only ledger
under C:\\<ae>\\keeper that grows with the disk instead of the context window.

Design rules, learned the hard way in this repo:
  - Append-only JSONL. Never rewrite the whole file, never lose a prior fact.
  - Grep-able. A human can `rg` the ledger without this module.
  - Honest. A recall that finds nothing says so; it does not invent a hit.
  - Durable. Facts survive process death because they are on disk before the
    call returns.

Layout:
  C:\\<ae>\\keeper\\ledger.jsonl   append-only, one JSON object per line
  C:\\<ae>\\keeper\\index.md      human-readable rollup, regenerated on demand
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional

KEEPER_ROOT = os.path.join("C:\\", "æ", "keeper")
LEDGER = os.path.join(KEEPER_ROOT, "ledger.jsonl")
INDEX = os.path.join(KEEPER_ROOT, "index.md")

# Bump when the on-disk shape changes so old entries stay readable.
SCHEMA = 1


def _ensure() -> None:
    os.makedirs(KEEPER_ROOT, exist_ok=True)
    if not os.path.exists(LEDGER):
        # Create empty; do not seed with a fake entry.
        with open(LEDGER, "a", encoding="utf-8"):
            pass


def _read_all() -> List[Dict[str, Any]]:
    """Read every entry. A malformed line is skipped, not fatal — one bad write
    must never make the whole ledger unreadable."""
    _ensure()
    out: List[Dict[str, Any]] = []
    try:
        with open(LEDGER, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception:
                    continue
    except FileNotFoundError:
        pass
    return out


def remember(text: str, kind: str = "fact", tags: Optional[List[str]] = None,
             source: str = "keeper") -> Dict[str, Any]:
    """Append one fact. Returns the stored record. Writes to disk before
    returning, so the fact is durable even if the caller dies immediately."""
    text = (text or "").strip()
    if not text:
        return {"ok": False, "error": "empty fact refused"}
    _ensure()
    rec = {
        "schema": SCHEMA,
        "ts": int(time.time()),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "kind": kind,
        "tags": list(tags or []),
        "source": source,
        "text": text,
    }
    with open(LEDGER, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())      # durable before we return
    return {"ok": True, "stored": rec}


def recall(query: str, limit: int = 20, kind: Optional[str] = None) -> Dict[str, Any]:
    """Case-insensitive substring search over text+tags. Returns real matches or
    an explicit empty result — never a plausible-looking fabrication."""
    q = (query or "").strip().lower()
    hits = []
    for rec in _read_all():
        if kind and rec.get("kind") != kind:
            continue
        hay = (str(rec.get("text", "")) + " " + " ".join(rec.get("tags") or [])).lower()
        if not q or q in hay:
            hits.append(rec)
    hits.sort(key=lambda r: r.get("ts", 0), reverse=True)
    return {"ok": True, "query": query, "count": len(hits), "matches": hits[:limit]}


def stats() -> Dict[str, Any]:
    """Real counts from the file on disk."""
    recs = _read_all()
    kinds: Dict[str, int] = {}
    for r in recs:
        k = r.get("kind", "?")
        kinds[k] = kinds.get(k, 0) + 1
    size = os.path.getsize(LEDGER) if os.path.exists(LEDGER) else 0
    oldest = min((r.get("ts", 0) for r in recs), default=0)
    newest = max((r.get("ts", 0) for r in recs), default=0)
    return {
        "ok": True,
        "ledger": LEDGER,
        "entries": len(recs),
        "bytes": size,
        "kinds": kinds,
        "oldest": oldest,
        "newest": newest,
        "schema": SCHEMA,
    }


def write_index() -> Dict[str, Any]:
    """Regenerate the human-readable rollup. Grouped by kind, newest first."""
    recs = _read_all()
    by_kind: Dict[str, List[Dict[str, Any]]] = {}
    for r in recs:
        by_kind.setdefault(r.get("kind", "?"), []).append(r)

    lines = [
        "# keeper ledger",
        "",
        f"entries: {len(recs)}  ·  bytes: {os.path.getsize(LEDGER) if os.path.exists(LEDGER) else 0}",
        f"schema: {SCHEMA}  ·  file: `{LEDGER}`",
        "",
        "Append-only. The source of truth is `ledger.jsonl`; this file is a view.",
        "",
    ]
    for kind in sorted(by_kind):
        rows = sorted(by_kind[kind], key=lambda r: r.get("ts", 0), reverse=True)
        lines.append(f"## {kind} ({len(rows)})")
        lines.append("")
        for r in rows:
            tag = (" `" + "` `".join(r.get("tags") or []) + "`") if r.get("tags") else ""
            lines.append(f"- **{r.get('iso','?')}** — {r.get('text','')}{tag}")
        lines.append("")

    os.makedirs(KEEPER_ROOT, exist_ok=True)
    with open(INDEX, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))
    return {"ok": True, "index": INDEX, "entries": len(recs)}
