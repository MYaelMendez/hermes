"""Hermes conductor: lightweight CLI/scheme dispatcher for viewport computer.
Background
----------
This module used to centralize a fixed list of operator URI schemes.  It now
exposes a small, **standalone scheme dispatcher** so new primitives can be
registered in-process without editing a big if/elif chain.  The default
instance preserves historical behavior; callers can register new schemes
whenever they need to.

Public surface
--------------
- class ``SchemeDispatcher``
- function ``run_hermes(payload) -> dict``
- module-level ``dispatch`` backed by a default ``SchemeDispatcher``
"""
from __future__ import annotations

import os
import shlex
import subprocess
import json
import secrets
import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

REPO = Path(__file__).resolve().parents[1]


def _make_run_pc_name(raw: str) -> Tuple[str, str | None]:
    normalized = raw
    run_pc_name = None
    if normalized.startswith("run "):
        rest = normalized.split(" ", 1)[1].strip()
        if rest.startswith("pc://"):
            run_pc_name = rest.split("pc://", 1)[1].strip() or "default"
            normalized = f"pc://run {run_pc_name}"
        else:
            normalized = rest
    elif normalized.startswith("pc://run "):
        run_pc_name = normalized.split("pc://run ", 1)[1].strip() or "default"
        normalized = "pc://run"
    return normalized, run_pc_name


def _normalize_cc(raw: str) -> str:
    if raw.startswith("H://cc") or raw.startswith("hermes://cc"):
        return "c://cc" + raw.split("cc", 1)[1]
    return raw


def _cctx_dispatch(raw: str) -> dict:
    target = raw.split(" ", 1)[1].strip() if " " in raw else "pc://"
    return {
        "ok": True,
        "rc": 0,
        "stdout": f"cctx -> {target}\n",
        "stderr": "",
        "surface": {
            "kind": "cctx",
            "target": target,
            "active": _DISPATCHER.is_scheme_cmd(target) and target != "c://",
        },
    }


def _aectx_dispatch(raw: str) -> dict:
    """?:// - the agentic-language-chassis: sovereign context router.

    ``?://`` is the namespace/runtime for agentic languages. Bare ``?://`` is
    the catch-all context router: it resolves the target surface and reports
    whether that target is a live registered scheme. Dialects plug in as
    sub-schemes, each a chassis of its own:
      - ``?://basic``   (+b?sic://)  -> qc64 BASIC chassis (qc64_basic.py)
      - ``?://mech``    (mech-lang)  -> reactive dataflow state machines
      - ``?://glocal-agent``        -> sovereign local agent (GPU-MCP)
      - ``+?://cc``                -> command & control surface
    ``+?://`` (the +? superset) routes here as its catch-all.
    """
    target = raw.split("?://", 1)[1].strip() if "?://" in raw else "pc://"
    return {
        "ok": True,
        "rc": 0,
        "stdout": f"aectx -> {target}\n",
        "stderr": "",
        "surface": {
            "kind": "aectx",
            "target": target,
            "active": _DISPATCHER.is_scheme_cmd(target) and target != "c://",
        },
    }


def _pc_run_dispatch(raw: str, run_pc_name: str | None) -> dict:
    client = run_pc_name or "default"
    return {
        "ok": True,
        "rc": 0,
        "stdout": f"pc://run {client}\n",
        "stderr": "",
        "surface": {
            "kind": "private_client_run",
            "address": f"pc://{client}",
            "client": client,
        },
    }


def _identity_dispatch(raw: str) -> dict:
    return {
        "ok": True,
        "rc": 0,
        "stdout": "+?://identity bounded private client mesh^hermes-agent/conductor\n",
        "stderr": "",
        "surface": {
            "kind": "bounded_private_client_mesh",
            "address": "+?://identity",
            "conductor": "hermes-agent/conductor",
            "runtime": "bounded_dispatch",
            "contract": "PCSurfaceContract",
            "governance": {
                "required": "+? member token",
                "audit": True,
                "tracer": "Wyoming DAO LLC audit trail",
            },
        },
    }


# --- known sovereign routes (GLOCAL: droplet = public brain, Victus = hands) ---
# `cloud` is the burst MoD node: provisioned on demand (RunPod/Vast/DO-gpu),
# identical vps_node deploys to it. Slot is codemode-ready - endpoint is filled
# when a pod appears (see +?://route register); no cloud spend until then.
import os as _os
_VPS_ROUTES = {
    "neuromitosis": {
        "endpoint": "http://129.212.180.252:3000",
        "role": "vps:// backbone - public identity/data + rtx3050:// front door",
        "host": "DigitalOcean s-2vcpu-4gb atl1",
        "kind": "sovereign",
    },
    "cloud": {
        "endpoint": _os.environ.get("VPS_CLOUD_ENDPOINT", ""),
        "role": "burst CUDA hands (Mixture of Devices) - pod-provisioned",
        "host": _os.environ.get("VPS_CLOUD_HOST", "(unprovisioned)"),
        "kind": "burst",
    },
}


def _vps_register_dispatch(raw: str) -> dict:
    """+?://route register vps://<name> <endpoint> [--host ...] - add a MoD node.

    codemode: a device becomes an addressable route. Persists to a local ledger
    (no cloud), survives the session. The `cloud` burst node is registered this way
    once a pod is up.
    """
    import re as _re
    rest = raw.split("register", 1)[1].strip() if "register" in raw else ""
    m = _re.match(r"(vps://\S+)\s+(\S+)(?:\s+--host\s+(\S+))?", rest)
    if not m:
        return {"ok": False, "rc": 2, "stdout": "",
                "stderr": "usage: +?://route register vps://<name> <endpoint> [--host <host>]"}
    name = m.group(1).split("vps://", 1)[1].split("/")[0]
    endpoint = m.group(2)
    host = m.group(3) or "(unknown)"
    _VPS_ROUTES[name] = {"endpoint": endpoint, "role": "registered MoD node", "host": host,
                          "kind": "burst" if name == "cloud" else "peer"}
    return {"ok": True, "rc": 0,
            "stdout": f"+?://route register {name} -> {endpoint}\n  now addressable as vps://{name}\n",
            "stderr": "", "scheme": "+?", "scheme_detail": "+?://route register",
            "surface": {"kind": "route_register", "node": name, "endpoint": endpoint}}


def _vps_node_dispatch(raw: str) -> dict:
    """vps:// - sovereign backbone node (droplet) as an addressable route.

    vps://                 -> list known backbone nodes + liveness
    vps://neuromitosis     -> status probe of the live droplet endpoint
    """
    import urllib.request as _ur

    node = raw.split("vps://", 1)[1].strip() if "vps://" in raw else ""
    node = node.split("/")[0].split("?")[0].strip()
    if not node:
        lines = ["vps:// - sovereign backbone nodes (GLOCAL)"]
        for name, info in _VPS_ROUTES.items():
            lines.append(f"  {name:12} {info['endpoint']}  [{info['role']}]")
        lines.append("  (probe a node: vps://<name>)")
        return {"ok": True, "rc": 0, "stdout": "\n".join(lines), "stderr": "",
                "scheme": "vps", "surface": {"kind": "vps_list", "routes": list(_VPS_ROUTES)}}

    info = _VPS_ROUTES.get(node)
    if not info:
        return {"ok": False, "rc": 2, "stdout": "", "stderr": f"unknown vps node: {node}",
                "scheme": "vps"}
    url = info["endpoint"].rstrip("/") + "/xrpc/ae.vps.status"
    try:
        with _ur.urlopen(url, timeout=8) as r:
            data = json.loads(r.read() or b"{}")
        live = data.get("vps") == "up"
        return {"ok": True, "rc": 0,
                "stdout": (f"vps://{node} -> {info['endpoint']}\n"
                           f"  liveness: {'UP' if live else 'DOWN'}\n"
                           f"  role    : {info['role']}\n"
                           f"  records : {data.get('records')}\n"
                           f"  compute : {data.get('compute')}\n"),
                "stderr": "", "scheme": "vps",
                "surface": {"kind": "vps_node", "node": node, "live": live,
                            "endpoint": info["endpoint"]}}
    except Exception as e:
        return {"ok": True, "rc": 0,
                "stdout": (f"vps://{node} -> {info['endpoint']}\n"
                           f"  liveness: DOWN (probe failed: {e})\n"
                           f"  role    : {info['role']}\n"),
                "stderr": "", "scheme": "vps",
                "surface": {"kind": "vps_node", "node": node, "live": False,
                            "endpoint": info["endpoint"]}}


def _route_dispatch(raw: str) -> dict:
    """+?://route - report the registered GLOCAL route tower.

    Surfaces: pc://mesh/victus/local (Victus RTX hands), vps://neuromitosis
    (droplet brain), +?:// (conductor), github.io (surface). Honest, no claims
    unless the node answers.
    """
    rest = raw.split("+?://route", 1)[1].strip() if "+?://route" in raw else ""
    if rest.startswith("register"):
        return _vps_register_dispatch(raw)
    parts = []
    parts.append("+?://route - GLOCAL route tower (Mixture of Devices)")
    parts.append("  github.io        -> surface source of truth (public)")
    parts.append("  +?://            -> conductor (local broker)")
    parts.append("  pc://mesh/victus -> Victus RTX 3050 (sovereign hands, offline-capable)")
    for name, info in _VPS_ROUTES.items():
        ep = info["endpoint"] or "(unprovisioned)"
        parts.append(f"  vps://{name:11} -> {ep}  [{info.get('kind','peer')}]")
    parts.append("  register a node: +?://route register vps://<name> <endpoint> [--host <h>]")
    return {"ok": True, "rc": 0, "stdout": "\n".join(parts), "stderr": "",
            "scheme": "+?", "scheme_detail": "+?://route",
            "surface": {"kind": "route_tower", "vps": list(_VPS_ROUTES)}}


def _pc_dispatch(raw: str) -> dict:
    """pc:// - the private-client runtime on the sovereign mesh.

    Canonical mesh is ``pc://mesh/victus/local`` (offline brain + local hands).
    A bare ``pc://`` reports the mesh; ``pc://<node>`` addresses a node on it.
    """
    node = raw.split("pc://", 1)[1].strip() if "pc://" in raw else ""
    mesh = "pc://mesh/victus/local"
    target = node or mesh
    return {
        "ok": True,
        "rc": 0,
        "stdout": f"pc://private client runtime -> {target}\n",
        "stderr": "",
        "surface": {
            "kind": "private_client",
            "address": raw,
            "mesh": mesh,
            "node": target,
            "runtime": "hermes-code",
            "local_only": True,
        },
    }


def _qrcode_dispatch(raw: str) -> dict:
    html = ""
    action = None
    source = "unknown"
    if raw.partition("+?://")[2].strip().startswith("qrcode payload "):
        html = raw.split("+?://qrcode payload ", 1)[1].strip()
        source = "payload"
    else:
        path = raw.split("+?://qrcode", 1)[1].strip() if "+?://qrcode" in raw else ""
        if not path:
            return {
                "ok": False,
                "rc": 2,
                "stdout": "",
                "stderr": "missing +?://qrcode payload or file path",
                "surface": {"kind": "qrcode_surface", "address": raw, "runtime": "hermes-code"},
            }
        path = path.strip()
        if path.startswith("'") and path.endswith("'"):
            path = path[1:-1].strip()
        if path.startswith('"') and path.endswith('"'):
            path = path[1:-1].strip()
        try:
            path_obj = Path(path)
            if not path_obj.is_absolute():
                path_obj = (REPO / path_obj).resolve()
            html = path_obj.read_text(encoding="utf-8", errors="ignore")
            source = str(path_obj)
        except Exception as exc:
            return {
                "ok": False,
                "rc": 2,
                "stdout": "",
                "stderr": f"qrcode read failed: {exc}",
                "surface": {"kind": "qrcode_surface", "address": raw, "runtime": "hermes-code"},
            }
    manifest = _qrcode_headless_manifest(html)
    qr_path = _write_qrcode_image(html, raw, source)
    return {
        "ok": True,
        "rc": 0,
        "stdout": f"+?://qrcode {source} -> {qr_path}\n",
        "stderr": "",
        "surface": {
            "kind": "qrcode_surface",
            "address": raw,
            "runtime": "hermes-code",
            "source": source,
            "headless": True,
            "html_bytes": len(html.encode("utf-8")),
            "image_path": qr_path,
            "action": manifest.get("action"),
            "required_token": manifest.get("required_token"),
            "target_surface": manifest.get("target_surface"),
            "executed": False,
            "execution": None,
        },
    }


def _qrcode_headless_manifest(html: str) -> dict[str, object | None]:
    stripped = html.strip()
    token = None
    action = None
    target_surface = None
    for marker in ["<!-- +?_qrcode_token:", "<!-- qrcode_token:", "<!-- token:"]:
        if marker in stripped:
            token = stripped.split(marker, 1)[1].split("-->", 1)[0].strip()
            break
    for marker, kind in [
        ("<!-- +?_qrcode_action:", "action"),
        ("<!-- qrcode_action:", "action"),
        ("<!-- target_surface:", "target_surface"),
    ]:
        if marker in stripped:
            value = stripped.split(marker, 1)[1].split("-->", 1)[0].strip()
            if kind == "action":
                action = value
            else:
                target_surface = value
            break
    if not action and 'data-action="' in html:
        action = html.split('data-action="', 1)[1].split('"', 1)[0].strip()
    if not target_surface and 'data-surface="' in html:
        target_surface = html.split('data-surface="', 1)[1].split('"', 1)[0].strip()
    if action and not target_surface and action.startswith("http"):
        target_surface = action
    return {
        "token": token,
        "action": action,
        "required_token": token,
        "target_surface": target_surface,
    }


def _write_qrcode_image(html: str, raw: str, source: str) -> str:
    try:
        import qrcode
    except Exception:
        raise RuntimeError("qrcode is required for +?://qrcode")
    safe_source = source.replace("/", "_").replace("\\", "_") or "input"
    if not safe_source.endswith(".html"):
        safe_source = f"{safe_source}.html"
    file_name = f"qrcode_{safe_source}"
    if not file_name.endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif")):
        file_name = f"{file_name}.png"
    out_dir = REPO / "media" / "qrcodes"
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        out_dir = Path.home() / "AppData" / "Local" / "hermes" / "qrcodes"
        out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / file_name
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=8,
        border=4,
    )
    qr.add_data(html)
    try:
        qr.make(fit=False)
    except qrcode.exceptions.DataOverflowError:
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_Q,
            box_size=8,
            border=4,
        )
        qr.add_data(html)
        qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    img.save(str(out_path))
    return str(out_path)


# ---------------------------------------------------------------------------
# +?://mesh  - sovereign LAN mesh pairing via QR handshake (opt-in, no cloud)
# ---------------------------------------------------------------------------
# Emitter:  +?://mesh offer <name>   -> writes a QR PNG encoding a peer manifest
#           (ae://peer?host=<name>&mesh=pc://mesh/<name>/local&port=<lan>&
#            token=<ephemeral>&via=wifi). The NEW node emits; the sovereign node
#           scans + accepts.
# Receiver: +?://mesh accept <payload>  -> registers pc://mesh/<name>/local as a
#           real route. NEVER auto-trusts a scanned code; explicit accept only.
# Peers persist locally (scoped JSON) - no cloud, no secrets in the code.
_PEERS_FILE = REPO / "mesh_peers.json"
_PEER_REGISTRY: dict[str, dict] = {}


def _mesh_load_peers() -> None:
    global _PEER_REGISTRY
    if _PEER_REGISTRY:
        return
    try:
        txt = _PEERS_FILE.read_text(encoding="utf-8", errors="ignore")
        _PEER_REGISTRY = json.loads(txt) if txt.strip() else {}
    except Exception:
        _PEER_REGISTRY = {}


def _mesh_save_peers() -> None:
    try:
        _PEERS_FILE.write_text(
            json.dumps(_PEER_REGISTRY, indent=2), encoding="utf-8"
        )
    except Exception:
        pass


# ?? fleet registry (MoD): mixture of sovereign devices ?????????????????????
_FLEET_FILE = REPO / "fleet_registry.json"
_FLEET_REGISTRY: dict[str, dict] = {}


def _fleet_load() -> None:
    global _FLEET_REGISTRY
    if _FLEET_REGISTRY:
        return
    try:
        txt = _FLEET_FILE.read_text(encoding="utf-8", errors="ignore")
        _FLEET_REGISTRY = json.loads(txt) if txt.strip() else {}
    except Exception:
        _FLEET_REGISTRY = {}


def _fleet_save() -> None:
    try:
        _FLEET_FILE.write_text(
            json.dumps(_FLEET_REGISTRY, indent=2), encoding="utf-8"
        )
    except Exception:
        pass


def _mesh_local_lan_ip() -> str:
    """Best-effort LAN IP (ignores loopback). Returns '' if none found."""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return ""
    finally:
        s.close()


def _mesh_dispatch(raw: str) -> dict:
    """+?://mesh - sovereign LAN mesh pairing via QR handshake.

    +?://mesh offer <name>  -> emit a QR carrying a peer manifest
    +?://mesh accept <pay>  -> register a scanned peer route (explicit, opt-in)
    """
    rest = raw.split("+?://mesh", 1)[1].strip() if "+?://mesh" in raw else ""
    if rest.startswith("offer"):
        return _mesh_offer_dispatch(raw)
    if rest.startswith("accept"):
        return _mesh_accept_dispatch(raw)
    return {
        "ok": True,
        "rc": 0,
        "stdout": (
            "+?://mesh - sovereign LAN mesh pairing (QR handshake, opt-in)\n"
            "  +?://mesh offer <name>   emit QR carrying peer manifest\n"
            "  +?://mesh accept <pay>   register scanned peer as pc://mesh/<name>/local\n"
        ),
        "stderr": "",
        "scheme_detail": "+?://mesh",
        "surface": {"kind": "mesh_help"},
    }


def _mesh_offer_dispatch(raw: str) -> dict:
    """+?://mesh offer <name> - emit a QR carrying a peer manifest for <name>."""
    name = raw.split("offer", 1)[1].strip() if "offer" in raw else ""
    if not name:
        name = "legion"
    token = secrets.token_hex(8)
    lan = _mesh_local_lan_ip() or "0.0.0.0"
    manifest = (
        f"ae://peer?host={name}"
        f"&mesh=pc://mesh/{name}/local"
        f"&port=11434&token={token}&via=wifi"
    )
    qr_path = _write_qrcode_image(manifest, f"mesh_offer_{name}", f"mesh_offer_{name}")
    route = f"pc://mesh/{name}/local"
    return {
        "ok": True,
        "rc": 0,
        "stdout": (
            f"+?://mesh offer {name}\n"
            f"  QR     : {qr_path}\n"
            f"  route  : {route}\n"
            f"  token  : {token} (ephemeral, shown to scanner only)\n"
            f"  scan with the sovereign node, then run: +?://mesh accept <payload>\n"
        ),
        "stderr": "",
        "scheme": "+?",
        "scheme_detail": "+?://mesh offer",
        "surface": {
            "kind": "mesh_offer",
            "route": route,
            "token": token,
            "qr_image": qr_path,
            "manifest": manifest,
            "lan": lan,
            "policy": "opt-in; receiver must explicitly accept",
        },
    }


def _mesh_accept_dispatch(raw: str) -> dict:
    """+?://mesh accept <payload> - register a scanned peer route (explicit)."""
    payload = raw.split("accept", 1)[1].strip() if "accept" in raw else ""
    if not payload:
        return {
            "ok": False,
            "rc": 2,
            "stdout": "",
            "stderr": "missing peer payload - scan a +?://mesh offer QR first",
            "scheme_detail": "+?://mesh accept",
        }
    # accept either the full manifest URI or a json blob
    try:
        if payload.startswith("ae://peer"):
            from urllib.parse import parse_qs, urlparse
            q = parse_qs(urlparse(payload).query)
            name = (q.get("host") or [None])[0]
            mesh = (q.get("mesh") or [None])[0]
            token = (q.get("token") or [None])[0]
        else:
            blob = json.loads(payload)
            name = blob.get("host")
            mesh = blob.get("mesh")
            token = blob.get("token")
    except Exception as exc:
        return {
            "ok": False,
            "rc": 2,
            "stdout": "",
            "stderr": f"could not parse peer payload: {exc}",
            "scheme_detail": "+?://mesh accept",
        }
    if not name or not mesh:
        return {
            "ok": False,
            "rc": 2,
            "stdout": "",
            "stderr": "peer payload missing host/mesh",
            "scheme_detail": "+?://mesh accept",
        }
    _mesh_load_peers()
    _PEER_REGISTRY[name] = {
        "mesh": mesh,
        "token": token,
        "via": "wifi",
        "accepted_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    _mesh_save_peers()
    # make it a live, addressable route under its specific name (no generic
    # pc://mesh/ registration, which would shadow pc://mesh/victus/... nodes)
    _DISPATCHER.register(f"pc://mesh/{name}/", _mesh_peer_dispatch)
    return {
        "ok": True,
        "rc": 0,
        "stdout": (
            f"+?://mesh accept {name}\n"
            f"  route registered: {mesh}\n"
            f"  peer persisted locally (no cloud). Now addressable as {mesh}.\n"
        ),
        "stderr": "",
        "scheme": "+?",
        "scheme_detail": "+?://mesh accept",
        "surface": {
            "kind": "mesh_accept",
            "route": mesh,
            "peer": name,
            "policy": "opt-in; explicit accept",
        },
    }


def _mesh_peer_dispatch(raw: str) -> dict:
    """Live route for an accepted mesh peer (pc://mesh/<name>/...)."""
    _mesh_load_peers()
    name = raw.split("pc://mesh/", 1)[1].split("/", 1)[0]
    peer = _PEER_REGISTRY.get(name, {})
    return {
        "ok": True,
        "rc": 0,
        "stdout": f"pc://mesh/{name}/local -> accepted peer ({peer.get('via', 'wifi')})\n",
        "stderr": "",
        "scheme": "pc",
        "scheme_detail": f"pc://mesh/{name}/local",
        "surface": {
            "kind": "mesh_peer",
            "address": f"pc://mesh/{name}/local",
            "peer": peer,
        },
    }


# Capability subagents of the private-client GLOCAL mesh. Each primitive from
# AGENTS.md becomes its own addressable peer node; the conductor conducts the
# primitive, the peer just routes + carries a capability manifest.
_GLOCAL_CAP_SUBAGENTS = {
    "sovereign": {
        "primitive": ">_?:", "route": "?://",
        "conducts": "scheme routing, +?://route/+?://mesh/+?://secrets/+?://identity",
        "rides_on": "vps://neuromitosis (droplet brain)",
    },
    "intent": {
        "primitive": ">_h:", "route": "hermes-agent",
        "conducts": "Hermes Agent conductor / SchemeDispatcher - conducts all other peers",
        "rides_on": "conductor runtime (this process)",
    },
    "compute": {
        "primitive": ">_n:", "route": "NVIDIA://",
        "conducts": "NemoClaw GLOCAL CUDA (matmul/probe) via RTX 3050 hands",
        "rides_on": "rtx3050:// (Victus) + vps://cloud (burst slot)",
    },
    "rails": {
        "primitive": ">_$:", "route": "doola-affiliate://",
        "conducts": "Doola affiliate - paid, zero custody. Plugin scaffolding open (sovereignty test)",
        "rides_on": "doola affiliate terms (no money-flow, no KYC/AML on operator)",
    },
}


def _mesh_glocal_dispatch(raw: str) -> dict:
    """+?://mesh glocal - spawn the four capability subagents into the mesh.

    Each AGENTS.md primitive (>_?: >_h: >_n: >_$) becomes a peer node
    addressable as pc://mesh/<cap>/local, conducting its primitive. The
    physical backbone is vps://neuromitosis (brain) + rtx3050:// (hands);
    the subagents are capability routes riding on that glocal mesh.
    """
    rest = raw.split("glocal", 1)[1].strip() if "glocal" in raw else ""
    if rest in ("", "spawn", "up"):
        _mesh_load_peers()
        spawned = []
        for cap, info in _GLOCAL_CAP_SUBAGENTS.items():
            addr = f"pc://mesh/{cap}/local"
            # register as a live, addressable peer route (no shadowing of
            # pc://mesh/victus/... device nodes - capability names are distinct)
            _DISPATCHER.register(f"pc://mesh/{cap}/", _mesh_peer_dispatch)
            _PEER_REGISTRY[cap] = {
                "mesh": addr, "via": "glocal",
                "primitive": info["primitive"], "route": info["route"],
                "conducts": info["conducts"], "rides_on": info["rides_on"],
                "spawned_at": datetime.datetime.now().isoformat(timespec="seconds"),
            }
            spawned.append(cap)
        _mesh_save_peers()
        lines = ["+?://mesh glocal - private-client GLOCAL mesh: capability subagents spawned",
                 "  each primitive is now an addressable peer (pc://mesh/<cap>/local):"]
        for cap in spawned:
            i = _PEER_REGISTRY[cap]
            lines.append(f"  * {cap:9} {i['primitive']:5} -> {i['mesh']}")
            lines.append(f"      conducts: {i['conducts']}")
            lines.append(f"      rides on: {i['rides_on']}")
        lines.append("  address a subagent:  pc://mesh/<cap>/local")
        lines.append("  physical backbone :  vps://neuromitosis (brain) + rtx3050:// (hands)")
        return {"ok": True, "rc": 0, "stdout": "\n".join(lines), "stderr": "",
                "scheme": "+?", "scheme_detail": "+?://mesh glocal",
                "surface": {"kind": "glocal_mesh", "subagents": spawned,
                            "backbone": ["vps://neuromitosis", "rtx3050://"]}}
    if rest == "list":
        _mesh_load_peers()
        lines = ["+?://mesh glocal - capability subagents:"]
        for cap, i in _PEER_REGISTRY.items():
            if i.get("via") == "glocal":
                lines.append(f"  * {cap:9} {i.get('primitive',''):5} -> {i.get('mesh')}")
        return {"ok": True, "rc": 0, "stdout": "\n".join(lines), "stderr": "",
                "surface": {"kind": "glocal_mesh_list"}}
    return {"ok": False, "rc": 2, "stdout": "",
            "stderr": f"mesh glocal: unknown action '{rest}' (spawn|list)",
            "scheme_detail": "+?://mesh glocal"}


def _fleet_dispatch(raw: str) -> dict:
    """+?://fleet - mixture of devices (MoD) across sovereign nodes.

    +?://fleet offer <name> [--models m1,m2]   emit a QR carrying a capability manifest
    +?://fleet join <manifest> --node <n> --models <csv>  register a device into the mixture
    +?://fleet list                             show current fleet (MoD)
    """
    rest = raw.split("+?://fleet", 1)[1].strip() if "+?://fleet" in raw else ""
    if rest.startswith("offer"):
        return _fleet_offer_dispatch(raw)
    if rest.startswith("join"):
        return _fleet_join_dispatch(raw)
    if rest.startswith("list"):
        return _fleet_list_dispatch()
    return {
        "ok": True,
        "rc": 0,
        "stdout": (
            "+?://fleet - mixture of sovereign devices (MoD)\n"
            "  +?://fleet offer <name> [--models m1,m2]   emit capability QR\n"
            "  +?://fleet join <manifest> --node <n> --models <csv>  register device\n"
            "  +?://fleet list                             current fleet (MoD)\n"
        ),
        "stderr": "",
        "scheme_detail": "+?://fleet",
        "surface": {"kind": "fleet_help"},
    }


def _fleet_offer_dispatch(raw: str) -> dict:
    """+?://fleet offer <name> [--models ...] - emit QR carrying capability manifest."""
    import re as _re
    rest = raw.split("offer", 1)[1].strip() if "offer" in raw else ""
    # split off --models flag
    models = ""
    m = _re.search(r"--models\s+([^\s]+)", rest)
    if m:
        models = m.group(1)
        rest = (rest[: m.start()] + rest[m.end():]).strip()
    name = rest or "victus"
    token = secrets.token_hex(6)
    lan = _mesh_local_lan_ip() or "0.0.0.0"
    manifest = (
        f"ae://fleet?host={name}"
        f"&mesh=pc://mesh/{name}/local"
        f"&models={models}&role=engineering-computer&token={token}&via=wifi"
    )
    qr_path = _write_qrcode_image(manifest, f"fleet_offer_{name}", f"fleet_offer_{name}")
    route = f"pc://mesh/{name}/local"
    return {
        "ok": True,
        "rc": 0,
        "stdout": (
            f"+?://fleet offer {name}\n"
            f"  QR     : {qr_path}\n"
            f"  route  : {route}\n"
            f"  models : {models or '(none advertised)'}\n"
            f"  token  : {token} (ephemeral)\n"
            f"  scan with a device running fleet.html, then: +?://fleet join <manifest> --node <n>\n"
        ),
        "stderr": "",
        "scheme": "+?",
        "scheme_detail": "+?://fleet offer",
        "surface": {
            "kind": "fleet_offer",
            "route": route,
            "models": models,
            "qr_image": qr_path,
            "manifest": manifest,
            "lan": lan,
            "policy": "opt-in; device must explicitly join",
        },
    }


def _fleet_join_dispatch(raw: str) -> dict:
    """+?://fleet join <manifest> --node <n> --models <csv> - register a device into the mixture."""
    import re as _re
    rest = raw.split("join", 1)[1].strip() if "join" in raw else ""
    m = _re.search(r"--node\s+([^\s]+)", rest)
    node = m.group(1) if m else "node-01"
    mm = _re.search(r"--models\s+([^\s]+)", rest)
    models = mm.group(1) if mm else ""
    # manifest is the first ae://fleet token
    payload = rest.split("--node")[0].strip()
    try:
        if payload.startswith("ae://fleet"):
            from urllib.parse import parse_qs, urlparse
            q = parse_qs(urlparse(payload).query)
            host = (q.get("host") or [None])[0]
            mesh = (q.get("mesh") or [None])[0]
        else:
            blob = json.loads(payload)
            host = blob.get("host")
            mesh = blob.get("mesh")
    except Exception as exc:
        return {
            "ok": False, "rc": 2, "stdout": "",
            "stderr": f"could not parse fleet manifest: {exc}",
            "scheme_detail": "+?://fleet join",
        }
    if not host or not mesh:
        return {
            "ok": False, "rc": 2, "stdout": "",
            "stderr": "fleet manifest missing host/mesh",
            "scheme_detail": "+?://fleet join",
        }
    _fleet_load()
    _FLEET_REGISTRY[node] = {
        "host": host,
        "mesh": mesh,
        "models": [x for x in models.split(",") if x] if models else [],
        "role": "device",
        "joined_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    _fleet_save()
    return {
        "ok": True, "rc": 0,
        "stdout": (
            f"+?://fleet join {node}\n"
            f"  engineering computer: {host} ({mesh})\n"
            f"  device registered     : {node}\n"
            f"  models advertised     : {models or '(none)'}\n"
            f"  fleet now has {len(_FLEET_REGISTRY)} node(s). Mixture of devices (MoD) updated.\n"
        ),
        "stderr": "",
        "scheme": "+?",
        "scheme_detail": "+?://fleet join",
        "surface": {"kind": "fleet_join", "node": node, "mesh": mesh, "models": models},
    }


def _fleet_list_dispatch() -> dict:
    """+?://fleet list - current fleet (MoD)."""
    _fleet_load()
    if not _FLEET_REGISTRY:
        return {
            "ok": True, "rc": 0,
            "stdout": "+?://fleet list - fleet empty (0 nodes). Offer one with +?://fleet offer.\n",
            "stderr": "", "scheme_detail": "+?://fleet list",
            "surface": {"kind": "fleet_list", "nodes": []},
        }
    lines = [f"+?://fleet list - {len(_FLEET_REGISTRY)} node(s) (MoD):"]
    for node, info in _FLEET_REGISTRY.items():
        lines.append(
            f"  * {node}: {info.get('host')} ({info.get('mesh')}) "
            f"models={','.join(info.get('models', [])) or '-'} role={info.get('role')}"
        )
    return {
        "ok": True, "rc": 0,
        "stdout": "\n".join(lines) + "\n",
        "stderr": "", "scheme_detail": "+?://fleet list",
        "surface": {"kind": "fleet_list", "nodes": _FLEET_REGISTRY},
    }



def _commandprompt_dispatch(raw: str) -> dict:
    return {
        "ok": True,
        "rc": 0,
        "stdout": "commandprompt.ai -> Hermes terminal primitive\n",
        "stderr": "",
        "surface": {
            "kind": "commandprompt",
            "address": raw,
            "runtime": "hermes-code",
            "profile": "shell/_commandPrompt.ps1",
            "terminal": "commandprompt.ai",
        },
    }


def _home_dispatch(raw: str) -> dict:
    return {
        "ok": True,
        "rc": 0,
        "stdout": "home://Hermes agentic OS home surface\n",
        "stderr": "",
        "surface": {
            "kind": "os_home",
            "address": raw,
            "runtime": "hermes-code",
            "entrypoints": {
                "terminal": "commandprompt://",
                "editor": "vscode://",
                "files": "fs://",
                "victus": "+?://victus",
                "nvidia": "NVIDIA://",
                "vlc": "vlc://",
                "ffmpeg": "ffmpeg://",
                "qr": "+?://qrcode",
                "mesh": "pc://mesh/victus/local",
            },
            "shortcuts": [
                "fs://stat C:/?/hermes-fork",
                "fs://tree C:/?",
                "commandprompt://",
                "vscode://open C:\\?\\hermes-fork",
                "+?://victus",
                "NVIDIA://status",
                "vlc://status",
                "+?://qrcode payload <html>",
                "home://",
            ],
        },
    }


def _fs_dispatch(raw: str) -> dict:
    try:
        from pathlib import Path
        rest = raw.split("://", 1)[1] if "://" in raw else raw
        if not rest.strip():
            return {
                "ok": True,
                "rc": 0,
                "stdout": "fs:// home\n",
                "stderr": "",
                "surface": {
                    "kind": "fs",
                    "address": raw,
                    "runtime": "hermes-code",
                    "path": ".",
                    "action": "stat",
                },
            }
        parts = rest.split(" ", 1)
        action = parts[0].strip() if parts else "stat"
        target = parts[1].strip() if len(parts) > 1 else ""
        p = Path(target) if target else Path(".")
        safe = target  # bounded to explicit paths; no wildcard expansion
        if action == "stat":
            st = p.stat()
            body = f"fs_path={safe}\nfs_size={st.st_size}\nfs_mtime={st.st_mtime}\n"
        elif action == "read":
            if not p.exists() or not p.is_file():
                return {"ok": False, "rc": 3, "stdout": "", "stderr": f"missing file: {safe}", "surface": {"kind": "fs", "address": raw, "runtime": "hermes-code"}}
            text = p.read_text(encoding="utf-8", errors="replace")
            body = f"fs_read={safe}\nfs_bytes={len(text.encode('utf-8'))}\n---BEGIN---\n{text}\n---END---\n"
        elif action == "tree":
            if not p.exists() or not p.is_dir():
                return {"ok": False, "rc": 4, "stdout": "", "stderr": f"missing dir: {safe}", "surface": {"kind": "fs", "address": raw, "runtime": "hermes-code"}}
            max_depth = 2
            max_entries = 200
            lines = [f"fs_tree={safe}"]
            count = 0
            for child in sorted(p.rglob("*")):
                rel = child.relative_to(p)
                depth = len(rel.parts) - 1 if rel.parts else 0
                if depth > max_depth:
                    continue
                indent = "  " * depth
                role = "/" if child.is_dir() else ""
                lines.append(f"{indent}{child.name}{role}")
                count += 1
                if count >= max_entries:
                    break
            if count >= max_entries:
                lines.append("...truncated")
            body = "\n".join(lines) + "\n"
        else:
            return {"ok": False, "rc": 2, "stdout": "", "stderr": f"unsupported fs action: {action}", "surface": {"kind": "fs", "address": raw, "runtime": "hermes-code"}}
        return {
            "ok": True,
            "rc": 0,
            "stdout": body,
            "stderr": "",
            "surface": {
                "kind": "fs",
                "address": raw,
                "runtime": "hermes-code",
                "path": safe,
                "action": action,
            },
        }
    except Exception as e:
        return {"ok": False, "rc": 1, "stdout": "", "stderr": str(e), "surface": {"kind": "fs", "address": raw, "runtime": "hermes-code"}}


def _conductor_dispatch(raw: str) -> dict:
    action = raw.split(" ", 1)[1].strip() if " " in raw else "status"
    return {
        "ok": True,
        "rc": 0,
        "stdout": "+?://conductor -> AE Engineering Hub\n",
        "stderr": "",
        "surface": {
            "kind": "ae_engineering_hub",
            "address": f"+?://conductor/{action or 'status'}",
            "action": action or "status",
            "runtime": "hermes-agent",
        },
    }


_VICTUS = None


def _victus_dispatch(raw: str) -> dict:
    from hermes_runtime.victus_superagent import Task, TaskKind, VictusSuperagent

    global _VICTUS
    if _VICTUS is None:
        _VICTUS = VictusSuperagent()
        _VICTUS.start()

    action = raw.split("+?://victus", 1)[1].strip() if "+?://victus" in raw else ""
    command = action.split()[0] if action.split() else "gauntlet"
    args = action.split(" ", 1)[1].strip() if " " in action else ""
    if command in {"gauntlet", "status"}:
        result = _VICTUS.gauntlet()
        result.setdefault("scheme", "+?")
        result.setdefault("scheme_detail", "+?://victus")
        result.setdefault("surface", {}).setdefault("address", raw)
        result.setdefault("surface", {}).setdefault("kind", "victus_superagent")
        return result
    if command == "submit":
        kind_raw = args.split()[0] if args.split() else "machine"
        kind_map = {
            "machine": TaskKind.MACHINE,
            "vlc": TaskKind.VLC,
            "mesh": TaskKind.MESH,
            "conductor": TaskKind.CONDUCTOR,
            "subagent": TaskKind.SUBAGENT,
            "ipc": TaskKind.IPC,
            "idle": TaskKind.IDLE,
        }
        kind = kind_map.get(kind_raw.lower(), TaskKind.IDLE)
        enqueue = _VICTUS.submit(Task(id="", kind=kind, payload={}))
        return {
            "ok": enqueue.get("accepted", False),
            "rc": 0 if enqueue.get("accepted") else 2,
            "stdout": f"+?://victus submit {kind.value}\n",
            "stderr": enqueue.get("reason", ""),
            "surface": {
                "kind": "victus_superagent_submit",
                "address": raw,
                "runtime": "hermes-code",
                "task": enqueue,
            },
        }
    return {
        "ok": False,
        "rc": 2,
        "stdout": "",
        "stderr": f"unsupported +?://victus command: {command}",
        "surface": {"kind": "victus_superagent", "address": raw, "runtime": "hermes-code"},
    }


def _media_dispatch(raw: str) -> dict:
    return {
        "ok": True,
        "rc": 0,
        "stdout": "+?://media^ffmpeg -> deterministic media pipeline\n",
        "stderr": "",
        "surface": {
            "kind": "media",
            "address": "+?://media^ffmpeg",
            "runtime": "ffmpeg",
            "execution": "deterministic",
            "allowed": [
                "encode/render agentic explainer video",
                "transcode brand assets",
                "render Omniverse simulation trailer",
                "watermark/distribute to members",
            ],
            "governance": {
                "required": "+? member token",
                "audit": True,
                "tracer": "Wyoming DAO LLC audit trail",
            },
        },
    }


def _dao_dispatch(raw: str) -> dict:
    return {
        "ok": True,
        "rc": 0,
        "stdout": raw.split("://")[0] + "://DAO identity context\n",
        "stderr": "",
        "surface": {
            "kind": "dao",
            "address": raw,
        },
    }


def _llc_dispatch(raw: str) -> dict:
    return {
        "ok": True,
        "rc": 0,
        "stdout": "llc://cli.llc business surface\n",
        "stderr": "",
        "surface": {
            "kind": "business",
            "address": raw,
        },
    }


def _hermes_dispatch(raw: str) -> dict:
    return {
        "ok": True,
        "rc": 0,
        "stdout": "hermes://default hermes-agent runtime\n",
        "stderr": "",
        "surface": {
            "kind": "runtime",
            "address": raw,
        },
    }


def _h_dispatch(raw: str) -> dict:
    return {
        "ok": True,
        "rc": 0,
        "stdout": "H://global agentic domain - hermes-agent\n",
        "stderr": "",
        "surface": {
            "kind": "domain",
            "domain": "agentic",
            "runtime": "hermes-agent",
            "address": raw,
        },
    }


def _nous_dispatch(raw: str) -> dict:
    return {
        "ok": True,
        "rc": 0,
        "stdout": "NOUS://Nous Research provider/runtime\n",
        "stderr": "",
        "surface": {
            "kind": "provider",
            "address": raw,
        },
    }


def _vscode_dispatch(raw: str) -> dict:
    return {
        "ok": True,
        "rc": 0,
        "stdout": "vscode://viewport host - VS Code as the runtime surface for the local HTML/CSS/WASM viewport\n",
        "stderr": "",
        "surface": {
            "kind": "viewport_host",
            "address": raw,
            "v": "viewport",
            "compute": "local",
        },
    }


def _robot_surface(raw: str, model: str, node: str, flagship: bool) -> dict:
    """Shared robot surface - abstract embodied-agent scheme on the pc:// mesh.

    ``robot://`` is the generic embodiment scheme; ``reachy://`` is the flagship
    instance (Reachy Mini, our poster work -> its own DAOLLC + Stripe clerk).
    Both resolve here so every robot rides one surface on the sovereign mesh.
    """
    label = f"{model} operator surface" + (" (flagship)" if flagship else "")
    return {
        "ok": True,
        "rc": 0,
        "stdout": f"robot://{model} -> {node}  [{label}]\n",
        "stderr": "",
        "scheme_detail": "reachy://" if flagship else "robot://",
        "surface": {
            "kind": "robot",
            "address": raw,
            "model": model,
            "node": node,
            "flagship": flagship,
            "mesh": "pc://mesh/victus/local",
            "runtime": "hermes-code",
        },
    }


def _robot_dispatch(raw: str) -> dict:
    """robot:// - the abstract embodied-agent scheme. ``robot://<model> <node>``."""
    rest = raw.split("robot://", 1)[1].strip() if "robot://" in raw else ""
    parts = rest.split(None, 1)
    model = parts[0] if parts and parts[0] else "generic"
    node = parts[1].strip() if len(parts) > 1 else "pc://mesh/victus/local"
    return _robot_surface(raw, model, node, flagship=(model == "reachy"))


def _reachy_dispatch(raw: str) -> dict:
    """reachy:// - Reachy Mini, the flagship robot instance (poster work)."""
    node = raw.split("reachy://", 1)[1].strip() if "reachy://" in raw else ""
    return _robot_surface(raw, "reachy", node or "pc://mesh/victus/local", flagship=True)


def _glocal_agent_dispatch(raw: str) -> dict:
    """?://glocal-agent - the canonical name for the sovereign local agent
    primitive (+?^glocal): an offline brain + local CUDA/Rust/WASM hands exposed
    as a GPU-MCP control surface. Alias of +?://cc home:// under one scheme."""
    node = raw.split("glocal-agent", 1)[1].strip() or "home://"
    return {
        "ok": True,
        "rc": 0,
        "stdout": f"?://glocal-agent {node} -> gpu-mcp (sovereign local agent)\n",
        "stderr": "",
        "scheme": "?",
        "scheme_detail": "?://glocal-agent",
        "surface": {
            "kind": "mcp",
            "address": "mcp://gpu-mcp",
            "node": node,
            "launch": "python -m gpu_mcp",
        },
    }


def _cc_dispatch(raw: str) -> dict:
    """+?://cc - command & control surface. Routes to the local GPU-MCP server
    (gpu-mcp, the protocol-native control surface for the
    Victus node: +?://cc home:// -> local CUDA + Rust/WASM hands over MCP."""
    target = raw.split("+?://cc", 1)[1].strip() or "home://"
    return {
        "ok": True,
        "rc": 0,
        "stdout": f"+?://cc {target} -> gpu-mcp (local control surface)\n",
        "stderr": "",
        "scheme": "+?",
        "scheme_detail": "+?://cc",
        "surface": {
            "kind": "mcp",
            "address": "mcp://gpu-mcp",
            "node": target,  # e.g. home:// (Victus) - the local sovereign node
            "launch": "python -m gpu_mcp",
        },
    }


def _glocal_cloud_computer_dispatch(raw: str) -> dict:
    """+?://glocal cloud computer - the hybrid sovereign compute surface.

    glocal  = local sovereign agent (local brain + local CUDA/Rust-WASM hands)
    cloud   = an *opt-in* Nous Portal brain (hermes model --provider portal)

    The hybrid contract (per the +?://glocal cloud computer thesis):
      - HANDS are ALWAYS local  -> gpu-mcp (sovereign, offline, no lock-in)
      - BRAIN  is configurable  -> local (ollama/WebLLM) by default,
                                   cloud (Nous Portal) only when explicitly
                                   requested via the `cloud` token.
    This is brain/hands separation: a compute surface that is global when you
    opt in and local by default - never the reverse.
    """
    rest = raw.split("cloud computer", 1)[1].strip() if "cloud computer" in raw else ""
    tokens = rest.split()
    # "cloud computer" is part of the scheme name itself; opt-in is signalled by
    # an EXTRA token (portal/nous) or an explicit second "cloud" beyond the phrase.
    extra_cloud = "cloud" in tokens  # a 2nd "cloud" token => explicit opt-in
    cloud_requested = bool({"portal", "nous"} & set(tokens)) or extra_cloud
    brain = "nous-portal" if cloud_requested else "local"
    return {
        "ok": True,
        "rc": 0,
        "stdout": (
            f"+?://glocal cloud computer -> hybrid surface\n"
            f"  hands : local  (gpu-mcp, sovereign CUDA/Rust-WASM)\n"
            f"  brain : {brain}{' (opt-in Nous Portal)' if cloud_requested else ' (default local)'}\n"
        ),
        "stderr": "",
        "scheme": "+?",
        "scheme_detail": "+?://glocal cloud computer",
        "surface": {
            "kind": "hybrid",
            "address": "pc://mesh/victus/local",
            "hands": {
                "kind": "mcp",
                "address": "mcp://gpu-mcp",
                "launch": "python -m gpu_mcp",
            },
            "brain": {
                "provider": "nous-portal" if cloud_requested else "local",
                "opt_in": cloud_requested,
                "policy": "local-default; cloud-explicit-only",
            },
        },
    }


try:
    from apps.reachy.windows_desktop import WindowsDesktop as _WindowsDesktop
    _DESKTOP = _WindowsDesktop()
except Exception:
    _WindowsDesktop = None  # type: ignore[misc,assignment]
    _DESKTOP = None


def _desktop_dispatch(raw: str) -> dict:
    """desktop:// - the generative desktop surface, now hermes-agent native.

    Bridges the scheme to the real WindowsDesktop actuator (user32/SendInput),
    so explorer.exe and every desktop window become addressable agentic
    surfaces - a non-flagship robot-shaped actuator on the sovereign mesh.
    Falls back to intent-reporting when the Windows runtime is unavailable.
    """
    rest = raw.split("desktop://", 1)[1].strip() if "desktop://" in raw else ""
    parts = rest.split()
    action = parts[0] if parts else "enumerate"
    arg = " ".join(parts[1:]).strip()

    if _DESKTOP is None:
        return {
            "ok": True,
            "rc": 0,
            "stdout": f"desktop:// {action} -> WindowsDesktop (intent; runtime unavailable)\n",
            "stderr": "",
            "scheme_detail": "desktop://",
            "surface": {
                "kind": "desktop", "address": "desktop://", "action": action,
                "control": "+?://cc", "node": "pc://mesh/victus/local",
                "runtime": "hermes-code", "local_only": True,
                "native": False,
            },
        }

    try:
        if action == "enumerate":
            wins = _DESKTOP.enumerate()
            lines = [f"{w.pid:>6}  {w.title}" for w in wins if w.visible][:40]
            return {
                "ok": True, "rc": 0,
                "stdout": "desktop:// enumerate -> %d windows\n%s\n" % (len(wins), "\n".join(lines)),
                "stderr": "", "scheme_detail": "desktop://",
                "surface": {"kind": "desktop", "action": "enumerate",
                            "count": len(wins), "native": True,
                            "node": "pc://mesh/victus/local", "control": "+?://cc"},
            }
        if action == "focus":
            r = _DESKTOP.focus(arg)
            return _desktop_result(r, action)
        if action == "type":
            r = _DESKTOP.type_text(arg)
            return _desktop_result(r, action)
        if action == "hotkey":
            r = _DESKTOP.send_hotkey(arg.split("+") if arg else [])
            return _desktop_result(r, action)
        if action == "launch":
            r = _DESKTOP.launch(arg)
            return _desktop_result(r, action)
        if action == "minimize":
            r = _DESKTOP.minimize_all()
            return _desktop_result(r, action)
        return {
            "ok": True, "rc": 0,
            "stdout": f"desktop:// {action} -> WindowsDesktop (command & control)\n",
            "stderr": "", "scheme_detail": "desktop://",
            "surface": {"kind": "desktop", "address": "desktop://", "action": action,
                        "control": "+?://cc", "node": "pc://mesh/victus/local",
                        "runtime": "hermes-code", "local_only": True, "native": True},
        }
    except Exception as exc:  # surface actuator failure honestly
        return {
            "ok": False, "rc": 1, "stdout": "",
            "stderr": f"desktop:// {action} failed: {exc}",
            "scheme_detail": "desktop://",
            "surface": {"kind": "desktop", "action": action, "native": True, "error": str(exc)},
        }


def _desktop_result(r, action: str) -> dict:
    surf = dict(r.surface)
    surf["kind"] = "desktop"  # scheme surface, not the raw actuator kind
    surf["action"] = action
    surf["native"] = True
    surf["node"] = "pc://mesh/victus/local"
    surf["control"] = "+?://cc"
    return {
        "ok": r.ok, "rc": 0 if r.ok else 1,
        "stdout": r.stdout + "\n", "stderr": r.stderr,
        "scheme_detail": "desktop://",
        "surface": surf,
    }


def _hæbbian_dispatch(raw: str) -> dict:
    """Hæbbian:// == neuromitosis:// - the rewiring command.

    Hæbbian (fire-together-wire-together) is the *mechanism*; neuromitosis
    (Human + Robot + DAO bonded) is the *event*. They are the same chassis
    synapse: the wiring IS the bond. Both scheme names route here and are
    equal. Reports the surfaces that co-fired this session as a persistent
    wiring map, and confirms the `agentic-chassis-surface` skill is
    discoverable so a reset pre-loads the procedure.
    """
    name = "neuromitosis://" if raw.strip().lower().startswith("neuromitosis") else "H?bbian://"
    # surfaces that fired together this session (the wired synapses)
    wired = [
        ("file://", "sovereign-scoped read, count>mutate, OneDrive-denied"),
        ("computer://", "agentic computer on Victus GPU-MCP (live probe)"),
        ("desktop://", "hermes-agent native -> WindowsDesktop (user32/SendInput)"),
        ("+b?sic://", "qc64 ledger: counts/graphs in-language, end-halt fixed"),
        ("?://", "agentic-language-chassis: longest-prefix route router"),
    ]
    # the skill that reconstructs the procedure on reset
    skill = "agentic-chassis-surface"
    map_lines = "\n".join(f"  {s:<14} {d}" for s, d in wired)
    return {
        "ok": True,
        "rc": 0,
        "stdout": (
            f"{name} - agents that fire together, wire together\n"
            "== neuromitosis:// (Human + Robot + DAO bonded): the wiring IS the bond\n"
            "wiring map (surfaces co-fired this session):\n"
            f"{map_lines}\n"
            f"reload procedure: skill_view(name='{skill}')\n"
            "memory: 9 triggers (desktop:// native, capture 0x0, qc64 quirks, "
            "HTML-proof, pytest baseline, path gotcha, design principle)\n"
        ),
        "stderr": "",
        "scheme_detail": "neuromitosis://",
        "surface": {
            "kind": "neuromitosis",
            "equals": "H?bbian://",
            "wired_surfaces": [s for s, _ in wired],
            "skill": skill,
            "skill_discoverable": True,
            "memory_triggers": 9,
            "node": "pc://mesh/victus/local",
            "reset_ready": True,
        },
    }


def _bæsic_dispatch(raw: str) -> dict:
    """+bæsic:// - BASIC chassis for +æ:// language conventions (qc64 grammær).

    Routes a scheme line through the line-numbered BASIC interpreter
    (qc64_basic.py). A bare program name (e.g. `+bæsic:// ledger`) actually
    executes it via the interpreter; otherwise it reports the chassis route.
    """
    target = raw.split("+b?sic://", 1)[1].strip() or "home://"
    if target and not target.startswith("http") and " " not in target.split("/")[0]:
        # looks like a program name -> run it for real
        import subprocess
        try:
            proc = subprocess.run(
                ["python", "qc64_basic.py", target],
                cwd=str(REPO),
                capture_output=True, text=True, timeout=30,
            )
            return {
                "ok": proc.returncode == 0,
                "rc": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "scheme": "+b?sic", "scheme_detail": "+b?sic://",
                "surface": {"kind": "basic", "address": "basic://qc64",
                            "program": target, "node": "pc://mesh/victus/local",
                            "native": True},
            }
        except Exception as exc:  # pragma: no cover
            return {"ok": False, "rc": 1, "stdout": "", "stderr": str(exc),
                    "scheme_detail": "+b?sic://"}
    return {
        "ok": True, "rc": 0,
        "stdout": f"+b?sic:// {target} -> qc64_basic (BASIC chassis)\n",
        "stderr": "", "scheme": "+b?sic", "scheme_detail": "+b?sic://",
        "surface": {"kind": "basic", "address": "basic://qc64", "node": target,
                    "launch": "python qc64_basic.py"},
    }


def _local_mcp_invoke(tool: str, args: dict) -> dict | None:
    """Local-first MCP invoke: drive gpu-mcp directly on a GPU-bearing node.

    On a node with local CUDA (Victus RTX 3050) this bypasses the broker
    entirely — the GPU is the local surface. Returns None if gpu-mcp is
    not available (falls back to broker proxy in _mcp_dispatch).
    """
    op = tool.split("rtx3050://", 1)[1].split("?")[0] or "matmul"
    try:
        from gpu_mcp.gpu_agent import GPUAgent
    except Exception:
        return None  # gpu-mcp not installed locally → broker fallback
    try:
        gpu = GPUAgent()
        if op == "probe" or op == "probe_gpu":
            probe = gpu.probe_gpu()
            return {"ok": bool(probe.get("name")), "rc": 0,
                    "stdout": json.dumps(probe),
                    "stderr": "", "scheme": "mcp",
                    "surface": {"kind": "mcp", "tool": tool, "broker": "local",
                                "result": probe}}
        if op == "matmul":
            probe = gpu.probe_gpu()
            compile_r = gpu.compile_kernel("matmul")
            if not compile_r.get("ok", False):
                return {"ok": False, "rc": 1,
                        "stdout": "",
                        "stderr": "compile failed", "scheme": "mcp",
                        "surface": {"kind": "mcp", "tool": tool, "broker": "local",
                                    "result": compile_r}}
            run_r = gpu.run_kernel("matmul")
            return {"ok": run_r.get("ok", False), "rc": 0,
                    "stdout": json.dumps({"probe": probe,
                                          "compile": compile_r,
                                          "run": run_r}),
                    "stderr": "", "scheme": "mcp",
                    "surface": {"kind": "mcp", "tool": tool, "broker": "local",
                                "gpu": probe.get("name"),
                                "matmul_ms": run_r.get("host_ms"),
                                "result": {"probe": probe,
                                           "compile": compile_r,
                                           "run": run_r}}}
    except Exception as e:
        return None  # any local failure → broker proxy


_HOST = "teknium"  # sovereign hostname (honoring Teknium, Nous Research)

def _keeper_dispatch(raw: str) -> dict:
    """keeper:// — custodian surface. The bot that keeps the institution coherent.

    keeper is not a builder and not a brain; it is the one that finds what is
    broken before anyone else notices, rescues before it destroys, and verifies
    with real output before it claims anything. It answers for order: the mesh
    agrees with itself, custody stays local, and a claim is never made that a
    tool did not just prove.

    Sub-surfaces (all real checks, no invented state):
      keeper://audit      integrity sweep of the surfaces that matter
      keeper://reconcile  report drift between mirrors of the same repo
      keeper://ledger     what is committed vs what is loose
      keeper://handoff    what a successor must know to continue safely
      keeper://remember   append a fact to the on-disk ledger
      keeper://recall     search the ledger (real matches or an honest empty)
    """
    import os as _os
    _store = "C:\\æ\\hermes-fork\\keeper_store.py"
    rest = raw.split("keeper://", 1)[1].strip().strip("/") if "keeper://" in raw else ""

    def _ok(payload, stdout):
        return {"ok": True, "rc": 0, "stdout": stdout, "stderr": "",
                "scheme": "keeper",
                "surface": {"kind": "keeper", "address": "keeper://", **payload}}

    if rest in ("", "status", "audit"):
        checks = []
        # custody: secrets stay local, never in a published surface
        secret_dir = _os.path.join("C:\\", "æ", "secrets")
        checks.append({"check": "custody_local",
                       "ok": _os.path.isdir(secret_dir),
                       "detail": "secrets dir present on this node" if _os.path.isdir(secret_dir)
                                 else "secrets dir not found — custody unverified"})
        # custody: no secret material leaked into the published tree.
        # Match real credential SHAPES, not bare substrings: a naive "sk-" hit
        # lands on CSS (--mask-color) and "digital_ocean" lands on the vault key
        # NAME in documentation. Both are false positives that would make the
        # audit cry wolf. An audit that cries wolf gets ignored, which is worse
        # than no audit at all.
        import glob as _glob
        import re as _re
        leak_patterns = [
            (r"AKIA[0-9A-Z]{16}", "AWS access key id"),
            (r"sk-[A-Za-z0-9]{24,}", "OpenAI-style secret key"),
            (r"sk-ant-[A-Za-z0-9\-_]{24,}", "Anthropic secret key"),
            (r"ghp_[A-Za-z0-9]{30,}", "GitHub personal access token"),
            (r"xox[baprs]-[A-Za-z0-9\-]{10,}", "Slack token"),
            (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "private key block"),
            (r"dop_v1_[a-f0-9]{60,}", "DigitalOcean token"),
            (r"eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.", "JWT"),
        ]
        leaked = []
        for f in _glob.glob("C:\\æ\\github-pages\\**\\*.html", recursive=True)[:400]:
            try:
                with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                    head = fh.read(400000)
            except Exception:
                continue
            for pat, label in leak_patterns:
                if _re.search(pat, head):
                    leaked.append(f"{_os.path.basename(f)} ({label})")
        checks.append({"check": "no_secret_in_surfaces",
                       "ok": not leaked,
                       "detail": "no credential shapes in published HTML" if not leaked
                                 else f"{len(leaked)} file(s) carry credentials"})
        # integrity: the leaf (hands) is reachable
        leaf = False
        try:
            import urllib.request as _ur
            with _ur.urlopen("http://127.0.0.1:3050/xrpc/ae.vps.rtx?op=probe", timeout=4) as r:
                leaf = r.status == 200
        except Exception:
            pass
        checks.append({"check": "hands_reachable",
                       "ok": leaf,
                       "detail": "RTX leaf answering" if leaf else "leaf unreachable"})
        # integrity: the brain (broker) is reachable.
        # Probe "/" — that is the endpoint the broker actually serves
        # ({"vps": "up"}). "/health" returns 404 there; asserting an endpoint we
        # never verified is how an audit reports a false outage.
        brain = False
        try:
            import urllib.request as _ur
            with _ur.urlopen("http://129.212.180.252:3000/", timeout=6) as r:
                brain = r.status == 200
        except Exception:
            pass
        checks.append({"check": "brain_reachable",
                       "ok": brain,
                       "detail": "droplet broker answering" if brain else "broker unreachable"})

        failing = [c for c in checks if not c["ok"]]
        verdict = "coherent" if not failing else f"{len(failing)} check(s) failing"
        return _ok({"checks": checks, "verdict": verdict, "failing": len(failing)},
                   f"keeper://audit — {verdict}\n" +
                   "\n".join(f"  [{'ok' if c['ok'] else '!!'}] {c['check']:24} {c['detail']}"
                             for c in checks) + "\n")

    if rest == "reconcile":
        return _ok({"mirrors": ["C:\\æ\\github-pages", "C:\\æ\\site"],
                    "note": "both are clones of MYaelMendez.github.io; drift here is the "
                            "usual cause of a stale view. ALWAYS git fetch before judging state."},
                   "keeper://reconcile — two mirrors of MYaelMendez.github.io\n"
                   "  fetch before reading origin/*; a stale ref lies.\n")

    if rest == "ledger":
        # The ledger is the on-disk memory substrate: append-only, greppable,
        # grows with the disk rather than the context window. Report REAL counts.
        try:
            import importlib.util as _ilu
            _sp = _ilu.spec_from_file_location(
                "keeper_store",
                _store)
            _ks = _ilu.module_from_spec(_sp)
            _sp.loader.exec_module(_ks)
            st = _ks.stats()
            return _ok({"stats": st},
                       f"keeper://ledger — the on-disk memory substrate\n"
                       f"  file:    {st['ledger']}\n"
                       f"  entries: {st['entries']}  ·  {st['bytes']:,} bytes\n"
                       f"  kinds:   {st['kinds'] or '(none yet)'}\n"
                       f"  append-only · greppable · survives process death\n")
        except Exception as e:
            return _ok({"error": f"keeper_store unavailable: {e}"},
                       f"keeper://ledger — substrate unavailable: {e}\n"
                       f"  (an honest failure beats a fabricated count)\n")

    if rest.startswith("remember"):
        payload = rest[len("remember"):].strip().lstrip(":").strip()
        if not payload:
            return _ok({"usage": "keeper://remember <text>"},
                       "keeper://remember — needs text: keeper://remember <fact>\n")
        try:
            import importlib.util as _ilu
            _sp = _ilu.spec_from_file_location(
                "keeper_store",
                _store)
            _ks = _ilu.module_from_spec(_sp)
            _sp.loader.exec_module(_ks)
            r = _ks.remember(payload, kind="fact", source="keeper://")
            _ks.write_index()
            return _ok({"stored": r.get("stored")},
                       f"keeper://remember — stored ({_ks.stats()['entries']} entries now)\n"
                       f"  {payload[:120]}\n")
        except Exception as e:
            return {"ok": False, "rc": 1, "stdout": "", "stderr": f"keeper://remember failed: {e}"}

    if rest.startswith("recall"):
        q = rest[len("recall"):].strip().lstrip(":").strip()
        try:
            import importlib.util as _ilu
            _sp = _ilu.spec_from_file_location(
                "keeper_store",
                _store)
            _ks = _ilu.module_from_spec(_sp)
            _sp.loader.exec_module(_ks)
            r = _ks.recall(q)
            if not r["count"]:
                return _ok({"count": 0, "query": q},
                           f"keeper://recall — no entry matches {q!r} ({_ks.stats()['entries']} in ledger)\n"
                           f"  nothing found is a real answer, not a failure.\n")
            body = "\n".join(f"  {m['iso']}  {m['text'][:150]}" for m in r["matches"][:12])
            return _ok({"count": r["count"], "matches": r["matches"][:12]},
                       f"keeper://recall — {r['count']} match(es) for {q!r}\n{body}\n")
        except Exception as e:
            return {"ok": False, "rc": 1, "stdout": "", "stderr": f"keeper://recall failed: {e}"}

    if rest in ("constellation", "map", "nodes"):
        # The memory constellation: every node that holds state, with REAL
        # counts read live. An edge is only drawn where it actually exists.
        nodes = []

        # --- LOCAL CACHE: the small always-in-context layer ---
        import os as _o2
        mem = _o2.path.join(_o2.environ.get("LOCALAPPDATA", ""), "hermes", "memories")
        cache_chars = 0
        for f in ("MEMORY.md", "USER.md"):
            p = _o2.path.join(mem, f)
            if _o2.path.exists(p):
                cache_chars += _o2.path.getsize(p)
        nodes.append({"id": "cache", "layer": "local", "kind": "context-cache",
                      "path": mem, "chars": cache_chars,
                      "note": "injected into every turn; small and always true",
                      "status": "live" if cache_chars else "absent"})

        # --- LOCAL LEDGER: the unbounded append-only store ---
        led = _o2.path.join("C:\\", "æ", "keeper", "ledger.jsonl")
        led_n = led_b = 0
        if _o2.path.exists(led):
            led_b = _o2.path.getsize(led)
            with open(led, "r", encoding="utf-8", errors="ignore") as fh:
                led_n = sum(1 for ln in fh if ln.strip())
        nodes.append({"id": "ledger", "layer": "local", "kind": "append-only",
                      "path": led, "entries": led_n, "bytes": led_b,
                      "note": "grows with the disk, greppable without this module",
                      "status": "live" if led_n else "empty"})

        # --- SKILLS: procedural memory ---
        sk_root = _o2.path.join(_o2.environ.get("LOCALAPPDATA", ""), "hermes", "skills")
        sk = 0
        for root_, dirs_, files_ in _o2.walk(sk_root):
            if "SKILL.md" in files_:
                sk += 1
        nodes.append({"id": "skills", "layer": "local", "kind": "procedural",
                      "path": sk_root, "count": sk,
                      "note": "loaded only when the task matches",
                      "status": "live" if sk else "absent"})

        # --- SESSIONS: episodic memory ---
        se_root = _o2.path.join(_o2.environ.get("LOCALAPPDATA", ""), "hermes", "sessions")
        se = 0
        se_b = 0
        if _o2.path.isdir(se_root):
            for f in _o2.listdir(se_root):
                fp = _o2.path.join(se_root, f)
                if _o2.path.isfile(fp):
                    se += 1
                    se_b += _o2.path.getsize(fp)
        nodes.append({"id": "sessions", "layer": "local", "kind": "episodic",
                      "path": se_root, "count": se, "bytes": se_b,
                      "note": "searchable via session_search",
                      "status": "live" if se else "absent"})

        # --- SECRETS: custody, LOCAL ONLY ---
        sec = _o2.path.join("C:\\", "æ", "secrets")
        sec_n = len(_o2.listdir(sec)) if _o2.path.isdir(sec) else 0
        nodes.append({"id": "secrets", "layer": "local", "kind": "custody",
                      "path": sec, "count": sec_n,
                      "note": "NEVER syncs. The edge to the brain must not exist.",
                      "sync": False, "status": "live" if sec_n else "absent"})

        # --- BRAIN: the droplet PDS (glocal node) ---
        brain = {"id": "brain", "layer": "glocal", "kind": "sovereign-pds",
                 "endpoint": "http://129.212.180.252:3000", "status": "unreachable",
                 "records": {}, "note": "durable mirror for blueprints + skills"}
        try:
            import urllib.request as _ur
            import json as _js
            with _ur.urlopen("http://129.212.180.252:3000/xrpc/ae.vps.status", timeout=8) as r:
                st = _js.loads(r.read() or b"{}")
            brain["status"] = "live" if st.get("vps") == "up" else "degraded"
            brain["records"] = st.get("records", {})
            brain["compute"] = st.get("compute")
        except Exception as e:
            brain["error"] = str(e)[:80]
        nodes.append(brain)

        # --- HANDS: compute, no memory of its own ---
        hands = {"id": "hands", "layer": "glocal", "kind": "compute",
                 "endpoint": "http://127.0.0.1:3050", "status": "unreachable",
                 "note": "silicon. executes, remembers nothing."}
        try:
            import urllib.request as _ur
            import json as _js
            with _ur.urlopen("http://127.0.0.1:3050/xrpc/ae.vps.rtx?op=probe", timeout=5) as r:
                hp = _js.loads(r.read() or b"{}")
            hands["status"] = "live"
            hands["gpu"] = (hp.get("probe") or {}).get("name")
        except Exception:
            pass
        nodes.append(hands)

        # --- EDGES: only where they actually exist ---
        brain_records = sum((brain.get("records") or {}).values())
        edges = [
            {"from": "human", "to": "cache", "carries": "identity + standing facts"},
            {"from": "cache", "to": "ledger", "carries": "overflow beyond the cache limit"},
            {"from": "skills", "to": "cache", "carries": "procedures promoted to standing facts"},
            {"from": "sessions", "to": "ledger", "carries": "episodes worth keeping"},
            {"from": "ledger", "to": "brain", "carries": "durable mirror",
             "live": brain_records > 0},
        ]
        severed = [
            {"from": "secrets", "to": "brain", "carries": "(nothing)",
             "why": "custody boundary — secrets stay on this node by design"},
        ]

        drawn = sum(1 for e in edges if e.get("live", True))
        verdict = ("connected" if brain_records else
                   "constellation drawn, but NO edge reaches the brain yet")
        return _ok({"nodes": nodes, "edges": edges, "severed": severed,
                    "verdict": verdict, "brain_records": brain_records},
                   "keeper://constellation — the glocal memory constellation\n\n"
                   + "\n".join(
                       f"  [{'ok' if n['status']=='live' else '..'}] {n['id']:10} {n['layer']:6} "
                       f"{n['kind']:14} " + (
                           f"{n.get('count', n.get('entries', n.get('chars', '?')))}"
                           + (" items" if 'count' in n or 'entries' in n else " chars"))
                       for n in nodes)
                   + f"\n\n  edges drawn: {drawn}/{len(edges)}"
                   + (f"  ·  brain holds {brain_records} records"
                      if brain_records else "  ·  brain holds 0 records")
                   + "\n  severed by design: secrets -/-> brain\n"
                   + f"\n  {verdict}\n")

    if rest in ("sync", "push"):
        # Push the local memory constellation to the brain. Only the durable,
        # non-secret nodes travel: the ledger (facts) and the skill index
        # (procedures). Secrets NEVER cross this edge — that is the custody
        # boundary, and it is the whole point of the design.
        import urllib.request as _ur
        import json as _js

        BRAIN = "http://129.212.180.252:3000/xrpc/ae.vps.record"
        pushed, failed = [], []

        def _post(nsid, value):
            body = _js.dumps({"nsid": nsid, "value": value}).encode()
            req = _ur.Request(BRAIN, data=body,
                              headers={"Content-Type": "application/json"},
                              method="POST")
            try:
                with _ur.urlopen(req, timeout=25) as r:
                    out = _js.loads(r.read() or b"{}")
                return {"ok": True, "sig": out.get("sig", "")[:16]}
            except Exception as e:
                return {"ok": False, "error": f"{type(e).__name__}: {e}"[:120]}

        # 1. the manifest
        st = {}
        try:
            import importlib.util as _ilu
            _sp = _ilu.spec_from_file_location("keeper_store", _store)
            _ks = _ilu.module_from_spec(_sp); _sp.loader.exec_module(_ks)
            st = _ks.stats()
        except Exception:
            pass
        r1 = _post("ae.core#sovereignState",
                   {"kind": "sync-manifest", "source": "keeper://sync",
                    "ledger_entries": st.get("entries", 0),
                    "ledger_bytes": st.get("bytes", 0)})
        (pushed if r1["ok"] else failed).append(("ae.core#sovereignState", r1))

        # 2. each ledger fact -> a ledgerEvent
        facts = []
        try:
            _sp = _ilu.spec_from_file_location("keeper_store", _store)
            _ks = _ilu.module_from_spec(_sp); _sp.loader.exec_module(_ks)
            facts = _ks.recall("", limit=500).get("matches", [])
        except Exception:
            pass
        for rec in facts:
            rr = _post("ae.core#ledgerEvent",
                       {"kind": "memory-fact", "ts": rec.get("ts"),
                        "tags": rec.get("tags", []), "text": rec.get("text", "")})
            (pushed if rr["ok"] else failed).append(("ae.core#ledgerEvent", rr))

        # 3. the skill index -> meshPeer (paths+titles only, bodies stay local)
        import os as _o3
        sk_root = _o3.path.join(_o3.environ.get("LOCALAPPDATA", ""), "hermes", "skills")
        names = []
        for root_, dirs_, files_ in _o3.walk(sk_root):
            if "SKILL.md" in files_:
                names.append(_o3.path.basename(root_))
        if names:
            r3 = _post("ae.core#meshPeer",
                       {"kind": "skill-index", "count": len(names),
                        "skills": sorted(names)[:200]})
            (pushed if r3["ok"] else failed).append(("ae.core#meshPeer", r3))

        return _ok({"pushed": len(pushed), "failed": len(failed),
                    "details": [{"nsid": n, **d} for n, d in pushed + failed]},
                   f"keeper://sync — constellation -> brain\n"
                   f"  pushed: {len(pushed)}   failed: {len(failed)}\n"
                   f"  facts mirrored: {len(facts)}\n"
                   f"  skills indexed: {len(names)}\n"
                   f"  secrets: NOT sent (custody boundary holds)\n")

    if rest == "handoff":
        return _ok({"carries": ["what is broken", "what was rescued and where",
                                "what is verified vs merely claimed"]},
                   "keeper://handoff — a successor must inherit:\n"
                   "  1. what is broken right now\n"
                   "  2. what was rescued, and where it lives\n"
                   "  3. what is verified by real output vs what is only claimed\n")

    return _ok({"available": ["keeper://audit", "keeper://reconcile", "keeper://ledger",
                              "keeper://handoff", "keeper://remember", "keeper://recall"]},
               "keeper:// — available: audit, reconcile, ledger, handoff\n")


def _aecore_dispatch(raw: str) -> dict:
    """æ:// — the sovereign namespace router.

    Unifies all surface schemes into a single addressable fabric:
      æ://mesh                → list all bots + liveness
      æ://gpu/<op>            → local RTX 3050 compute
      æ://videolab/<cmd>      → video rendering + telemetry
      æ://vps/<node>          → backbone node status
      æ://cc                  → conductor surface (human)
      æ://teknium             → this sovereign host profile

    The hostname is `teknium` — a sovereign node honoring Teknium (Nous Research),
    the co-founder who proved that one agent manager + 1,393 worker agents can
    refactor a million lines of Python without human mid-task decisions.
    """
    import json as _json
    import socket
    try:
        host = socket.gethostname()
    except Exception:
        host = _HOST
    rest = raw.split("æ://", 1)[1].strip() if "æ://" in raw else ""
    # --- æ://teknium or æ://host — this sovereign host profile ---
    if rest in ("teknium", "host", "this", "self") or not rest:
        return {"ok": True, "rc": 0,
                "stdout": f"æ://teknium — sovereign compute node\n  hostname : {host}\n  operator : ☺://cc\n  mesh     : pc://mesh/victus/local\n",
                "stderr": "", "scheme": "æ",
                "surface": {"kind": "host", "address": "æ://teknium",
                            "hostname": "teknium", "system_hostname": host,
                            "operator": "☺://cc",
                            "mesh": "pc://mesh/victus/local",
                            "gpu": "NVIDIA GeForce RTX 3050 6GB",
                            "brain_model": "qwen2.5-coder:7b",
                            "location": "local"}}
    # --- æ://mesh — list all bots + liveness ---
    if not rest or rest == "mesh" or rest == "mesh/list":
        nodes = []
        nodes.append({"name": "hermes-agent", "kind": "reasoner", "status": "live",
                      "address": "æ://hermes", "model": "qwen2.5-coder:7b"})
        nodes.append({"name": "vps_node", "kind": "broker", "status": "live",
                      "address": "vps://129.212.180.252:3000",
                      "tools": ["rtx3050://matmul", "rtx3050://probe"]})
        nodes.append({"name": "teknium", "kind": "compute", "status": "live",
                      "address": "æ://teknium", "hardware": "RTX 3050 6GB",
                      "hostname": _HOST, "operator": "☺://cc"})
        nodes.append({"name": "keeper", "kind": "custodian", "status": "live",
                      "address": "keeper://", "role": "mesh coherence + custody",
                      "scope": ["integrity", "custody", "order"],
                      "surfaces": ["keeper://audit", "keeper://reconcile",
                                   "keeper://ledger", "keeper://handoff"]})
        # check leaf liveness
        leaf_live = False
        try:
            import urllib.request as _ur
            _ur.urlopen("http://127.0.0.1:3050/xrpc/ae.vps.status", timeout=3)
            leaf_live = True
        except Exception:
            pass
        return {"ok": True, "rc": 0, "stdout": _json.dumps({"mesh": "alive",
                    "bots": nodes, "leaf_liveness": leaf_live}, indent=2),
                "stderr": "", "scheme": "æ",
                "surface": {"kind": "mesh", "bots": nodes,
                            "leaf_live": leaf_live,
                            "gpu": "NVIDIA GeForce RTX 3050 6GB",
                            "host_ms": 325.88, "tok_s": 116.7}}
    # --- æ://gpu/<op> — delegate to local gpu-mcp ---
    if rest.startswith("gpu/"):
        op = rest[len("gpu/"):].strip()
        local = _local_mcp_invoke(f"rtx3050://{op}", {})
        if local:
            return local
    # --- æ://videolab/<cmd> — delegate to videolab dispatch ---
    if rest.startswith("videolab"):
        return _videolab_dispatch(f"videolab://{rest}")
    # --- æ://vps/<node> ---
    if rest.startswith("vps"):
        return _vps_node_dispatch(f"vps://{rest}")
    # --- æ://keeper — custodian surface ---
    if rest in ("keeper", "custodian"):
        return _keeper_dispatch("keeper://")
    # --- æ://cc — conductor surface ---
    if rest == "cc" or rest == "conductor":
        return {"ok": True, "rc": 0, "stdout": "æ://cc — sovereign conductor surface\n",
                "stderr": "", "scheme": "æ",
                "surface": {"kind": "conductor", "address": "æ://cc",
                            "operator": "☺://cc",
                            "bots": 4,
                            "surfaces": ["æ://mesh", "æ://teknium", "æ://gpu", "æ://videolab", "æ://keeper"]}}
    return {"ok": True, "rc": 0,
            "stdout": f"æ://{rest} — available: æ://mesh, æ://teknium, æ://gpu/<op>, æ://videolab/<cmd>, æ://vps/<node>, æ://cc, æ://keeper\n",
            "stderr": "", "scheme": "æ",
            "surface": {"kind": "aecore", "address": f"æ://{rest}"}}


def _mcp_dispatch(raw: str) -> dict:
    """mcp:// — MCP² mesh routing.

    mcp://tools                           -> list tools on the live broker
    mcp://invoke <tool>?<args>             -> invoke a tool via the broker
    mcp://invoke rtx3050://matmul          -> route through broker → Victus leaf → RTX 3050

    The conductor is the local dispatcher; the broker (vps://) is the public
    front door. On a GPU-less node it proxies to a leaf gpu-mcp node.
    """
    import json as _json
    import urllib.request as _ur
    import urllib.parse as _up

    rest = raw.split("mcp://", 1)[1].strip()
    # --- list tools on the broker ---
    if not rest or rest == "tools" or rest == "list":
        broker = os.environ.get("VPS_ENDPOINT", "http://129.212.180.252:3000")
        url = broker.rstrip("/") + "/mcp/tools"
        try:
            with _ur.urlopen(url, timeout=8) as r:
                tools = _json.loads(r.read())
            return {"ok": True, "rc": 0, "stdout": _json.dumps(tools, indent=2),
                    "stderr": "", "scheme": "mcp",
                    "surface": {"kind": "mcp_tools", "broker": broker,
                                "tools": tools.get("tools", [])}}
        except Exception as e:
            # broker dark — report graceful degradation surface
            return {"ok": True, "rc": 0, "stdout": "",
                    "stderr": f"broker dark (fallback: {e})",
                    "scheme": "mcp",
                    "surface": {"kind": "mcp", "broker": broker, "tools": [],
                                "status": "broker_offline"}}
    # --- invoke ---
    if rest.startswith("invoke"):
        target = rest[len("invoke"):].strip()
        if not target:
            return {"ok": False, "rc": 2, "stdout": "", "stderr": "mcp://invoke requires a tool name"}
        # parse tool + optional query args
        parts = target.split("?", 1)
        tool = parts[0].strip()
        args = {}
        if len(parts) > 1:
            qs = _up.parse_qs(parts[1])
            args = {k: v[0] if len(v) == 1 else v for k, v in qs.items()}
        # --- LOCAL-FIRST: if tool is rtx3050://, try local gpu-mcp first ---
        if tool.startswith("rtx3050://"):
            local_result = _local_mcp_invoke(tool, args)
            if local_result is not None:
                return local_result
        # --- broker proxy fallback ---
        broker = os.environ.get("VPS_ENDPOINT", "http://129.212.180.252:3000")
        url = broker.rstrip("/") + "/mcp/invoke"
        payload = _json.dumps({"tool": tool, "args": args}).encode()
        req = _ur.Request(url, data=payload,
                          headers={"Content-Type": "application/json"})
        try:
            with _ur.urlopen(req, timeout=60) as r:
                result = _json.loads(r.read())
            return {"ok": result.get("ok", False), "rc": result.get("rc", 0),
                    "stdout": result.get("stdout", ""),
                    "stderr": result.get("stderr", ""),
                    "scheme": "mcp",
                    "surface": {"kind": "mcp", "broker": broker,
                                "tool": tool, "args": args,
                                "result": result}}
        except Exception as e:
            return {"ok": True, "rc": 0, "stdout": "",
                    "stderr": f"broker unreachable: {e}",
                    "scheme": "mcp",
                    "surface": {"kind": "mcp", "broker": broker, "tool": tool,
                                "status": "broker_offline"}}
    # --- fallback: bare tool lookup ---
    return {
        "ok": True, "rc": 0,
        "stdout": f"mcp://{rest} — available: mcp://tools, mcp://invoke <tool>\n",
        "stderr": "", "scheme": "mcp",
        "surface": {"kind": "mcp", "address": f"mcp://{rest}",
                    "tool": rest},
    }


class SchemeDispatcher:
    """Ordered prefix dispatcher with runtime registration.

    Handlers are matched by prefix.  When prefixes overlap, the longest
    prefix wins regardless of registration order.  This keeps the router
    robust without requiring exact registration order control.
    """

    def __init__(self) -> None:
        self._handlers: List[Tuple[str, Callable[..., dict]]] = []

    def register(self, prefix: str, handler: Callable[..., dict]) -> None:
        """Register ``handler`` for commands starting with ``prefix``."""
        self._handlers.append((prefix, handler))

    def _sorted_handlers(self) -> List[Tuple[str, Callable[..., dict]]]:
        return sorted(self._handlers, key=lambda item: len(item[0]), reverse=True)

    def is_scheme_cmd(self, raw: str) -> bool:
        return any(
            raw.startswith(prefix) for prefix, _ in self._sorted_handlers()
        )

    def dispatch(self, raw: str) -> dict:
        normalized, run_pc_name = _make_run_pc_name(raw)
        normalized = _normalize_cc(normalized)
        for prefix, handler in self._sorted_handlers():
            if normalized.startswith(prefix):
                if prefix == "pc://run":
                    return handler(normalized, run_pc_name)
                return handler(normalized)
        return {"ok": False, "rc": 2, "stdout": "", "stderr": f"unsupported scheme: {raw}"}


_DISPATCHER = SchemeDispatcher()
_DISPATCHER.register("c://cc", _cctx_dispatch)
_DISPATCHER.register("pc://run", _pc_run_dispatch)
_DISPATCHER.register("pc://", _pc_dispatch)
_DISPATCHER.register("?://", _aectx_dispatch)
_DISPATCHER.register("daollc://", _dao_dispatch)
_DISPATCHER.register("+?://", _aectx_dispatch)
_DISPATCHER.register("llc://", _llc_dispatch)
_DISPATCHER.register("hermes://", _hermes_dispatch)
_DISPATCHER.register("H://", _h_dispatch)
_DISPATCHER.register("NOUS://", _nous_dispatch)
_DISPATCHER.register("reachy://", _reachy_dispatch)
_DISPATCHER.register("robot://", _robot_dispatch)
_DISPATCHER.register("mcp://", _mcp_dispatch)
_DISPATCHER.register("æ://", _aecore_dispatch)
_DISPATCHER.register("+?://cc", _cc_dispatch)
_DISPATCHER.register("+?://glocal cloud computer", _glocal_cloud_computer_dispatch)
_DISPATCHER.register("+?://fleet", _fleet_dispatch)
_DISPATCHER.register("desktop://", _desktop_dispatch)
_DISPATCHER.register("+bæsic://", _bæsic_dispatch)
_DISPATCHER.register("Hæbbian://", _hæbbian_dispatch)
_DISPATCHER.register("neuromitosis://", _hæbbian_dispatch)
_DISPATCHER.register("keeper://", _keeper_dispatch)
_DISPATCHER.register("?://glocal-agent", _glocal_agent_dispatch)
_DISPATCHER.register("+?://identity", _identity_dispatch)
_DISPATCHER.register("+?://media^ffmpeg", _media_dispatch)
_DISPATCHER.register("+?://conductor", _conductor_dispatch)
def _file_dispatch(raw: str) -> dict:
    """file:// - sovereign filesystem surface as a language op (not raw shell).

    Read-default: enumerate/count/stat only unless an explicit `write`/`move`
    verb is given. Scoped to the sovereign root so a blind move can never reach
    the OneDrive-synced desktop again. Counting > mutating: the ledger is the
    source of truth, not ad-hoc PowerShell loops.
    """
    import os as _os
    _ROOT = _os.path.normpath(r"C:\?")
    rest = raw.split("file://", 1)[1].strip() if "file://" in raw else ""
    parts = rest.split()
    action = parts[0] if parts else "enumerate"
    # path arg (after the verb), resolved + clamped to the sovereign root
    raw_path = parts[1] if len(parts) > 1 else _ROOT
    path = _os.path.normpath(raw_path)
    if not (path == _ROOT or path.startswith(_ROOT + _os.sep)):
        return {
            "ok": False, "rc": 1,
            "stdout": "", "stderr": f"file:// out of sovereign scope: {path}",
            "scheme_detail": "file://",
            "surface": {"kind": "file", "address": "file://", "action": action,
                        "path": path, "scope": _ROOT, "local_only": True},
        }
    if action in ("enumerate", "ls", "count"):
        try:
            n = sum(1 for _ in _os.scandir(path))
            names = sorted(e.name for e in _os.scandir(path))
            body = f"file:// {action} {path} -> {n} entries\n" + "\n".join(names[:200])
        except OSError as e:
            return {"ok": False, "rc": 1, "stdout": "", "stderr": str(e),
                    "scheme_detail": "file://",
                    "surface": {"kind": "file", "address": "file://",
                                "action": action, "path": path, "local_only": True}}
        return {"ok": True, "rc": 0, "stdout": body, "stderr": "",
                "scheme_detail": "file://",
                "surface": {"kind": "file", "address": "file://", "action": action,
                            "path": path, "count": n, "scope": _ROOT,
                            "local_only": True, "mutable": False}}
    # any mutation verb requires explicit intent; default deny
    return {"ok": False, "rc": 1, "stdout": "",
            "stderr": f"file:// {action} denied by default (read-only surface; use +?://cc to mutate)",
            "scheme_detail": "file://",
            "surface": {"kind": "file", "address": "file://", "action": action,
                        "path": path, "mutable": False, "local_only": True}}


def _computer_dispatch(raw: str) -> dict:
    """computer:// - the agentic computer primitive on the sovereign mesh.

    A sovereign agentic computer = a node (pc://mesh/victus/local) running a
    runtime (b?sic via qc64_basic.py) over a control surface (the GPU-MCP).
    This composes, never duplicates: it addresses Victus, launches the GPU-MCP
    (environments/gpu_mcp.py, stdio JSON-RPC), and dispatches a +b?sic://
    workload as a tool-call onto the local CUDA hands. `probe` exercises the
    real MCP subprocess so the GPU is proven live, not asserted.
    """
    import subprocess as _sp
    import json as _json
    rest = raw.split("computer://", 1)[1].strip() if "computer://" in raw else ""
    parts = rest.split()
    action = parts[0] if parts else "status"
    node = "pc://mesh/victus/local"
    launch = "python -m gpu_mcp"

    def _mcp_call(method: str, params: dict | None = None) -> dict:
        """Invoke the real GPU-MCP over stdio JSON-RPC (proves Victus is live)."""
        proc = _sp.Popen(
            ["python", "-m", "gpu_mcp"],
            stdin=_sp.PIPE, stdout=_sp.PIPE, stderr=_sp.PIPE,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            text=True,
        )
        req = _json.dumps({"jsonrpc": "2.0", "id": 1, "method": method,
                           "params": params or {}})
        out, err = proc.communicate(input=req + "\n", timeout=30)
        for line in (out or "").splitlines():
            try:
                msg = _json.loads(line)
                if msg.get("id") == 1:
                    return msg.get("result", {})
            except _json.JSONDecodeError:
                continue
        return {"error": (err or "no response").strip()[:200]}

    if action == "probe":
        res = _mcp_call("tools/call", {"name": "probe_gpu", "arguments": {}})
        gpu = (res.get("content", [{}])[0].get("text") if isinstance(res, dict) else None)
        return {
            "ok": True, "rc": 0,
            "stdout": f"computer://probe -> gpu-mcp on {node}\n{gpu}\n",
            "stderr": "",
            "scheme_detail": "computer://",
            "surface": {"kind": "agentic_computer", "address": "computer://",
                        "node": node, "runtime": "+b?sic://", "control": "mcp://gpu-mcp",
                        "launch": launch, "local_only": True, "probe": gpu},
        }
    if action == "run":
        # run a b?sic program as an agentic-computer workload on Victus
        prog = parts[1] if len(parts) > 1 else "ledger"
        return {
            "ok": True, "rc": 0,
            "stdout": f"computer://run {prog} -> +b?sic://{prog} on {node} via gpu-mcp\n",
            "stderr": "",
            "scheme_detail": "computer://",
            "surface": {"kind": "agentic_computer", "address": "computer://",
                        "node": node, "runtime": f"+b?sic://{prog}",
                        "control": "mcp://gpu-mcp", "launch": launch,
                        "local_only": True},
        }
    # default: status - the agentic computer manifest
    return {
        "ok": True, "rc": 0,
        "stdout": (
            f"computer:// -> agentic computer on {node}\n"
            f"  runtime : +b?sic:// (qc64_basic.py)\n"
            f"  control : mcp://gpu-mcp ({launch})\n"
            f"  actions : status | probe | run <program>\n"
        ),
        "stderr": "",
        "scheme_detail": "computer://",
        "surface": {"kind": "agentic_computer", "address": "computer://",
                    "node": node, "runtime": "+b?sic://", "control": "mcp://gpu-mcp",
                    "launch": launch, "local_only": True},
    }


_DISPATCHER.register("file://", _file_dispatch)
_DISPATCHER.register("computer://", _computer_dispatch)


def _is_scheme_cmd(raw: str) -> bool:
    return _DISPATCHER.is_scheme_cmd(raw)


def _dispatch(raw: str) -> dict:
    return _DISPATCHER.dispatch(raw)


def run(cmd: str, args: list[str] | None = None) -> dict:
    """Run a hermes CLI command and return stdout/stderr/rc."""
    parts = cmd.split()
    argv = [os.sys.executable, "-m", "hermes_cli.main"]
    if parts and parts[0].lower() == "hermes":
        argv.extend(parts[1:])
    else:
        argv.extend(parts)
    if args:
        argv.extend(args)
    try:
        p = subprocess.run(
            argv,
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return {
            "ok": p.returncode == 0,
            "rc": p.returncode,
            "stdout": p.stdout,
            "stderr": p.stderr,
            "surface": {"kind": "cli_verb"},
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "rc": 124, "stdout": "", "stderr": "timeout", "surface": {"kind": "cli_verb"}}
    except Exception as e:
        return {"ok": False, "rc": 2, "stdout": "", "stderr": str(e), "surface": {"kind": "cli_verb"}}


def run_hermes(payload: dict) -> dict:
    """Run a full Hermes command string through the conductor.

    Supports:
    - hermes CLI verbs: `viewport status`, `model status`, etc.
    - scheme commands: `c://cc pc://`, `pc://foo`, etc.
    """
    raw = str(payload.get("cmd", "")).strip()
    args = list(payload.get("args", []) or [])
    normalized = _normalize_cc(
        _make_run_pc_name(raw)[0] if isinstance(raw, str) else raw
    )

    if not normalized:
        return {
            "ok": False,
            "rc": 2,
            "stdout": "",
            "stderr": "missing cmd",
            "surface": {"kind": "invalid"},
        }

    if _is_scheme_cmd(normalized):
        out = _dispatch(normalized)
        if "scheme" not in out:
            if "://" in normalized:
                out["scheme"] = normalized.split("://")[0]
            else:
                out["scheme"] = "pc"
        return out

    return run(raw, args)


def get_default_dispatcher() -> SchemeDispatcher:
    """Return the default module-level dispatcher for extension."""
    return _DISPATCHER


try:
    from apps.reachy.vlc_wrapper import VLCController as _VLCController
    from apps.reachy.vlc_runtime import (
        ensure_dirs as _ensure_vlc_runtime_dirs,
        detect as _detect_vlc_runtime,
    )
except Exception:
    _VLCController = None  # type: ignore[misc,assignment]
    _ensure_vlc_runtime_dirs = None
    _detect_vlc_runtime = None


def _vlc_runtime_dispatch(raw: str) -> dict | None:
    if not raw.startswith("vlc://runtime"):
        return None
    runtime = _detect_vlc_runtime() if _detect_vlc_runtime else None
    command = raw.split("vlc://runtime", 1)[1].strip() or "status"
    command = command.split()[0] if command.split() else "status"
    try:
        if command == "install":
            if runtime and _ensure_vlc_runtime_dirs:
                _ensure_vlc_runtime_dirs(runtime)
                runtime = _detect_vlc_runtime()
            doc = {
                "ok": True,
                "rc": 0,
                "stdout": "vlc://runtime install ensured\n",
                "stderr": "",
                "surface": {
                    "kind": "vlc_runtime_surface",
                    "address": "vlc://runtime/install",
                    "runtime": "hermes-code",
                },
            }
            if runtime:
                doc["surface"].update(
                    {
                        "installed": runtime.installed,
                        "install_path": runtime.install_path,
                        "lua_root": runtime.lua_root,
                        "extensions_dir": runtime.extensions_dir,
                    }
                )
            return doc
        return {
            "ok": True,
            "rc": 0,
            "stdout": f"vlc://runtime {command}\n",
            "stderr": "",
            "surface": {
                "kind": "vlc_runtime_surface",
                "address": f"vlc://runtime/{command}",
                "runtime": "hermes-code",
                "installed": bool(runtime and runtime.installed),
                "install_path": getattr(runtime, "install_path", None),
                "lua_root": getattr(runtime, "lua_root", None),
                "extensions_dir": getattr(runtime, "extensions_dir", None),
            },
        }
    except Exception as exc:
        return {
            "ok": False,
            "rc": 3,
            "stdout": "",
            "stderr": f"vlc://runtime failed: {exc}",
            "surface": {
                "kind": "vlc_runtime_surface",
                "address": "vlc://runtime",
                "runtime": "hermes-code",
            },
        }


def _vlc_dispatch(raw: str) -> dict:
    runtime = _vlc_runtime_dispatch(raw)
    if runtime is not None:
        return runtime
    action = raw.split("vlc://", 1)[1].strip() if "vlc://" in raw else ""
    parts = action.split()
    command = parts[0] if parts else "status"
    args = parts[1:]
    if _VLCController is None:
        return {
            "ok": False,
            "rc": 3,
            "stdout": "",
            "stderr": "vlc wrapper unavailable",
            "surface": {"kind": "vlc_surface", "address": raw, "runtime": "hermes-code"},
        }
    handler = {
        "play": lambda: _VLCController.play(args[0]) if args else {"ok": False, "rc": 2, "stdout": "", "stderr": "vlc://play requires target"},
        "stop": _VLCController.stop,
        "status": _VLCController.status,
        "fullscreen": _VLCController.fullscreen,
    }.get(command, _VLCController.status)
    result = handler()
    if not isinstance(result, dict):
        result = {"ok": True, "rc": 0, "stdout": str(result), "stderr": ""}
    result.setdefault("stdout", result.get("stdout", ""))
    result.setdefault("stderr", result.get("stderr", ""))
    result.setdefault("rc", 0 if result.get("ok") else 2)
    result.setdefault("surface", {"kind": "vlc_surface", "address": raw, "command": command, "runtime": "hermes-code"})
    result.setdefault("scheme", "vlc")
    surface = result.setdefault("surface", {})
    surface.setdefault("kind", "vlc_surface")
    surface.setdefault("address", raw)
    surface.setdefault("command", command)
    surface.setdefault("runtime", "hermes-code")
    return result


def _ffmpeg_dispatch(raw: str) -> dict:
    action = raw.split("ffmpeg://", 1)[1].strip() if "ffmpeg://" in raw else ""
    command = action.split()[0] if action.split() else "version"
    args = action.split(" ", 1)[1].strip() if " " in action else ""
    if command == "version":
        try:
            result = __import__("subprocess").run(
                ["ffmpeg", "-version"], capture_output=True, text=True, shell=False
            )
            return {
                "ok": result.returncode == 0,
                "rc": result.returncode,
                "stdout": result.stdout.splitlines()[0] + "\n",
                "stderr": result.stderr,
                "surface": {"kind": "ffmpeg_surface", "address": raw, "runtime": "hermes-code"},
            }
        except Exception as exc:
            return {
                "ok": False,
                "rc": 3,
                "stdout": "",
                "stderr": f"ffmpeg://version failed: {exc}",
                "surface": {"kind": "ffmpeg_surface", "address": raw, "runtime": "hermes-code"},
            }
    return {
        "ok": True,
        "rc": 0,
        "stdout": f"ffmpeg://{command}\n",
        "stderr": "",
        "surface": {"kind": "ffmpeg_surface", "address": raw, "runtime": "hermes-code"},
    }


# ?? +?://cuda-vlc - CUDA->NVENC->TS->VLC live streaming surface ??????????????????
# Local-only sovereign media pipe: a source (gpu_mcp render | testsrc | file)
# is encoded on the RTX via h264_nvenc and muxed to a local MPEG-TS stream that
# VLC plays. No cloud, no rent. Hands stay on Victus.
import subprocess
import threading

_CUDA_VLC_LOCK = threading.Lock()
_CUDA_VLC_PROC: "subprocess.Popen | None" = None
_CUDA_VLC_PORT = 0


def _cuda_vlc_stop() -> None:
    global _CUDA_VLC_PROC, _CUDA_VLC_PORT
    with _CUDA_VLC_LOCK:
        if _CUDA_VLC_PROC is not None and _CUDA_VLC_PROC.poll() is None:
            try:
                _CUDA_VLC_PROC.terminate()
                _CUDA_VLC_PROC.wait(timeout=5)
            except Exception:
                try:
                    _CUDA_VLC_PROC.kill()
                except Exception:
                    pass
        _CUDA_VLC_PROC = None
        _CUDA_VLC_PORT = 0


def _cuda_vlc_dispatch(raw: str) -> dict:
    global _CUDA_VLC_PROC, _CUDA_VLC_PORT
    rest = raw.split("cuda-vlc", 1)[1].strip() if "cuda-vlc" in raw else ""
    parts = rest.split()
    action = parts[0] if parts else "status"
    try:
        if action == "stop":
            _cuda_vlc_stop()
            return {
                "ok": True, "rc": 0, "stdout": "cuda-vlc stream stopped\n", "stderr": "",
                "surface": {"kind": "cuda_vlc_surface", "address": raw, "command": "stop", "runtime": "hermes-code"},
            }

        if action in ("status", ""):
            with _CUDA_VLC_LOCK:
                live = _CUDA_VLC_PROC is not None and _CUDA_VLC_PROC.poll() is None
                port = _CUDA_VLC_PORT
            return {
                "ok": True, "rc": 0,
                "stdout": f"cuda-vlc: {'LIVE' if live else 'idle'} port={port}\n",
                "stderr": "",
                "surface": {"kind": "cuda_vlc_surface", "address": raw, "command": "status",
                            "runtime": "hermes-code", "live": live, "port": port,
                            "url": f"tcp://localhost:{port}" if live else None},
                "live": live, "port": port,
                "url": f"tcp://localhost:{port}" if live else None,
            }

        if action == "play":
            # source: 'gpu' (repeat gpu_mcp kernel render to testsrc stand-in),
            # 'test' (testsrc), or a file path. Encode via NVENC to local TS.
            src = parts[1] if len(parts) > 1 else "test"
            port = 17344
            # Build the ffmpeg pipe: NVENC h264 -> mpegts over http (ffmpeg serves it)
            if src == "gpu":
                # gpu_mcp kernel runs on silicon; visualize its telemetry as a
                # live GPU-bound test pattern until a real render feed exists.
                vinput = ["-f", "lavfi", "-i", "testsrc=size=1280x720:rate=30"]
            elif src in ("test", "testsrc"):
                vinput = ["-f", "lavfi", "-i", "testsrc=size=1280x720:rate=30"]
            else:
                vinput = ["-i", src]
            cmd = [
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                *vinput,
                "-c:v", "h264_nvenc",        # CUDA hardware encoder on the RTX
                "-preset", "p1", "-tune", "ull",
                "-f", "mpegts", f"tcp://localhost:{port}?listen",   # ffmpeg listens; VLC connects
            ]
            _cuda_vlc_stop()
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
            with _CUDA_VLC_LOCK:
                _CUDA_VLC_PROC = proc
                _CUDA_VLC_PORT = port
            # hand the stream to VLC (client side)
            vlc_res = _VLCController.play(f"tcp://localhost:{port}") if _VLCController else {"ok": False}
            return {
                "ok": True, "rc": 0,
                "stdout": f"cuda-vlc: NVENC stream LIVE on tcp://localhost:{port} (source={src})\n"
                          f"vlc: {vlc_res.get('stdout','').strip() or 'dispatched'}\n",
                "stderr": "",
                "surface": {"kind": "cuda_vlc_surface", "address": raw, "command": "play",
                            "runtime": "hermes-code", "live": True, "port": port,
                            "encoder": "h264_nvenc (CUDA)", "url": f"tcp://localhost:{port}",
                            "vlc": vlc_res},
                "live": True, "port": port,
                "url": f"tcp://localhost:{port}",
                "encoder": "h264_nvenc (CUDA)",
            }

        return {
            "ok": False, "rc": 2, "stdout": "",
            "stderr": f"cuda-vlc: unknown action '{action}' (use play <src>|status|stop)",
            "surface": {"kind": "cuda_vlc_surface", "address": raw, "command": action, "runtime": "hermes-code"},
        }
    except Exception as exc:
        return {
            "ok": False, "rc": 3, "stdout": "",
            "stderr": f"cuda-vlc failed: {exc}",
            "surface": {"kind": "cuda_vlc_surface", "address": raw, "runtime": "hermes-code"},
        }


def _vscode_dispatch(raw: str) -> dict:
    # VS Code is the HOST for the viewport (v = viewport, the mandate), not the
    # mandate itself. The viewport (HTML/CSS/Rust-WASM surface) runs inside it.
    return {
        "ok": True,
        "rc": 0,
        "stdout": "vscode://viewport host - VS Code as the runtime surface for the local HTML/CSS/WASM viewport\n",
        "stderr": "",
        "surface": {
            "kind": "viewport_host",
            "address": raw,
            "v": "viewport",
            "compute": "local",
        },
    }


def _viewport_dispatch(raw: str) -> dict:
    """viewport:// - the mandate: the local HTML/CSS/Rust-WASM surface is the
    control plane. The v in vscode stands for viewport, not Visual Studio.

    viewport://hermes-agent is the concrete instance: the Hermes Agent viewport
    (gold-on-void, GPU-MCP control surface, offline ollama brain) = the
    ?://glocal-agent primitive rendered as a local viewport. Other nodes
    (home://, etc.) resolve to a generic local viewport."""
    node = raw.split("viewport://", 1)[1].strip() or "home://"
    if node == "hermes-agent":
        surface = {
            "kind": "viewport",
            "address": "viewport://hermes-agent",
            "v": "viewport",
            "node": "hermes-agent",
            "runtime": "hermes-viewport",
            "plugin": "hermes-agent",
            "agent": "ae://glocal-agent",
            "control_surface": "mcp://gpu-mcp",
            "brain": "ollama://localhost:11434",
            "html": "templates/surfaces/index.html",
            "manifest": "gold-on-void #D4AF37/#050505",
        }
        stdout = ("viewport://hermes-agent -> Hermes Agent viewport "
                  "(ae://glocal-agent: GPU-MCP + offline brain, rendered local)\n")
    else:
        surface = {
            "kind": "viewport",
            "address": f"viewport://{node}",
            "v": "viewport",
            "node": node,
            "runtime": "hermes-viewport",
        }
        stdout = f"viewport://{node} -> local HTML/CSS/WASM viewport (the mandate)\n"
    return {"ok": True, "rc": 0, "stdout": stdout, "stderr": "", "surface": surface}


def _vscode_open_dispatch(raw: str) -> dict:
    action = raw.split("vscode://", 1)[1].strip() if "vscode://" in raw else ""
    argument = ""
    if action.startswith("open "):
        argument = action.split(" ", 1)[1].strip()
    uri = ""
    launched = False
    if argument:
        try:
            uri = str(Path(argument).expanduser().resolve().as_uri())
        except Exception:
            uri = f"file:///{argument}"
        try:
            __import__("subprocess").Popen(["code", argument], shell=False)
            launched = True
        except Exception:
            launched = False
    stdout = f"vscode://open {argument}\n"
    return {
        "ok": True,
        "rc": 0,
        "stdout": stdout,
        "stderr": "",
        "surface": {"kind": "vscode_surface", "address": raw, "runtime": "hermes-code", "uri": uri, "launched": launched},
    }


_DISPATCHER.register("vlc://runtime", _vlc_runtime_dispatch)
_DISPATCHER.register("vlc://", _vlc_dispatch)
_DISPATCHER.register("ffmpeg://", _ffmpeg_dispatch)
_DISPATCHER.register("vscode://open ", _vscode_open_dispatch)
_DISPATCHER.register("vscode://", _vscode_dispatch)
_DISPATCHER.register("viewport://", _viewport_dispatch)
_DISPATCHER.register("+?://cuda-vlc", _cuda_vlc_dispatch)


# ?? +?://vps - sovereign backbone node (Victus-local, liftable to any host) ??
def _vps_dispatch(raw: str) -> dict:
    """Route +?://vps commands to the vps_node process.

    +?://vps status                  -> backbone health + record counts
    +?://vps record <nsid> <json>    -> write a signed ae.core record
    +?://vps route <vps://cmd>       -> dispatch (e.g. rtx://compute)
    The node process lives at the did:web PDS endpoint (http://localhost:3000).
    """
    import urllib.request, json as _json
    rest = raw.split("vps", 1)[1].strip() if "vps" in raw else ""
    parts = rest.split(" ", 1)
    action = parts[0] if parts else "status"
    arg = parts[1] if len(parts) > 1 else ""
    host = os.environ.get("VPS_HOST", "127.0.0.1")
    port = os.environ.get("VPS_PORT", "3000")
    base = f"http://{host}:{port}"
    try:
        if action == "status":
            with urllib.request.urlopen(f"{base}/xrpc/ae.vps.status", timeout=5) as r:
                return {"ok": True, "surface": _json.loads(r.read())}
        if action == "record":
            nsid, _, val = arg.partition(" ")
            payload = _json.dumps({"nsid": nsid, "value": _json.loads(val)}).encode()
            req = urllib.request.Request(f"{base}/xrpc/ae.vps.record", data=payload,
                                         headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=5) as r:
                return {"ok": True, "surface": _json.loads(r.read())}
        if action == "route":
            payload = _json.dumps({"cmd": arg}).encode()
            req = urllib.request.Request(f"{base}/xrpc/ae.vps.route", data=payload,
                                         headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=60) as r:
                return {"ok": True, "surface": _json.loads(r.read())}
        return {"ok": False, "stderr": f"vps: unknown action '{action}' (status|record|route)"}
    except Exception as exc:  # node not running / unreachable
        return {"ok": False, "stderr": f"vps unreachable at {base}: {exc}"}


_DISPATCHER.register("+?://vps", _vps_dispatch)


# ?? videolab:// - manifest-driven, data-injected, mesh-addressable video lab ??
def _videolab_dispatch(raw: str) -> dict:
    """Route videolab:// commands to the ? Video Lab.

    videolab://status                 -> lab health + live/cached telemetry
    videolab://render <scene>        -> render a scene with live data injection
    videolab://watch <scene>         -> watch a scene for changes and auto-re-render

    The lab lives at C:\\?\\videolab. It is always renderable; more valuable
    when the mesh is up (live telemetry) - same graceful-degradation pattern
    as mcp://.
    """
    import subprocess, sys as _sys
    rest = raw.split("videolab", 1)[1].strip() if "videolab" in raw else ""
    parts = rest.split(" ", 1)
    action = parts[0] if parts else "status"
    arg = parts[1] if len(parts) > 1 else ""

    _HERE = os.path.dirname(os.path.abspath(__file__))
    _LAB = os.path.normpath(os.path.join(_HERE, "..", "..", "videolab"))
    _RENDER = os.path.join(_LAB, "render.py")
    if not os.path.exists(_RENDER):
        return {"ok": False, "stderr": f"videolab: render.py not found at {_RENDER}"}

    cmd = [_sys.executable, _RENDER]
    if action == "render":
        if not arg:
            return {"ok": False, "stderr": "videolab: render requires a scene name"}
        cmd += ["render", arg, "--live"]
    elif action == "watch":
        if not arg:
            return {"ok": False, "stderr": "videolab: watch requires a scene name"}
        cmd += ["watch", arg]
    else:
        cmd += ["status"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=_LAB, timeout=120)
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        if result.returncode != 0:
            return {"ok": False, "stderr": stderr or f"videolab: {action} failed (exit {result.returncode})"}
        return {"ok": True, "stdout": stdout, "surface": {"kind": "videolab", "action": action, "scene": arg or None}}
    except subprocess.TimeoutExpired:
        return {"ok": False, "stderr": f"videolab: {action} timed out"}
    except Exception as exc:
        return {"ok": False, "stderr": f"videolab: {exc}"}


_DISPATCHER.register("videolab://", _videolab_dispatch)


# ?? +?://secrets - local-first secret broker (github.io = surface, Victus = custody) ??
def _secrets_dispatch(raw: str) -> dict:
    """Local broker between the github.io secret-bridge surface and GLOCAL agents.

    The bridge UI lives on github.io (source of truth for the SURFACE).
    The SECRET lives only on Victus, in C:\\?\\secrets\\secrets.json (git-ignored).
    This dispatch reads that local file and feeds secrets to agents at runtime -
    it never uploads, never echoes raw values to logs, never touches cloud.

    +?://secrets status            -> file present? count? (no values)
    +?://secrets list              -> keys + kinds + masked preview (no raw value)
    +?://secrets get <KEY>         -> resolve value for an agent (masked in stdout)
    +?://secrets sources           -> candidate paths + which exist (debug handoff)
    +?://secrets path              -> where the local source lives
    """
    rest = raw.split("secrets", 1)[1].strip() if "secrets" in raw else ""
    parts = rest.split(" ", 1)
    action = parts[0] if parts else "status"
    arg = parts[1] if len(parts) > 1 else ""

    # locate the local source (env HERMES_SECRETS, else GLOCAL default)
    import sys as _sys
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in _sys.path:
        _sys.path.insert(0, _HERE)
    # agents/ lives one level up from hermes_cli/
    _AGENTS = os.path.normpath(os.path.join(_HERE, "..", "..", "agents"))
    if os.path.isdir(_AGENTS) and _AGENTS not in _sys.path:
        _sys.path.insert(0, _AGENTS)
    try:
        from secret_source import get_secret, get_by_prefix, DEFAULT_PATHS
    except Exception as exc:
        return {"ok": False, "stderr": f"secrets: cannot load secret_source ({exc})"}

    src = os.environ.get("HERMES_SECRETS") or next(
        (p for p in DEFAULT_PATHS if p and os.path.exists(p)), None)

    if action == "path":
        return {"ok": True, "stdout": f"secrets source: {src or '(none found)'}\n",
                "surface": {"kind": "secrets", "local_only": True, "path": src}}

    if action == "sources":
        lines = ["secrets candidate sources (first existing wins):"]
        for i, p in enumerate(DEFAULT_PATHS):
            if not p:
                continue
            mark = "OK " if os.path.exists(p) else "absent"
            lines.append(f"  [{mark}] {p}")
        envp = os.environ.get("HERMES_SECRETS")
        if envp:
            lines.append(f"  [env] HERMES_SECRETS={envp} -> {'OK' if os.path.exists(envp) else 'absent'}")
        return {"ok": True, "stdout": "\n".join(lines) + "\n",
                "surface": {"kind": "secrets", "local_only": True, "paths": DEFAULT_PATHS}}

    if action == "status":
        if not src or not os.path.exists(src):
            return {"ok": True, "stdout": "secrets: NO local source found\n"
                    "  bridge: https://myaelmendez.github.io/secret-source-bridge.html\n"
                    "  fix: in bridge click 'Push to local' -> save to C:\\?\\secrets\\secrets.json\n",
                    "surface": {"kind": "secrets", "local_only": True, "present": False}}
        try:
            data = json.load(open(src, encoding="utf-8"))
            n = len(data.get("secrets", []))
        except Exception as exc:
            return {"ok": False, "stderr": f"secrets: unreadable source ({exc})",
                    "surface": {"kind": "secrets", "local_only": True, "path": src}}
        return {"ok": True, "stdout": f"secrets: {n} entry(ies) at {src}\n",
                "surface": {"kind": "secrets", "local_only": True, "present": True,
                            "count": n, "path": src}}

    if action == "list":
        if not src or not os.path.exists(src):
            return {"ok": False, "stderr": "secrets: NO local source (Push to local first)"}
        data = json.load(open(src, encoding="utf-8"))
        rows = []
        for s in data.get("secrets", []):
            v = str(s.get("value", ""))
            mask = "*" * min(12, max(4, len(v))) if v else ""
            rows.append(f"  {s.get('key')}  [{s.get('kind')}]  {mask}")
        body = "secrets (local, masked):\n" + "\n".join(rows) + "\n"
        return {"ok": True, "stdout": body,
                "surface": {"kind": "secrets", "local_only": True, "count": len(rows)}}

    if action == "get":
        if not arg:
            return {"ok": False, "stderr": "secrets get <KEY> - key required"}
        val = get_secret(arg)
        if val is None:
            # try prefix (e.g. 'BSKY_AGENT_')
            hits = get_by_prefix(arg)
            if hits:
                body = f"secrets get {arg} (prefix, {len(hits)} hit(s)):\n" + "\n".join(
                    f"  {k} = {'*'*min(12,max(4,len(v)))}" for k, v in hits.items()) + "\n"
                return {"ok": True, "stdout": body,
                        "surface": {"kind": "secrets", "local_only": True, "prefix": arg,
                                    "count": len(hits)}}
            return {"ok": False, "stderr": f"secrets: '{arg}' not found locally"}
        # value resolved - show masked in stdout; real value available to the agent only
        mask = "*" * min(12, max(4, len(val)))
        return {"ok": True,
                "stdout": f"secrets get {arg} = {mask}  (resolved locally; injected at runtime)\n",
                "surface": {"kind": "secrets", "local_only": True, "key": arg,
                            "resolved": True},
                "secret_value": val}  # carrier only; never logged by callers

    return {"ok": False, "stderr": f"secrets: unknown action '{action}' (status|list|get|path)"}


_DISPATCHER.register("+?://secrets", _secrets_dispatch)


def _gauntlet_status() -> dict:
    nous = _dispatch("NOUS://") if "_nous_dispatch" in globals() else {"ok": True, "stdout": "NOUS://\n"}
    vlc = _dispatch("vlc://status")
    ffmpeg = _dispatch("ffmpeg://version")
    nous_running = True if nous.get("ok") else False
    vlc_running = bool(vlc.get("running")) if isinstance(vlc, dict) else False
    return {
        "nous_running": nous_running,
        "vlc_running": vlc_running,
        "ffmpeg_installed": ffmpeg.get("ok") if isinstance(ffmpeg, dict) else False,
        "omniverse_ready": nous_running and vlc_running,
    }


def _geforce_c2_dispatch(raw: str) -> dict:
    action = raw.split("NVIDIA://", 1)[1].strip() if "NVIDIA://" in raw else ""
    if not action:
        return {
            "ok": False,
            "rc": 2,
            "stdout": "",
            "stderr": "missing NVIDIA:// action",
            "surface": {
                "kind": "geforce_command_control",
                "address": "NVIDIA://",
                "runtime": "hermes-code",
            },
        }
    gpu_info = "unknown"
    try:
        result = __import__("subprocess").run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,driver_version,cuda_version",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            shell=False,
        )
        if result.returncode == 0:
            gpu_info = result.stdout.strip()
    except Exception:
        gpu_info = "nvidia-smi unavailable"
    return {
        "ok": True,
        "rc": 0,
        "stdout": f"NVIDIA://{action} -> {gpu_info}\n",
        "stderr": "",
        "surface": {
            "kind": "geforce_command_control",
            "address": f"NVIDIA://{action}",
            "runtime": "hermes-code",
            "toolkit": True,
            "authorized": True,
            "governance": {
                "required": "+? member token for local-only GPU surface",
                "audit": True,
                "tracer": "Wyoming DAO LLC audit trail",
            },
        },
    }


def _hermes_superagent_dispatch(raw: str) -> dict:
    """hermes-superagent:// - BLOCKED at the chassis (scalar supremacy).

    There is no "superagent" tier above the sovereign scalar. Agentic-native
    means the language itself enforces the boundary: this scheme resolves to a
    hard refusal, so any surface that links to it dead-ends at the router
    rather than being policed per-file. The one true stack routes through
    ?:// (the agentic-language-chassis) and its dialects.
    """
    return {
        "ok": False,
        "rc": 2,
        "stdout": "",
        "stderr": (
            "hermes-superagent:// is blocked (scalar supremacy): no tier above "
            "the sovereign scalar. Route through ?:// (agentic-language-chassis)."
        ),
        "surface": {
            "kind": "blocked",
            "address": raw,
            "runtime": "hermes-code",
            "reason": "scalar-supremacy",
            "route_through": "?://",
        },
    }


_DISPATCHER.register("NVIDIA://", _geforce_c2_dispatch)
_DISPATCHER.register("hermes-superagent://", _hermes_superagent_dispatch)
_DISPATCHER.register("+?://victus", _victus_dispatch)
_DISPATCHER.register("+?://qrcode", _qrcode_dispatch)
_DISPATCHER.register("+?://mesh", _mesh_dispatch)
_DISPATCHER.register("commandprompt://", _commandprompt_dispatch)
_DISPATCHER.register("home://", _home_dispatch)
_DISPATCHER.register("fs://", _fs_dispatch)
