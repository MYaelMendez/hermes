"""gen_neuromitosis.py — bake the live neuromitosis.com site into a static snapshot.

Pulls the real wiring + mesh from the chassis bridge (or falls back to inline
defaults) and writes neuromitosis.static.html — a self-contained file with the
data baked in, so it deploys to the real neuromitosis.com DNS with no live
server. Co-webmastering stays live (serve_neuromitosis.py); this is the frozen
artifact for production.

Usage:  python gen_neuromitosis.py [--out neuromitosis.static.html] [--bridge http://127.0.0.1:8093]
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "neuromitosis.com.html")


def _fetch(url: str, timeout: int = 4):
    try:
        return json.loads(urllib.request.urlopen(url, timeout=timeout).read())
    except Exception:
        return None


def _wiring_js(wiring: dict | None) -> str:
    if not wiring:
        return json.dumps({
            "ok": True, "skill": "agentic-chassis-surface", "memory_triggers": 9,
            "reset_ready": True, "wired_surfaces": [
                {"scheme": "file://", "detail": "sovereign-scoped read, count>mutate"},
                {"scheme": "computer://", "detail": "agentic computer on Victus GPU-MCP"},
                {"scheme": "desktop://", "detail": "hermes-agent native -> WindowsDesktop"},
                {"scheme": "+bæsic://", "detail": "qc64 ledger: counts/graphs in-language"},
                {"scheme": "æ://", "detail": "agentic-language-chassis router"},
            ],
        })
    return json.dumps(wiring)


def _mesh_js(mesh: dict | None) -> str:
    if not mesh:
        return json.dumps({"ok": True, "topology": "MoD", "nodes": [
            {"domain": "cli.llc", "role": "Build — agentic infrastructure.", "bonded": False},
            {"domain": "daollc.ai", "role": "Entity — sovereign DAO LLC.", "bonded": False},
            {"domain": "llm.store", "role": "Intelligence — æπ combinator.", "bonded": False},
            {"domain": "æ.store", "role": "Commerce — agentic email, IOA.", "bonded": False},
            {"domain": "æl.net", "role": "Arrival — entry to the topology.", "bonded": False},
            {"domain": "neuromitosis.com", "role": "Bond — Human+Robot+DAO wired.", "bonded": True},
        ]})
    return json.dumps(mesh)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "neuromitosis.static.html"))
    ap.add_argument("--bridge", default="http://127.0.0.1:8093")
    args = ap.parse_args()

    wiring = _fetch(f"{args.bridge}/wiring.json")
    mesh = _fetch(f"{args.bridge}/mesh.json")
    if wiring:
        print(f"baked live wiring: {len(wiring.get('wired_surfaces', []))} synapses")
    else:
        print("bridge offline — baking inline default wiring")
    if mesh:
        print(f"baked live mesh: {len(mesh.get('nodes', []))} nodes")
    else:
        print("bridge offline — baking inline default mesh")

    with open(SRC, "r", encoding="utf-8") as fh:
        html = fh.read()

    # inject the baked data so loadWiring/loadMesh don't need the bridge
    inject = (
        f"const __WIRING__ = {_wiring_js(wiring)};\n"
        f"const __MESH__ = {_mesh_js(mesh)};\n"
        "if (typeof __WIRING__ !== 'undefined') { /* baked */ }\n"
    )
    # replace the live fetch calls with baked data
    html = html.replace(
        'const res = await fetch("/wiring.json");\n      if (!res.ok) throw new Error("bridge " + res.status);\n      const data = await res.json();',
        'const data = __WIRING__;',
    )
    html = html.replace(
        'const res = await fetch("/mesh.json");\n      if (!res.ok) throw new Error("mesh " + res.status);\n      const data = await res.json();',
        'const data = __MESH__;',
    )
    # the /compose console still needs a live bridge; keep it, but note it
    html = html.replace("</script>", inject + "</script>", 1)

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"wrote {args.out} ({os.path.getsize(args.out)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
