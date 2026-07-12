"""ingest_github_pages.py — aggregate our github.io dev surfaces into meta_memory.

github.io is the POINT-OF-TRUTH surface for our sovereign development. This
script reads the canonical surface rollup (surfaces.json, mirroring aggregate.html),
probes each URL for liveness, and writes an `aggregate` delta into
C:\ae\meta_memory.csv so the neuromitosis agentic cortex INGESTS its own
published development.

The loop:
  github.io (aggregate of all dev) -> probed -> meta_memory.csv (cortex trace)
  -> Hæbbian:// + neuromitosis.com render it.

The published surface becomes a LIVING INPUT to the cortex, not a static mirror.

Usage:  python ingest_github_pages.py [--dry-run]
"""
from __future__ import annotations
import argparse
import csv
import io
import json
import sys
import time
import urllib.request

META_CSV = r"C:\ae\meta_memory.csv"
# canonical rollup — mirrors aggregate.html SURFACES; github.io is the truth source
SURFACES = [
    ["æ:// homebase", "https://myaelmendez.github.io/", "unified mesh hub"],
    ["mesh-agenti", "https://myaelmendez.github.io/mesh-agenti.html", "pair two sovereign nodes via QR"],
    ["fleet", "https://myaelmendez.github.io/fleet.html", "MoD×MoA×MoM device mixture"],
    ["cuda-vlc", "https://myaelmendez.github.io/cuda-vlc.html", "sovereign CUDA→NVENC→VLC stream"],
    ["secret-bridge", "https://myaelmendez.github.io/secret-source-bridge.html", "local secret manager (vault node)"],
    ["sovereign-state", "https://myaelmendez.github.io/sovereign-state.html", "memory + ledger + #250 spine"],
    ["#startabusiness", "https://myaelmendez.github.io/agentic.html", "DAOLLC bootstrap + Doola"],
    ["glocal-secrets", "https://myaelmendez.github.io/glocal-secrets-blueprint.html", "surface github.io · custody Victus"],
    ["glocal-cuda", "https://myaelmendez.github.io/glocal-cuda-blueprint.html", "MoD blueprint: brain/droplet·hands/RTX"],
    ["glocal-mesh", "https://myaelmendez.github.io/glocal-mesh.html", "each primitive -> capability subagent"],
    ["rails", "https://myaelmendez.github.io/rails.html", "Doola affiliate (paid, zero custody)"],
    ["neuromitosis", "https://myaelmendez.github.io/neuromitosis.html", "operational substrate of distributed cognition"],
]


def _probe(url: str) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "neuromitosis-cortex/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print(f"[ingest] probing {len(SURFACES)} github.io dev surfaces (truth-source rollup)")
    rows = []
    live = 0
    for label, url, desc in SURFACES:
        ok = _probe(url)
        live += int(ok)
        status = "LIVE" if ok else "DOWN"
        print(f"  [{status}] {label:18} {url}")
        rows.append(("aggregate", f"{label} -> {url} [{status}] : {desc}"))

    if args.dry_run:
        print(f"[ingest] dry-run: {len(rows)} aggregate rows (not written)")
        return 0

    # canonical format matches meta_memory.bæsic:  epoch|key|value  (pipe-delimited)
    with open(META_CSV, "a", encoding="utf-8") as fh:
        for key, value in rows:
            fh.write(f"{int(time.time())}|{key}|{value}\n")
    print(f"[ingest] wrote {len(rows)} aggregate rows ({live} live) -> {META_CSV}")
    print("[ingest] cortex now ingests its own github.io development. Hæbbian:// reflects it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
