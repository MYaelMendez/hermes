"""github_pds.py — GitHub-enabled ATProto PDS for the neuromitosis agentic cortex.

The cortex (C:\\ae\\cortex.db + meta_memory.csv) is the MST *origin*. This adapter
turns it into an ATProto-style **repo** whose content-addressed records live in a
GitHub repo — so github.com IS the PDS store (a content-addressable mesh node).

Design (KISS, stdlib-only + gh):
  - Each cortex record -> repo/<collection>/<rkey>.json, content-addressed by CID
    (sha256 of canonical JSON, CIDv1-dag-json style prefix).
  - repo/HEAD.json = lightweight MST root: { did, collections, root_cid, entries:[cid,rkey, collection], sig }.
  - Signing: ed25519 key from C:\\ae\\secrets\\neuromitosis-cortex.pem if present,
    else HMAC stand-in (per vps_node discipline; swap for @atproto/crypto).
  - Push: git commit + `gh` push to the GitHub repo  -> github.com becomes the PDS.
  - Pull: fetch upstream -> merge new rkeys  -> mesh convergence across cortex nodes.
  - did.json: published to the github.io truth surface (point-of-truth).

Usage:
  python github_pds.py push     # build MST repo from cortex.db + push to GitHub
  python github_pds.py pull     # converge from GitHub (mesh)
  python github_pds.py did      # emit did.json to github.io truth surface
  python github_pds.py status   # local repo summary

Custody: signing key stays on Victus. Only public DID doc + signed records cross.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import subprocess
import sys
import time
import urllib.request
from typing import Any

# --- config ---
CORTEX_DB = "C:\\ae\\cortex.db"
SECRET_DIR = "C:\\ae\\secrets"
DID = "did:web:neuromitosis.com:cortex"
GITHUB_REPO = os.environ.get("CORTEX_REPO", "MYaelMendez/neuromitosis-cortex")
GITHUB_PAGES_REPO = os.environ.get("GITHUB_PAGES_REPO", "MYaelMendez/myaelmendez.github.io")
REPO_LOCAL = os.environ.get("CORTEX_REPO_LOCAL", "C:\\ae\\cortex-pds")
COLLECTIONS = {
    "codemode": "ae.core",
    "cortex_axiom": "ae.core",
    "distributed_cognition": "ae.core",
    "cuda_IDE_RTX": "ae.core",
    "deploy": "ae.core",
    "aggregate": "ae.mesh",
    "skill_evolution": "ae.mission",
}


def _cid(payload: str) -> str:
    """CIDv1-dag-json-ish: base32(0x01 0x71 <sha256>). Sovereign-scoped, content-addressed."""
    h = hashlib.sha256(payload.encode("utf-8")).digest()
    raw = b"\x01\x71" + h  # cidv1, codec dag-json (0x71)
    return "b" + base64.b32encode(raw).decode("ascii").lower().rstrip("=")


def _sign(msg: bytes) -> str:
    """Sign msg. ed25519 if key present, else HMAC stand-in (vps_node discipline)."""
    key_path = os.path.join(SECRET_DIR, "neuromitosis-cortex.pem")
    if os.path.exists(key_path):
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            from cryptography.hazmat.primitives import serialization
            k = serialization.load_pem_private_key(open(key_path, "rb").read(), password=None)
            return "ed25519:" + base64.b64encode(k.sign(msg)).decode("ascii")
        except Exception:
            pass
    # stand-in
    h = hmac.new(b"victus-cortex-standin", msg, hashlib.sha256).digest()
    return "hmac:" + base64.b64encode(h).decode("ascii")


def _run_gh(args: list[str], inp: str | None = None) -> str:
    cmd = ["gh"] + args
    p = subprocess.run(cmd, input=inp, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"gh {args[0]} failed: {p.stderr.strip()}")
    return p.stdout


def _gh_api(method: str, path: str, body: dict | None = None) -> dict:
    args = ["api", f"-X{method}", path]
    if body is not None:
        for k, v in body.items():
            args += ["-f", f"{k}={v}"]
    out = _run_gh(args)
    return json.loads(out) if out.strip() else {}


def ensure_repo() -> None:
    """Create the GitHub repo if absent (private: records are meta-memory)."""
    try:
        _gh_api("GET", f"/repos/{GITHUB_REPO}")
    except RuntimeError:
        print(f"[pds] creating {GITHUB_REPO} (private)")
        _gh_api("POST", "/user/repos", {"name": GITHUB_REPO.split("/")[-1], "private": True,
                                         "description": "Neuromitosis agentic cortex — GitHub-enabled ATProto PDS (sovereign mesh node)"})
    # local clone / init
    if not os.path.isdir(REPO_LOCAL):
        try:
            subprocess.run(["git", "clone", f"https://github.com/{GITHUB_REPO}.git", REPO_LOCAL],
                           check=True, capture_output=True)
        except subprocess.CalledProcessError:
            os.makedirs(REPO_LOCAL, exist_ok=True)
            subprocess.run(["git", "-C", REPO_LOCAL, "init"], check=True)
            subprocess.run(["git", "-C", REPO_LOCAL, "remote", "add", "origin",
                            f"https://github.com/{GITHUB_REPO}.git"], check=True)


def build_repo() -> dict:
    """Build the MST repo from cortex.db into REPO_LOCAL/repo/."""
    from cortex_store import CortexStore
    s = CortexStore()
    repo_dir = os.path.join(REPO_LOCAL, "repo")
    os.makedirs(repo_dir, exist_ok=True)
    entries = []
    for row in s.all_rows():
        parts = row.split("|", 2)
        if len(parts) < 3:
            continue
        epoch, key, value = parts
        coll = COLLECTIONS.get(key, "ae.core")
        payload = json.dumps({"epoch": epoch, "key": key, "value": value},
                              ensure_ascii=False, sort_keys=True)
        cid = _cid(payload)
        rkey = hashlib.sha256(f"{key}:{epoch}".encode()).hexdigest()[:13]
        cdir = os.path.join(repo_dir, coll)
        os.makedirs(cdir, exist_ok=True)
        with open(os.path.join(cdir, f"{rkey}.json"), "w", encoding="utf-8") as fh:
            fh.write(payload)
        entries.append({"cid": cid, "rkey": rkey, "collection": coll, "key": key})
    # MST root (lightweight): sorted by cid, signed
    entries.sort(key=lambda e: e["cid"])
    root = {"did": DID, "collections": sorted(set(e["collection"] for e in entries)),
            "count": len(entries), "built": int(time.time()), "entries": entries}
    root_json = json.dumps(root, ensure_ascii=False, sort_keys=True)
    root["sig"] = _sign(root_json.encode("utf-8"))
    with open(os.path.join(repo_dir, "HEAD.json"), "w", encoding="utf-8") as fh:
        json.dump(root, fh, ensure_ascii=False, indent=2)
    return root


def push() -> None:
    ensure_repo()
    root = build_repo()
    os.chdir(REPO_LOCAL)
    subprocess.run(["git", "add", "-A"], check=True)
    # commit only if changed
    st = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if not st.stdout.strip():
        print("[pds] nothing to push (already converged)")
        return
    subprocess.run(["git", "commit", "-q", "-m", f"cortex MST: {root['count']} records @ {root['built']}"], check=True)
    subprocess.run(["git", "push", "-q", "origin", "HEAD"], check=True)
    print(f"[pds] pushed {root['count']} records -> github.com/{GITHUB_REPO} (cid-root {root['entries'][0]['cid'][:12]}…)")


def pull() -> None:
    """Mesh convergence: fetch upstream, merge new rkeys into local cortex."""
    ensure_repo()
    os.chdir(REPO_LOCAL)
    subprocess.run(["git", "pull", "-q", "origin", "HEAD"], check=True)
    head = json.load(open(os.path.join(REPO_LOCAL, "repo", "HEAD.json"), encoding="utf-8"))
    from cortex_store import CortexStore
    s = CortexStore()
    local_keys = {(r.split("|")[1], r.split("|")[0]) for r in s.all_rows()}
    merged = 0
    for e in head["entries"]:
        f = os.path.join(REPO_LOCAL, "repo", e["collection"], f"{e['rkey']}.json")
        rec = json.load(open(f, encoding="utf-8"))
        if (rec["key"], rec["epoch"]) not in local_keys:
            s.append(int(rec["epoch"]), rec["key"], rec["value"])
            merged += 1
    print(f"[pds] pulled {head['count']} records, merged {merged} new into local cortex")


def emit_did() -> None:
    """Publish did.json to the github.io truth surface (point-of-truth)."""
    public_key = "zSTANDIN_REPLACE_WITH_VICTUS_ED25519_MULTIBASE"
    key_path = os.path.join(SECRET_DIR, "neuromitosis-cortex.pem")
    if os.path.exists(key_path):
        try:
            from cryptography.hazmat.primitives import serialization
            pub = serialization.load_pem_private_key(open(key_path, "rb").read(), password=None).public_key()
            raw = pub.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
            public_key = "z" + base64.b58encode(raw).decode("ascii")
        except Exception:
            pass
    services = [
        {"id": "#atproto_pds", "type": "AtprotoPds", "serviceEndpoint": "https://github.com/" + GITHUB_REPO},
        {"id": "#github_pds", "type": "ContentAddressedStore", "serviceEndpoint": "https://github.com/" + GITHUB_REPO + "/tree/main/repo"},
        {"id": "#cortex_trace", "type": "CortexStore", "serviceEndpoint": CORTEX_DB,
         "description": "Local-first SQLite meta-memory trace (Victus custody). Origin of MST records."},
        {"id": "#ae_homebase", "type": "AeHomebase", "serviceEndpoint": "https://neuromitosis.com"},
        {"id": "#github_io_truth", "type": "PointOfTruth", "serviceEndpoint": "https://myaelmendez.github.io"},
    ]
    doc = {
        "@context": ["https://www.w3.org/ns/did/v1"],
        "id": DID,
        "alsoKnownAs": ["at://neuromitosis.com", "ae://neuromitosis.cortex"],
        "verificationMethod": [{
            "id": "#cortex-key", "type": "Ed25519VerificationKey2020",
            "controller": DID, "publicKeyMultibase": public_key}],
        "assertionMethod": ["#cortex-key"],
        "authentication": ["#cortex-key"],
        "service": services,
        "remark": "Sovereign anchor for the neuromitosis agentic cortex. GitHub-enabled ATProto PDS: content-addressed repo on github.com (mesh node). Signing key custodied on Victus; only public key + signed records cross. #hermiphicationisinevitable",
    }
    # write to github.io pages repo (truth surface, point-of-truth)
    pages = os.path.join("C:\\æ\\github-pages", "cortex", "did.json")
    os.makedirs(os.path.dirname(pages), exist_ok=True)
    with open(pages, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)
    print(f"[pds] did.json -> {pages} (truth surface; push github-pages to publish)")


def main() -> int:
    ap = argparse.ArgumentParser(description="GitHub-enabled ATProto PDS for the neuromitosis cortex")
    ap.add_argument("cmd", choices=["push", "pull", "did", "status"])
    args = ap.parse_args()
    if args.cmd == "push":
        push()
    elif args.cmd == "pull":
        pull()
    elif args.cmd == "did":
        emit_did()
    elif args.cmd == "status":
        from cortex_store import CortexStore
        s = CortexStore()
        print(f"[pds] cortex records: {s.count()}; repo target: github.com/{GITHUB_REPO}; did: {DID}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
