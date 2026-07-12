"""sync_to_droplet.py — synchronize our local dev corpus to the DO droplet PDS.

The droplet (aevps) is the MCP² broker / sovereign-state PDS at
http://129.212.180.252:3000. It exposes POST /xrpc/ae.vps.record which writes a
signed ae.core record. We push:
  - ae.core#sovereignState  : the SYNC manifest (counts, generated, pointer)
  - ae.core#blueprint       : each of our 23 blueprints (title+path+body)
  - ae.core#skillIndex      : the skills/strategies index (paths+titles)

Usage:  python sync_to_droplet.py [--dry-run] [--host 129.212.180.252 --port 3000]
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import urllib.request

DROP_HOST = os.environ.get("VPS_HOST", "129.212.180.252")
DROP_PORT = os.environ.get("VPS_PORT", "3000")
args_host = DROP_HOST
args_port = DROP_PORT


def _post_record(nsid: str, value: dict) -> dict:
    base = f"http://{args_host}:{args_port}"
    payload = json.dumps({"nsid": nsid, "value": value}).encode()
    req = urllib.request.Request(
        f"{base}/xrpc/ae.vps.record", data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")[:300]
        raise RuntimeError(f"record {nsid} -> HTTP {e.code}: {body}") from None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--host", default=DROP_HOST)
    ap.add_argument("--port", default=DROP_PORT)
    args = ap.parse_args()
    global args_host, args_port
    args_host, args_port = args.host, args.port

    idx = json.load(open("SYNC_INDEX.json", encoding="utf-8"))
    counts = idx["counts"]
    total = idx["total"]

    # 1) sovereignState manifest
    manifest = {
        "kind": "sync_manifest",
        "generated": idx["generated"],
        "source": idx["source"],
        "counts": counts,
        "total": total,
        "note": "neuromitosis.com bonded node -> droplet PDS sync. MoD topology. No secrets.",
        "children": ["ae.core#blueprint", "ae.core#skillIndex"],
    }
    print(f"[manifest] ae.core#sovereignState  total={total} counts={counts}")
    if not args.dry_run:
        print("   ->", _post_record("ae.core#sovereignState", manifest).get("sig", "?")[:24], "...")

    # 2) blueprints -> ae.core#ledgerEvent (each blueprint is a logged sovereign artifact)
    bp = [e for e in idx["entries"] if e["cat"] == "blueprint"]
    for e in bp:
        path = e["path"]
        try:
            body = open(path, encoding="utf-8", errors="ignore").read()
        except Exception as exc:
            body = f"(unreadable: {exc})"
        rec = {"title": e["title"], "path": path, "size": e["size"], "body": body}
        print(f"[blueprint] {e['title'][:48]:48} ({e['size']}b) -> ledgerEvent")
        if not args.dry_run:
            _post_record("ae.core#ledgerEvent", rec)

    # 3) skillIndex -> ae.core#meshPeer (skills/strategies are mesh peers)
    skills = [{"path": e["path"], "title": e["title"], "size": e["size"]}
              for e in idx["entries"] if e["cat"] in ("skill", "doc", "manifest", "other")]
    skill_idx = {"count": len(skills), "entries": skills}
    print(f"[skillIndex] ae.core#meshPeer  count={len(skills)}")
    if not args.dry_run:
        _post_record("ae.core#meshPeer", skill_idx)

    print("sync complete." if not args.dry_run else "dry-run complete (no records written).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
