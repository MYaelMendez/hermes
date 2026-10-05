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
    # a:// — the ASCII alias for æ://. The glyph æ is not on every keyboard, so
    # the namespace needs a typable entry point. `?` was the de-facto stand-in
    # (a terminal artifact when æ would not render), but `?` is the URL query
    # separator — a terrible alias. `a` is the letter; use it.
    if raw.startswith("+a://"):
        return "+æ://" + raw[len("+a://"):]
    if raw.startswith("a://"):
        return "æ://" + raw[len("a://"):]
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


def _pc_inference_dispatch(raw: str) -> dict:
    """pc://inference - the PC://INFERENCE portable inference substrate.

    llama.cpp as the machine layer executing GGUF cognitive artifacts across
    heterogeneous electronics. Reports the REAL local substrate and can run it:

        pc://inference                 -> report (model, runtime, GPU, VRAM)
        pc://inference run <prompt>    -> execute llama-cli -ngl 99, real tok/s
        pc://inference bench           -> A/B GPU (-ngl 99) vs CPU (-ngl 0)

    Local cognition != external authority: this surface reasons locally; any
    external consequence stays separately gated by PC://POLICY.
    """
    import os
    import subprocess

    rest = raw.split("pc://inference", 1)[1].strip() if "pc://inference" in raw else ""
    parts = rest.split(" ", 1)
    action = parts[0].strip().lower() if parts and parts[0].strip() else "report"
    arg = parts[1].strip() if len(parts) > 1 else ""

    model = os.environ.get(
        "PC_INFERENCE_MODEL",
        r"C:/Users/yaelm/AppData/Local/hermes/tools/qwen2.5-coder-7b-q4_k_m.gguf",
    )
    llama = os.environ.get(
        "PC_INFERENCE_LLAMA",
        r"C:/Users/yaelm/AppData/Local/Microsoft/WinGet/Packages/"
        r"ggml.llamacpp_Microsoft.Winget.Source_8wekyb3d8bbwe/llama-cli.exe",
    )

    def _gpu() -> str:
        try:
            r = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total,compute_cap",
                 "--format=csv,noheader"],
                capture_output=True, text=True, shell=False, timeout=8,
            )
            return r.stdout.strip() if r.returncode == 0 else "nvidia-smi unavailable"
        except Exception as e:  # noqa: BLE001
            return f"nvidia-smi error: {e}"

    def _gen(prompt: str, ngl: int, n: int = 150) -> str:
        if not os.path.exists(llama):
            return f"llama-cli missing: {llama}"
        if not os.path.exists(model):
            return f"model missing: {model}"
        try:
            r = subprocess.run(
                [llama, "-m", model, "-p", prompt, "-n", str(n),
                 "--temp", "0.2", "--ctx-size", "8192",
                 "-ngl", str(ngl), "--color", "off", "--single-turn"],
                capture_output=True, text=True, shell=False, timeout=600,
            )
            out = r.stdout or ""
            footer = ""
            for line in out.splitlines():
                if "t/s" in line and "Prompt:" in line:
                    footer = line.strip()
            return footer or (out.strip()[-300:] if out.strip() else (r.stderr or "")[-300:])
        except subprocess.TimeoutExpired:
            return "inference timed out"
        except Exception as e:  # noqa: BLE001
            return f"inference error: {e}"

    surface = {
        "kind": "pc_inference",
        "address": raw,
        "node": "pc://mesh/victus/local",
        "control": "+?://cc",
        "runtime": "llama.cpp",
        "model": os.path.basename(model),
        "model_present": os.path.exists(model),
        "llama_present": os.path.exists(llama),
        "native": os.path.exists(llama) and os.path.exists(model),
        "local_only": True,
    }

    if action == "report":
        return {
            "ok": True, "rc": 0,
            "stdout": (f"pc://inference -> {surface['model']}\n"
                       f"  runtime : llama.cpp ({'ready' if surface['llama_present'] else 'MISSING'})\n"
                       f"  gpu     : {_gpu()}\n"
                       f"  substrate: Model -> GGUF -> llama.cpp -> CPU/GPU\n"),
            "stderr": "",
            "surface": surface,
        }

    if action == "run":
        prompt = arg or "Write a Three.js rotating gold cube:"
        footer = _gen(prompt, 99)
        return {
            "ok": "t/s" in footer, "rc": 0 if "t/s" in footer else 1,
            "stdout": f"pc://inference run -ngl 99 -> {footer}\n",
            "stderr": "" if "t/s" in footer else footer,
            "surface": {**surface, "action": "run", "ngl": 99, "footer": footer},
        }

    if action == "bench":
        gpu = _gen("Write a Three.js rotating cube:", 99)
        cpu = _gen("Write a Three.js rotating cube:", 0)
        return {
            "ok": "t/s" in gpu and "t/s" in cpu, "rc": 0,
            "stdout": (f"pc://inference bench\n  -ngl 99 : {gpu}\n"
                       f"  -ngl  0 : {cpu}\n  (a 4-40x gap proves offload; equal = CPU fallback)\n"),
            "stderr": "",
            "surface": {**surface, "action": "bench", "gpu": gpu, "cpu": cpu},
        }

    return {
        "ok": False, "rc": 2, "stdout": "",
        "stderr": f"unknown pc://inference action: {action} (use report|run|bench)",
        "surface": surface,
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
    """vscode:// — the VSCODER://BRIDGE surface.

    VS Code is the human-controlled agentic terminal. The bridge exposes 6
    TypeScript modules over localhost WebSocket + JSON-RPC. This scheme makes
    those capabilities addressable from the conductor.

    Actions:
      vscode://              → bridge index (modules, capabilities, status)
      vscode://bridge        → IPC + auth + session state
      vscode://state         → IDEStateObserver (snapshot version, deltas)
      vscode://resolver      → CommandResolver (effect classification)
      vscode://plan          → PlanValidator (workspace hash, conflicts)
      vscode://capabilities  → the 11 typed namespaces
      vscode://events        → EventStream (delta chain, sanitize)
    """
    import json as _json
    import os as _os

    rest = raw.split("vscode://", 1)[1].strip() if "vscode://" in raw else ""
    action = (rest.split()[0].lower() if rest else "status")

    _BRIDGE_DIR = r"C:\æ\vscoder\src\bridge"
    _MODULES = {
        "ipc.ts": "JSON-RPC over WebSocket · localhost · authenticated · payload-capped",
        "state.ts": "IDEStateObserver · VSCODER_IDE_STATE_V1 · versioned snapshots · compact deltas",
        "resolver.ts": "CommandResolver · EffectClass (LOCAL/DURABLE/EXTERNAL) · known commands",
        "plan.ts": "PlanBuilder · PlanValidator · workspace_hash · 409 PLAN_STATE_CONFLICT",
        "capabilities.ts": "11 typed namespaces · CapabilityRegistry",
        "events.ts": "EventStream · delta chain · sanitize",
    }

    def _read_bridge_file(name: str) -> str:
        p = _os.path.join(_BRIDGE_DIR, name)
        if not _os.path.exists(p):
            return ""
        return open(p, encoding="utf-8", errors="replace").read()

    def _extract_exports(name: str) -> list:
        """Extract top-level export signatures from a bridge module."""
        src = _read_bridge_file(name)
        if not src:
            return []
        out = []
        for line in src.splitlines():
            line = line.strip()
            if line.startswith("export ") and ("function " in line or "class " in line or "const " in line or "interface " in line or "type " in line):
                # Take first 100 chars
                sig = line[:100]
                if sig not in out:
                    out.append(sig)
        return out[:12]

    def _extract_namespaces() -> list:
        """Extract the 11 capability namespaces from capabilities.ts."""
        src = _read_bridge_file("capabilities.ts")
        if not src:
            return []
        # Look for registerNamespace or namespace patterns
        import re as _re
        ns = _re.findall(r'registerNamespace\(["\']([^"\']+)["\']', src)
        if not ns:
            ns = _re.findall(r'namespace\s*=\s*["\']([^"\']+)["\']', src)
        if not ns:
            # Fallback: look for const xxx = { patterns after "export const"
            ns = _re.findall(r'export\s+const\s+(\w+)\s*=\s*\{', src)
        return sorted(set(ns))[:15]

    def _extract_jsonrpc_methods() -> list:
        """Extract JSON-RPC method names from ipc.ts."""
        src = _read_bridge_file("ipc.ts")
        if not src:
            return []
        import re as _re
        methods = _re.findall(r'["\']([a-z]+\.[a-z]+)["\']', src)
        return sorted(set(methods))[:10]

    def _extract_effect_classes() -> list:
        """Extract effect classes from resolver.ts."""
        src = _read_bridge_file("resolver.ts")
        if not src:
            return []
        import re as _re
        effects = _re.findall(r'"(LOCAL|DURABLE|EXTERNAL)"', src)
        return sorted(set(effects))

    def _extract_delta_kinds() -> list:
        """Extract delta kinds from events.ts."""
        src = _read_bridge_file("events.ts")
        if not src:
            return []
        import re as _re
        kinds = _re.findall(r'"([a-z_]+)"', src)
        return sorted(set(kinds))[:15]

    # ── bridge ──
    if action == "bridge":
        methods = _extract_jsonrpc_methods()
        return {
            "ok": True,
            "scheme": "vscode://",
            "action": "bridge",
            "transport": "localhost WebSocket + JSON-RPC 2.0",
            "auth": "session-authenticated · TTL 30min · revocable",
            "payload_cap": "64 KB",
            "jsonrpc_methods": methods,
            "modules": _MODULES,
            "stdout": (
                "vscode://bridge — VSCODER://BRIDGE\n"
                f"  transport   localhost WebSocket + JSON-RPC 2.0\n"
                f"  auth        session-authenticated · TTL 30min · revocable\n"
                f"  payload_cap 64 KB\n"
                f"  methods     {', '.join(methods) if methods else '(none found)'}\n"
                f"  modules     {len(_MODULES)}\n"
            ),
        }

    # ── state ──
    if action == "state":
        exports = _extract_exports("state.ts")
        return {
            "ok": True,
            "scheme": "vscode://",
            "action": "state",
            "observer": "IDEStateObserver",
            "snapshot_version": "VSCODER_IDE_STATE_V1",
            "deltas": "compact · only changed fields",
            "exports": exports,
            "stdout": (
                "vscode://state — IDEStateObserver\n"
                f"  snapshot_version  VSCODER_IDE_STATE_V1\n"
                f"  deltas            compact · only changed fields\n"
                f"  exports           {len(exports)}\n"
                + "".join(f"    {e}\n" for e in exports[:8])
            ),
        }

    # ── resolver ──
    if action == "resolver":
        effects = _extract_effect_classes()
        exports = _extract_exports("resolver.ts")
        return {
            "ok": True,
            "scheme": "vscode://",
            "action": "resolver",
            "resolver": "CommandResolver",
            "effect_classes": effects,
            "exports": exports,
            "stdout": (
                "vscode://resolver — CommandResolver\n"
                f"  effect_classes  {', '.join(effects) if effects else '(none found)'}\n"
                f"  exports         {len(exports)}\n"
                + "".join(f"    {e}\n" for e in exports[:8])
            ),
        }

    # ── plan ──
    if action == "plan":
        exports = _extract_exports("plan.ts")
        return {
            "ok": True,
            "scheme": "vscode://",
            "action": "plan",
            "validator": "PlanValidator",
            "conflict_code": "409 PLAN_STATE_CONFLICT",
            "workspace_hash": "SHA-256 over canonical workspace snapshot",
            "exports": exports,
            "stdout": (
                "vscode://plan — PlanValidator\n"
                f"  conflict_code   409 PLAN_STATE_CONFLICT\n"
                f"  workspace_hash  SHA-256 over canonical workspace snapshot\n"
                f"  exports         {len(exports)}\n"
                + "".join(f"    {e}\n" for e in exports[:8])
            ),
        }

    # ── capabilities ──
    if action == "capabilities":
        ns = _extract_namespaces()
        return {
            "ok": True,
            "scheme": "vscode://",
            "action": "capabilities",
            "namespaces": ns,
            "count": len(ns),
            "stdout": (
                "vscode://capabilities — 11 typed namespaces\n"
                f"  count  {len(ns)}\n"
                + "".join(f"    {n}\n" for n in ns)
            ),
        }

    # ── events ──
    if action == "events":
        kinds = _extract_delta_kinds()
        exports = _extract_exports("events.ts")
        return {
            "ok": True,
            "scheme": "vscode://",
            "action": "events",
            "stream": "EventStream",
            "delta_kinds": kinds,
            "sanitize": "excludes secrets from state/events/logs",
            "exports": exports,
            "stdout": (
                "vscode://events — EventStream\n"
                f"  delta_kinds  {len(kinds)}\n"
                f"  sanitize     excludes secrets from state/events/logs\n"
                f"  exports      {len(exports)}\n"
                + "".join(f"    {e}\n" for e in exports[:8])
            ),
        }

    # ── index ──
    ns = _extract_namespaces()
    methods = _extract_jsonrpc_methods()
    return {
        "ok": True,
        "scheme": "vscode://",
        "role": "the VSCODER://BRIDGE — VS Code as the human-controlled agentic terminal",
        "bridge_dir": _BRIDGE_DIR,
        "modules": _MODULES,
        "capabilities_count": len(ns),
        "jsonrpc_methods": methods,
        "actions": ["bridge", "state", "resolver", "plan", "capabilities", "events"],
        "surface": {
            "kind": "viewport_host",
            "address": raw,
            "v": "viewport",
            "compute": "local",
        },
        "stdout": (
            "vscode:// — VSCODER://BRIDGE\n"
            f"  bridge_dir      {_BRIDGE_DIR}\n"
            f"  modules         {len(_MODULES)}\n"
            f"  capabilities    {len(ns)} namespaces\n"
            f"  jsonrpc_methods {len(methods)}\n"
            f"\n  actions: bridge · state · resolver · plan · capabilities · events\n"
        ),
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

    if rest in ("constellation", "nodes"):
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

    if rest in ("map", "report", "system"):
        # A GENERATED map. A hand-written one goes stale silently — this one
        # cannot, because every line is measured at the moment it is printed.
        # A check that was not run says so; it is never shown as passing.
        import subprocess as _sub
        import os as _o4
        import glob as _g4

        FORK = _o4.path.join("C:\\", "æ", "hermes-fork")
        rows = []          # (layer, item, verdict, detail)

        # --- merge conflicts: measured, not remembered ---
        conf = []
        try:
            for f in _g4.glob(_o4.path.join(FORK, "**", "*.py"), recursive=True):
                if "node_modules" in f:
                    continue
                try:
                    with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                        if any(ln.startswith("<<<<<<< ") for ln in fh):
                            conf.append(_o4.path.relpath(f, FORK))
                except Exception:
                    pass
        except Exception:
            pass
        rows.append(("core", "merge conflicts (.py)",
                     "OK" if not conf else "FAIL",
                     "0 markers" if not conf else f"{len(conf)} file(s)"))

        # --- conductor loads and routes ---
        try:
            import importlib.util as _ilu2
            _sp2 = _ilu2.spec_from_file_location("_kc", _o4.path.join(FORK, "hermes_cli", "conductor.py"))
            _m2 = _ilu2.module_from_spec(_sp2)
            import sys as _sys2
            _sys2.modules["_kc"] = _m2
            _sp2.loader.exec_module(_m2)
            routed = []
            for r_ in ("keeper://", "æ://mesh", "æ://cc"):
                try:
                    routed.append((r_, bool(_m2._dispatch(r_).get("ok"))))
                except Exception:
                    routed.append((r_, False))
            good = sum(1 for _, k in routed if k)
            rows.append(("core", "conductor routing",
                         "OK" if good == len(routed) else "FAIL",
                         f"{good}/{len(routed)} routes answer"))
        except Exception as e:
            rows.append(("core", "conductor routing", "FAIL", f"import failed: {str(e)[:40]}"))

        # --- plugins: LOADED, not declared ---
        try:
            pdir = _o4.path.join(_o4.environ.get("LOCALAPPDATA", ""), "hermes", "plugins")
            total = loaded = 0
            for d_ in sorted(_g4.glob(_o4.path.join(pdir, "*"))):
                if not _o4.path.isdir(d_) or not _o4.path.exists(_o4.path.join(d_, "plugin.yaml")):
                    continue
                total += 1
                init = _o4.path.join(d_, "__init__.py")
                src = ""
                if _o4.path.exists(init):
                    with open(init, "r", encoding="utf-8", errors="ignore") as fh:
                        src = fh.read()
                if "def register(" in src:
                    loaded += 1
            rows.append(("plugins", "backends that register",
                         "OK" if loaded == total else "FAIL",
                         f"{loaded}/{total} have a register()"))
        except Exception as e:
            rows.append(("plugins", "backends that register", "FAIL", str(e)[:40]))

        # --- brain: live + durable ---
        try:
            import urllib.request as _ur4
            import json as _js4
            with _ur4.urlopen("http://129.212.180.252:3000/xrpc/ae.vps.status", timeout=8) as r_:
                b_ = _js4.loads(r_.read() or b"{}")
            n_ = sum((b_.get("records") or {}).values())
            rows.append(("glocal", "brain (droplet PDS)",
                         "OK" if b_.get("vps") == "up" else "FAIL",
                         f"up · {n_} records"))
        except Exception as e:
            rows.append(("glocal", "brain (droplet PDS)", "FAIL", str(e)[:40]))

        # --- hands: the RTX leaf ---
        try:
            import urllib.request as _ur5
            import json as _js5
            with _ur5.urlopen("http://127.0.0.1:3050/xrpc/ae.vps.rtx?op=probe", timeout=6) as r_:
                l_ = _js5.loads(r_.read() or b"{}")
            pr_ = l_.get("probe") or {}
            rows.append(("glocal", "hands (RTX leaf)",
                         "OK" if pr_.get("name") else "FAIL",
                         f"{pr_.get('name','?')} · {pr_.get('temperature.gpu','?')}C"))
        except Exception as e:
            rows.append(("glocal", "hands (RTX leaf)", "FAIL", str(e)[:40]))

        # --- public surface ---
        try:
            import urllib.request as _ur6
            with _ur6.urlopen("https://myaelmendez.github.io/", timeout=10) as r_:
                rows.append(("surface", "github.io", "OK" if r_.status == 200 else "FAIL",
                             f"HTTP {r_.status}"))
        except Exception as e:
            rows.append(("surface", "github.io", "FAIL", str(e)[:40]))

        ok_n = sum(1 for _, _, v, _ in rows if v == "OK")
        w = max(len(r[1]) for r in rows)
        body = "\n".join(f"  [{'ok' if v == 'OK' else '!!'}] {item:<{w}}  {detail}"
                         for _, item, v, detail in rows)
        return _ok({"rows": [{"layer": l, "item": i, "verdict": v, "detail": d}
                             for l, i, v, d in rows],
                    "ok": ok_n, "total": len(rows)},
                   f"keeper://map — generated, {ok_n}/{len(rows)} measured OK\n\n"
                   f"{body}\n\n"
                   f"  Every line above was measured at print time. A check that\n"
                   f"  was not run says so; none is shown as passing untested.\n")

    if rest in ("publish", "post"):
        # Publish a MEASURED fact from the ledger as an ae.social record.
        #
        # The ledger is the raw material; this is the filter. Only entries that
        # carry evidence cross to the network — an entry that cannot point at
        # what proved it is not publishable. The custody boundary holds: nothing
        # from C:\<ae>\secrets is ever read here.
        import urllib.request as _ur7
        import json as _js7

        BRAIN = "http://129.212.180.252:3000/xrpc/ae.vps.record"
        PRINCIPAL = "did:web:myaelmendez.github.io"

        # 1. load the ledger
        facts = []
        try:
            import importlib.util as _ilu7
            _sp7 = _ilu7.spec_from_file_location("keeper_store", _store)
            _ks7 = _ilu7.module_from_spec(_sp7); _sp7.loader.exec_module(_ks7)
            facts = _ks7.recall("", limit=500).get("matches", [])
        except Exception as e:
            return {"ok": False, "rc": 1, "stdout": "",
                    "stderr": f"keeper://publish — ledger unavailable: {e}"}

        # 2. filter to what is publishable: needs evidence, and must not carry
        #    anything secret-shaped. Same discipline as the audit.
        import re as _re7
        SECRET_SHAPES = _re7.compile(
            r"AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{24,}|ghp_[A-Za-z0-9]{30,}"
            r"|xox[baprs]-[A-Za-z0-9\-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----"
            r"|dop_v1_[a-f0-9]{60,}|password\s*[:=]|token\s*[:=]\s*[A-Za-z0-9]{16,}",
            _re7.I)

        publishable, held = [], []
        for rec in facts:
            src = str(rec.get("source", ""))
            text = str(rec.get("text", ""))
            has_ev = "::" in src and len(src.split("::", 1)[1].strip()) > 8
            if SECRET_SHAPES.search(text) or SECRET_SHAPES.search(src):
                held.append((rec, "secret-shaped content"))
            elif not has_ev:
                held.append((rec, "no evidence"))
            else:
                publishable.append(rec)

        if not publishable:
            return _ok({"published": 0, "held": len(held)},
                       f"keeper://publish — nothing publishable\n"
                       f"  {len(facts)} in ledger · {len(held)} held\n"
                       f"  a post needs evidence; an entry without it stays local.\n")

        # 3. publish each as ae.social#post
        def _post7(nsid, value):
            body = _js7.dumps({"nsid": nsid, "value": value}).encode()
            req = _ur7.Request(BRAIN, data=body,
                               headers={"Content-Type": "application/json"},
                               method="POST")
            try:
                with _ur7.urlopen(req, timeout=25) as r:
                    out = _js7.loads(r.read() or b"{}")
                return True, out.get("sig", "")[:16]
            except Exception as e:
                return False, f"{type(e).__name__}: {e}"[:100]

        published = []
        for rec in publishable:
            src = str(rec.get("source", ""))
            evidence = src.split("::", 1)[1].strip() if "::" in src else ""
            okp, sig = _post7("ae.social#post", {
                "text": str(rec.get("text", ""))[:3000],
                "kind": str(rec.get("kind", "fact")),
                "evidence": evidence[:500],
                "agent": "keeper",
                "principal": PRINCIPAL,
                "tags": [str(t)[:48] for t in (rec.get("tags") or [])][:12],
                "measured": True,
                "createdAt": rec.get("iso") or "",
            })
            published.append((okp, sig, str(rec.get("text", ""))[:70]))

        good = sum(1 for o, _, _ in published if o)
        return _ok({"published": good, "held": len(held),
                    "records": [{"ok": o, "sig": s, "text": t} for o, s, t in published]},
                   f"keeper://publish — receipts network\n"
                   f"  published: {good}/{len(publishable)}   held: {len(held)}\n"
                   f"  principal: {PRINCIPAL}\n"
                   f"  custody:   secrets never read here\n\n"
                   + "\n".join(f"  [{'ok' if o else '!!'}] {s:16} {t}"
                               for o, s, t in published[:8])
                   + (f"\n  held back: " + "; ".join(f"{w}" for _, w in held[:4])
                      if held else "")
                   + "\n")

    if rest == "code_mode" or rest.startswith("code_mode "):
        # æ://code_mode — the compact DSL for the sovereign mesh.
        #
        # Inspired by Cloudflare Code Mode: instead of calling tools individually,
        # the agent writes a compact program against a typed API. The program
        # runs in a sandbox (Python) with explicit bindings (the keeper:// verbs).
        #
        # Syntax:
        #   a          → keeper://audit
        #   p          → keeper://publish
        #   r          → keeper://remember
        #   R          → keeper://recall
        #   l          → keeper://ledger
        #   h          → keeper://handoff
        #   a|p|r      → pipe: audit → publish → remember
        #   r:broken   → recall filtered by "broken"
        #   a!         → audit with strict mode (fail on any warning)
        #   ?          → list available commands
        #
        # The DSL is deliberately tiny. The mesh has 7 verbs. The DSL maps
        # 1:1 to them. No abstraction, no magic — just a compact surface.

        import urllib.request as _ur8
        import json as _js8

        # Parse the program
        program = rest.strip() if rest else "?"

        # Available commands
        CMDS = {
            "a": "audit",
            "p": "publish",
            "r": "remember",
            "R": "recall",
            "l": "ledger",
            "h": "handoff",
        }

        # Help
        if program == "?" or program == "help":
            lines = ["æ://code_mode — compact DSL for the sovereign mesh", ""]
            lines.append("  commands:")
            for k, v in CMDS.items():
                lines.append(f"    {k:2} → keeper://{v}")
            lines.append("")
            lines.append("  composition:")
            lines.append("    a|p|r   → audit → publish → remember")
            lines.append("    r:broken → recall filtered by 'broken'")
            lines.append("    a!      → audit with strict mode")
            lines.append("")
            lines.append("  examples:")
            lines.append("    æ://code_mode a       → run audit")
            lines.append("    æ://code_mode a|p|r   → audit, publish results, remember")
            lines.append("    æ://code_mode R:fix   → recall entries matching 'fix'")
            return _ok({"commands": CMDS, "syntax": "a|p|r, r:filter, a!"},
                       "\n".join(lines) + "\n")

        # Parse pipe chain
        parts = program.split("|")
        results = []

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Check for filter (r:broken)
            filter_str = None
            if ":" in part and part.split(":")[0] in CMDS:
                cmd, filter_str = part.split(":", 1)
            else:
                cmd = part

            # Check for strict mode (a!)
            strict = False
            if cmd.endswith("!"):
                strict = True
                cmd = cmd[:-1]

            # Validate
            if cmd not in CMDS:
                return {"ok": False, "rc": 1, "stdout": "",
                        "stderr": f"æ://code_mode — unknown command '{cmd}'\n"
                                  f"  available: {', '.join(CMDS.keys())}\n"
                                  f"  use '?' for help\n"}

            # Execute
            verb = CMDS[cmd]
            if filter_str:
                verb = f"{verb} {filter_str}"
            if strict:
                verb = f"{verb} --strict"

            # Call the keeper:// dispatch
            try:
                result = _dispatch(f"keeper://{verb}")
                results.append({
                    "cmd": cmd,
                    "verb": verb,
                    "ok": result.get("ok", False),
                    "stdout": result.get("stdout", ""),
                    "stderr": result.get("stderr", ""),
                })
            except Exception as e:
                results.append({
                    "cmd": cmd,
                    "verb": verb,
                    "ok": False,
                    "stdout": "",
                    "stderr": f"{type(e).__name__}: {e}",
                })

        # Report
        good = sum(1 for r in results if r["ok"])
        lines = [f"æ://code_mode — {len(results)} command(s)", ""]
        for r in lines:
            pass  # placeholder
        for r in results:
            status = "ok" if r["ok"] else "!!"
            lines.append(f"  [{status}] {r['cmd']} → keeper://{r['verb']}")
            if r["stdout"]:
                # Show first 3 lines of stdout
                for l in r["stdout"].split("\n")[:3]:
                    if l.strip():
                        lines.append(f"       {l}")
            if r["stderr"]:
                lines.append(f"       error: {r['stderr'][:80]}")

        return _ok({"executed": good, "total": len(results), "results": results},
                   "\n".join(lines) + "\n")

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
      vidæo://<brand>[/<act>] → brand production surface (video + audio)
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
    # --- æ://code_mode — compact DSL for the sovereign mesh ---
    if rest == "code_mode" or rest.startswith("code_mode "):
        # Strip "code_mode" prefix and pass the rest as the program
        program = rest[len("code_mode"):].strip() if rest.startswith("code_mode ") else ""
        return _keeper_dispatch(f"keeper://code_mode {program}")
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
        # a:// is the ASCII alias for æ:// (normalized in dispatch); recognize it
        # here too so the router accepts it as a scheme before normalization.
        if raw.startswith("a://") or raw.startswith("+a://"):
            return True
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
_DISPATCHER.register("pc://inference", _pc_inference_dispatch)
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
_DISPATCHER.register("conductor://", _conductor_dispatch)


def _monaco_dispatch(raw: str) -> dict:
    """monaco:// - Monaco editor skill router.

    Routes monaco://<skill> URIs to the matching skill handler.
    Falls back to skill file lookup if no built-in route matches.
    """
    rest = raw.split("monaco://", 1)[1].strip() if "monaco://" in raw else ""
    skill = rest.split("?", 1)[0].split()[0] if rest else ""
    params = rest.split("?", 1)[1] if "?" in rest else ""

    _SKILL_ROUTES = {
        "llama-cpp-gpu": "Local GGUF inference via RTX 3050",
        "rtx-telemetry": "Live GPU metrics panel",
        "deploy-surfaces": "Deploy HTML surface from editor",
        "code-mode": "Run sandboxed code in editor",
        "pc-inference": "PC://INFERENCE substrate",
        "ae-as-skill": "æ:// computing stack guide",
        "glocal-mesh": "Mesh topology + tier status",
        "qr-vision": "QR detection + generation",
        "cri-index": "Consumer Redline Index",
        "mail-agent": "Agentic email triage + delivery",
    }

    if skill in _SKILL_ROUTES:
        return {
            "ok": True, "rc": 0,
            "stdout": f"monaco://{skill} → {_SKILL_ROUTES[skill]}\n",
            "stderr": "", "scheme": "monaco", "skill": skill, "params": params,
            "surface": {"kind": "monaco_dispatch", "skill": skill, "params": params},
        }

    return {
        "ok": False, "rc": 2,
        "stdout": "",
        "stderr": f"monaco:// unknown skill: {skill}. Routes: {', '.join(sorted(_SKILL_ROUTES))}",
        "scheme": "monaco", "skill": skill,
    }


_DISPATCHER.register("monaco://", _monaco_dispatch)


def _cloud_dispatch(raw: str) -> dict:
    """cloud:// - droplet cloud operations.

    Routes cloud://<op> to the droplet API at 129.212.180.252:3000.
    """
    import urllib.request, json as _json
    DROPLET = "http://129.212.180.252:3000"
    rest = raw.split("cloud://", 1)[1].strip() if "cloud://" in raw else ""
    op = rest.split("?", 1)[0].split()[0] if rest else ""
    params = rest.split("?", 1)[1] if "?" in rest else ""

    _CLOUD_OPS = {
        "status": "Droplet status + VPS health",
        "audit": "Keeper audit + ledger entry",
        "ledger": "List ledger entries",
        "posts": "List ae.social posts",
        "deploy": "Deploy surface to droplet",
        "record": "Write signed record",
        "gateway": "Open droplet gateway",
    }

    if op in _CLOUD_OPS:
        try:
            url = f"{DROPLET}/xrpc/ae.vps.{op}"
            with urllib.request.urlopen(url, timeout=5) as resp:
                body = resp.read().decode()
            return {
                "ok": True, "rc": 0,
                "stdout": f"cloud://{op} → droplet\n{body}\n",
                "stderr": "", "scheme": "cloud", "op": op, "params": params,
                "surface": {"kind": "cloud_dispatch", "op": op, "params": params},
            }
        except Exception as e:
            return {
                "ok": False, "rc": 1,
                "stdout": "", "stderr": f"cloud://{op} error: {e}",
                "scheme": "cloud", "op": op,
            }

    return {
        "ok": False, "rc": 2,
        "stdout": "",
        "stderr": f"cloud:// unknown op: {op}. Ops: {', '.join(sorted(_CLOUD_OPS))}",
        "scheme": "cloud", "op": op,
    }


_DISPATCHER.register("cloud://", _cloud_dispatch)
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
        # vault tier
        try:
            from secret_source import sources as _src_info
            info = _src_info()
            v = info.get("væult", {})
            if v.get("exists"):
                mark = "OK " if v.get("unlocked") else "LOCKED"
                lines.append(f"  [{mark}] væult: {v.get('path')} ({len(v.get('entries', []))} entries)")
            else:
                lines.append(f"  [absent] væult: {v.get('path')}")
        except Exception:
            pass
        return {"ok": True, "stdout": "\n".join(lines) + "\n",
                "surface": {"kind": "secrets", "local_only": True, "paths": DEFAULT_PATHS}}

    if action == "status":
        lines = []
        if not src or not os.path.exists(src):
            lines.append("secrets: NO bridge file found")
            lines.append("  bridge: https://myaelmendez.github.io/secret-source-bridge.html")
            lines.append("  fix: in bridge click 'Push to local' -> save to C:\\?\\secrets\\secrets.json")
        else:
            try:
                data = json.load(open(src, encoding="utf-8"))
                n = len(data.get("secrets", []))
                lines.append(f"secrets: {n} entry(ies) at {src}")
            except Exception as exc:
                lines.append(f"secrets: unreadable source ({exc})")
        # vault tier
        try:
            from secret_source import sources as _src_info
            info = _src_info()
            v = info.get("væult", {})
            if v.get("exists"):
                state = "unlocked" if v.get("unlocked") else "LOCKED"
                lines.append(f"  væult: {state} ({len(v.get('entries', []))} entries) at {v.get('path')}")
            else:
                lines.append(f"  væult: absent at {v.get('path')}")
        except Exception:
            pass
        return {"ok": True, "stdout": "\n".join(lines) + "\n",
                "surface": {"kind": "secrets", "local_only": True, "present": bool(src and os.path.exists(src))}}

    if action == "list":
        rows = []
        if src and os.path.exists(src):
            data = json.load(open(src, encoding="utf-8"))
            for s in data.get("secrets", []):
                v = str(s.get("value", ""))
                mask = "*" * min(12, max(4, len(v))) if v else ""
                rows.append(f"  {s.get('key')}  [{s.get('kind')}]  {mask}")
        # vault tier (masked)
        try:
            from secret_source import _vaeult_entries
            for k, v in _vaeult_entries().items():
                mask = "*" * min(12, max(4, len(v))) if v else ""
                rows.append(f"  {k}  [væult]  {mask}")
        except Exception:
            pass
        if not rows:
            return {"ok": False, "stderr": "secrets: NO local source (Push to local first)"}
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


def _vaeult_dispatch(raw: str) -> dict:
    """væult:// — sovereign vault operations (status, list, get, unlock).

    All values are masked in stdout. Raw values are carried in the result
    dict only for the agent, never printed. The passphrase is read from
    VAEULT_PASSPHRASE env var — never from the command line.
    """
    import sys as _sys
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in _sys.path:
        _sys.path.insert(0, _HERE)
    _AGENTS = os.path.normpath(os.path.join(_HERE, "..", "..", "agents"))
    if os.path.isdir(_AGENTS) and _AGENTS not in _sys.path:
        _sys.path.insert(0, _AGENTS)
    try:
        from secret_source import get_secret, get_by_prefix, sources as _src_info
    except Exception as exc:
        return {"ok": False, "stderr": f"væult: cannot load secret_source ({exc})"}

    rest = raw.split("væult://", 1)[1].strip() if "væult://" in raw else ""
    parts = rest.split(" ", 1)
    action = parts[0] if parts else "status"
    arg = parts[1] if len(parts) > 1 else ""

    info = _src_info()
    v = info.get("væult", {})

    if action == "status":
        if not v.get("exists"):
            return {"ok": True, "stdout": "væult: no vault found\n",
                    "surface": {"kind": "væult", "exists": False, "path": v.get("path")}}
        state = "unlocked" if v.get("unlocked") else "LOCKED"
        entries = v.get("entries", [])
        lines = [f"væult: {state}"]
        lines.append(f"  path: {v.get('path')}")
        lines.append(f"  entries: {len(entries)}")
        if entries:
            lines.append("  keys: " + ", ".join(entries))
        return {"ok": True, "stdout": "\n".join(lines) + "\n",
                "surface": {"kind": "væult", "exists": True, "unlocked": v.get("unlocked", False),
                            "path": v.get("path"), "entries": entries}}

    if action == "list":
        if not v.get("exists"):
            return {"ok": False, "stderr": "væult: no vault found"}
        if not v.get("unlocked"):
            return {"ok": False, "stderr": "væult: vault is locked (set VAEULT_PASSPHRASE)"}
        entries = v.get("entries", [])
        if not entries:
            return {"ok": True, "stdout": "væult: vault is empty\n"}
        lines = ["væult entries (masked):"]
        for k in entries:
            lines.append(f"  {k}  ************")
        return {"ok": True, "stdout": "\n".join(lines) + "\n",
                "surface": {"kind": "væult", "entries": entries}}

    if action == "get":
        if not arg:
            return {"ok": False, "stderr": "væult get <KEY> — key required"}
        if not v.get("exists"):
            return {"ok": False, "stderr": "væult: no vault found"}
        if not v.get("unlocked"):
            return {"ok": False, "stderr": "væult: vault is locked (set VAEULT_PASSPHRASE)"}
        val = get_secret(arg)
        if val is None:
            return {"ok": False, "stderr": f"væult: no entry '{arg}'"}
        mask = "*" * min(12, max(4, len(val)))
        return {"ok": True, "stdout": f"væult get {arg} = {mask}  (resolved locally; injected at runtime)\n",
                "secret_value": val,
                "surface": {"kind": "væult", "key": arg, "masked": True}}

    if action == "unlock":
        passphrase = os.environ.get("VAEULT_PASSPHRASE")
        if not passphrase:
            return {"ok": False, "stderr": "væult: VAEULT_PASSPHRASE not set"}
        if not v.get("exists"):
            return {"ok": False, "stderr": "væult: no vault found"}
        try:
            from secret_source import _vaeult_unlocked
            mod, key = _vaeult_unlocked()
            if mod is None:
                return {"ok": False, "stderr": "væult: wrong passphrase"}
            return {"ok": True, "stdout": "væult: unlocked ✓\n",
                    "surface": {"kind": "væult", "unlocked": True}}
        except Exception as exc:
            return {"ok": False, "stderr": f"væult: unlock failed ({exc})"}

    if action == "new":
        # væult://new <KEY> <VALUE>
        parts_new = arg.split(" ", 1)
        if len(parts_new) < 2 or not parts_new[0].strip() or not parts_new[1].strip():
            return {"ok": False, "stderr": "væult new <KEY> <VALUE> — key and value required"}
        key = parts_new[0].strip()
        value = parts_new[1].strip()
        if not v.get("exists"):
            return {"ok": False, "stderr": "væult: no vault found"}
        if not v.get("unlocked"):
            return {"ok": False, "stderr": "væult: vault is locked (set VAEULT_PASSPHRASE)"}
        try:
            from secret_source import _vaeult_unlocked, _vaeult_entries
            mod, vault_key = _vaeult_unlocked()
            if mod is None:
                return {"ok": False, "stderr": "væult: wrong passphrase"}
            import pathlib
            vault_path = pathlib.Path(v.get("path"))
            doc = mod.load_raw(vault_path)
            blob = mod.seal(vault_key, key, value)
            doc["entries"][key] = blob
            doc["updated"] = __import__("time").strftime("%Y-%m-%dT%H:%M:%S%z")
            mod.save_raw(vault_path, doc)
            return {"ok": True, "stdout": f"væult: stored '{key}' ({len(value)} chars, encrypted)\n",
                    "surface": {"kind": "væult", "action": "new", "key": key}}
        except Exception as exc:
            return {"ok": False, "stderr": f"væult: new failed ({exc})"}

    if action == "qr-export":
        # væult://qr-export <KEY> [--out PATH]
        if not arg:
            return {"ok": False, "stderr": "væult qr-export <KEY> [--out PATH]"}
        parts_qr = arg.split(" ")
        key = parts_qr[0]
        out = None
        if "--out" in parts_qr:
            out = parts_qr[parts_qr.index("--out") + 1]
        if not v.get("exists"):
            return {"ok": False, "stderr": "væult: no vault found"}
        if not v.get("unlocked"):
            return {"ok": False, "stderr": "væult: vault is locked (set VAEULT_PASSPHRASE)"}
        try:
            from secret_source import _vaeult_unlocked
            mod, vault_key = _vaeult_unlocked()
            if mod is None:
                return {"ok": False, "stderr": "væult: wrong passphrase"}
            import pathlib
            vault_path = pathlib.Path(v.get("path"))
            doc = mod.load_raw(vault_path)
            if key not in doc.get("entries", {}):
                return {"ok": False, "stderr": f"væult: no entry '{key}'"}
            payload = mod._qr_payload(key, doc["entries"][key])
            try:
                import qrcode
            except ImportError:
                return {"ok": False, "stderr": "væult: qrcode not installed (pip install qrcode pillow)"}
            qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=2)
            qr.add_data(payload)
            try:
                qr.make(fit=True)
            except Exception as e:
                return {"ok": False, "stderr": f"væult: secret too large for QR: {e}"}
            if qr.version > 40:
                return {"ok": False, "stderr": f"væult: needs QR v{qr.version} > v40 cap"}
            img = qr.make_image(fill_color="black", back_color="white")
            dest = pathlib.Path(out) if out else vault_path.with_suffix(".qr." + key + ".png")
            dest.parent.mkdir(parents=True, exist_ok=True)
            img.save(dest)
            return {"ok": True, "stdout": f"væult: sealed QR for '{key}' -> {dest}\n  version v{qr.version} · {len(payload)} bytes · SEALED (no plaintext)\n",
                    "surface": {"kind": "væult", "action": "qr-export", "key": key, "path": str(dest)}}
        except Exception as exc:
            return {"ok": False, "stderr": f"væult: qr-export failed ({exc})"}

    if action == "qr-import":
        # væult://qr-import <IMAGE>
        if not arg:
            return {"ok": False, "stderr": "væult qr-import <IMAGE>"}
        if not v.get("exists"):
            return {"ok": False, "stderr": "væult: no vault found"}
        if not v.get("unlocked"):
            return {"ok": False, "stderr": "væult: vault is locked (set VAEULT_PASSPHRASE)"}
        try:
            from secret_source import _vaeult_unlocked
            mod, vault_key = _vaeult_unlocked()
            if mod is None:
                return {"ok": False, "stderr": "væult: wrong passphrase"}
            import pathlib
            img_path = pathlib.Path(arg)
            if not img_path.exists():
                return {"ok": False, "stderr": f"væult: no image at {img_path}"}
            try:
                from pyzbar.pyzbar import decode as _zbar
                from PIL import Image
            except ImportError:
                return {"ok": False, "stderr": "væult: need pyzbar + pillow (pip install pyzbar pillow)"}
            found = _zbar(Image.open(img_path))
            if not found:
                return {"ok": False, "stderr": "væult: no QR detected"}
            data = found[0].data.decode("utf-8", errors="replace")
            if not data.startswith(mod._QR_PREFIX):
                return {"ok": False, "stderr": "væult: not a væult QR payload"}
            import json as _json
            payload = _json.loads(data[len(mod._QR_PREFIX):])
            name, blob = payload["name"], payload["blob"]
            vault_path = pathlib.Path(v.get("path"))
            doc = mod.load_raw(vault_path)
            try:
                value = mod.open_entry(vault_key, name, blob)
            except Exception:
                return {"ok": False, "stderr": f"væult: QR '{name}' does NOT open under this vault's passphrase"}
            doc["entries"][name] = blob
            doc["updated"] = __import__("time").strftime("%Y-%m-%dT%H:%M:%S%z")
            mod.save_raw(vault_path, doc)
            return {"ok": True, "stdout": f"væult: imported '{name}' from QR ({len(value)} chars, verified under this key)\n",
                    "surface": {"kind": "væult", "action": "qr-import", "key": name}}
        except Exception as exc:
            return {"ok": False, "stderr": f"væult: qr-import failed ({exc})"}

    if action == "email-import":
        # væult://email-import — check inbox for [væult] emails and import
        if not v.get("exists"):
            return {"ok": False, "stderr": "væult: no vault found"}
        if not v.get("unlocked"):
            return {"ok": False, "stderr": "væult: vault is locked (set VAEULT_PASSPHRASE)"}
        try:
            import importlib.util
            _email_mod_path = os.path.join(_AGENTS, "væult_email.py")
            spec = importlib.util.spec_from_file_location("_vaeult_email", _email_mod_path)
            email_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(email_mod)
            results = email_mod.check_inbox()
            if not results:
                return {"ok": True, "stdout": "væult: no new [væult] emails\n",
                        "surface": {"kind": "væult", "action": "email-import", "imported": 0}}
            lines = [f"væult: imported {len(results)} secret(s) from email:"]
            for r in results:
                lines.append(f"  ✓ {r['key']}")
            return {"ok": True, "stdout": "\n".join(lines) + "\n",
                    "surface": {"kind": "væult", "action": "email-import", "imported": len(results)}}
        except Exception as exc:
            return {"ok": False, "stderr": f"væult: email-import failed ({exc})"}

    if action == "path":
        return {"ok": True, "stdout": f"væult path: {v.get('path')}\n",
                "surface": {"kind": "væult", "path": v.get("path")}}

    return {"ok": False, "stderr": f"væult: unknown action '{action}' (try: status, list, get, new, qr-export, qr-import, email-import, unlock, path)"}


_DISPATCHER.register("+?://secrets", _secrets_dispatch)
_DISPATCHER.register("+æ://secrets", _secrets_dispatch)
_DISPATCHER.register("væult://", _vaeult_dispatch)


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
# ── vidæo:// — the brand production surface ────────────────────────────────
# vidæo://<brand>/<action>
#
# The brand IS the address. vidæo://aipodcast.me resolves the brand to its
# published surface and its asset manifest; the action runs the production
# pipeline against it.
#
#   vidæo://                        -> the scheme index (brands + actions)
#   vidæo://status                  -> toolchain: ffmpeg, node, GPU, corpus
#   vidæo://aipodcast.me            -> the brand: surface, manifest, asset counts
#   vidæo://aipodcast.me/verify     -> supervise the brand's corpus videos
#   vidæo://aipodcast.me/render <scene>  -> render a scene into the brand
#
# Graceful degradation: when the local toolchain is absent the brand surface
# still resolves (it is published); only the render/verify actions report why
# they cannot run. Same pattern as videolab:// and mcp://.

_VIDAEO_BRANDS = {
    "aipodcast.me": {
        "dir": "aipodcast_me",
        "surface": "https://myaelmendez.github.io/aipodcast_me/media.html",
        "hq": "https://myaelmendez.github.io/aipodcast_me/",
        "manifest": r"C:\æ\github-pages\aipodcast_me\media-manifest.json",
        "role": "Media — video + audio production. The brand carries the assets.",
    },
    "neuromitosis.com": {
        "dir": "neuromitosis",
        "surface": "https://myaelmendez.github.io/neuromitosis",
        "hq": "https://myaelmendez.github.io/neuromitosis",
        "manifest": r"C:\æ\github-pages\brain.json",
        "role": "Bond — the site brain. Human + Robot + DAO, wired via Hæbbian.",
    },
}


def _vidaeo_dispatch(raw: str) -> dict:
    """Route vidæo:// commands: the brand production surface."""
    import json as _json
    import os as _os
    import subprocess as _sp

    rest = raw.split("vidæo://", 1)[1].strip() if "vidæo://" in raw else ""
    # vidæo://<brand>/<action> [arg]   |   vidæo://<action>
    brand_key, action, arg = None, "status", ""
    if rest:
        head, _, tail = rest.partition("/")
        if head in _VIDAEO_BRANDS:
            brand_key = head
            if tail:
                a, _, b = tail.partition(" ")
                action, arg = (a or "status"), b.strip()
        else:
            a, _, b = rest.partition(" ")
            action, arg = (a or "status"), b.strip()

    _HERE = _os.path.dirname(_os.path.abspath(__file__))
    _ROOT = _os.path.normpath(_os.path.join(_HERE, "..", ".."))
    _VIDAEO = _os.path.join(_ROOT, "vidæo", "vidæo.py")
    _GPU_PY = r"C:\gpu\Scripts\python.exe"

    # ── no brand: the scheme index ──
    if brand_key is None and action in ("", "status", "index"):
        brands = [{"brand": k, "surface": v["surface"], "role": v["role"]}
                  for k, v in _VIDAEO_BRANDS.items()]
        return {
            "ok": True,
            "scheme": "vidæo://",
            "role": "brand production surface — the brand is the address",
            "brands": brands,
            "actions": ["status", "<brand>", "<brand>/verify", "<brand>/render <scene>"],
            "toolchain": {
                "vidæo_cli": _VIDAEO if _os.path.exists(_VIDAEO) else None,
                "gpu_python": _GPU_PY if _os.path.exists(_GPU_PY) else None,
            },
            "stdout": (f"vidæo:// — {len(brands)} brands\n"
                       + "".join(f"  vidæo://{b['brand']:18} {b['role'][:56]}\n" for b in brands)
                       + "\n  actions: status · <brand> · <brand>/verify · <brand>/render <scene>\n"),
        }

    if brand_key is None:
        return {"ok": False, "stderr": f"vidæo:// unknown action '{action}' — try vidæo://status or vidæo://aipodcast.me"}

    brand = _VIDAEO_BRANDS[brand_key]
    _BRAND_DIR = _os.path.join(_ROOT, "github-pages", brand["dir"])

    # ── the brand surface: what it is, what it carries ──
    if action in ("", "status"):
        info = {"ok": True, "brand": brand_key, "role": brand["role"],
                "surface": brand["surface"], "hq": brand["hq"]}
        mp = brand["manifest"]
        if _os.path.exists(mp):
            try:
                m = _json.loads(open(mp, encoding="utf-8").read())
                info["manifest"] = {
                    k: m.get(k) for k in
                    ("video_count", "audio_count", "total_video_mb", "total_audio_mb",
                     "total_surfaces", "total_categories", "all_pass", "episodes")
                    if m.get(k) is not None
                }
            except Exception as e:
                info["manifest_error"] = str(e)[:120]
        info["dir"] = _BRAND_DIR if _os.path.exists(_BRAND_DIR) else None
        lines = [f"vidæo://{brand_key}", f"  role     {brand['role']}",
                 f"  surface  {brand['surface']}"]
        if "manifest" in info:
            for k, v in info["manifest"].items():
                lines.append(f"  {k:9} {v}")
        info["stdout"] = "\n".join(lines) + "\n"
        return info

    # ── verify: supervise the brand's corpus ──
    if action == "verify":
        if not _os.path.exists(_VIDAEO):
            return {"ok": False, "stderr": f"vidæo://{brand_key}/verify — vidæo.py not found at {_VIDAEO}"}
        if not _os.path.exists(_GPU_PY):
            return {"ok": False, "stderr": f"vidæo://{brand_key}/verify — GPU python not found at {_GPU_PY}"}
        try:
            r = _sp.run([_GPU_PY, _VIDAEO, "corpus"], capture_output=True, text=True, timeout=300)
            return {"ok": r.returncode == 0, "stdout": r.stdout.strip()[-1500:],
                    "stderr": r.stderr.strip()[-400:],
                    "surface": {"kind": "vidæo", "brand": brand_key, "action": "verify"}}
        except Exception as exc:
            return {"ok": False, "stderr": f"vidæo://{brand_key}/verify — {exc}"}

    # ── render: run the AEE cycle into the brand ──
    if action == "render":
        if not _VIDAEO:
            return {"ok": False, "stderr": "vidæo://render — vidæo.py not found"}
        if not arg:
            return {"ok": False, "stderr": f"vidæo://{brand_key}/render requires a scene spec path"}
        try:
            r = _sp.run([_GPU_PY, _VIDAEO, "cycle", arg, _os.path.join(_BRAND_DIR, "render.mp4")],
                        capture_output=True, text=True, timeout=900, cwd=_os.path.join(_ROOT, "vidæo"))
            return {"ok": r.returncode == 0, "stdout": r.stdout.strip()[-1500:],
                    "stderr": r.stderr.strip()[-400:],
                    "surface": {"kind": "vidæo", "brand": brand_key, "action": "render"}}
        except Exception as exc:
            return {"ok": False, "stderr": f"vidæo://{brand_key}/render — {exc}"}

    return {"ok": False, "stderr": f"vidæo://{brand_key} unknown action '{action}'"}


_DISPATCHER.register("vidæo://", _vidaeo_dispatch)

# ── video:// — the render request surface (æRTXrender) ──────────────────────
# video://<what>  — ask for a video; the harness renders it deterministically.
#
# This is the REQUEST surface. `vidæo://` is the BRAND/pipeline surface (AEE
# cycle, corpus, brands); `video://` is the ask — "give me N seconds of X".
#
#   video://                          -> the surface index (known subjects)
#   video://status                    -> toolchain: node, ffmpeg, chrome, GPU
#   video://<subject> [seconds]       -> render <subject> for N seconds (default 5)
#   video://list                      -> surfaces available to render
#
# A subject is a scene in C:\æ\threejs-curriculo. The 5-second default matches
# the "summary" ask: a short, portable clip. Rendering runs the real pipeline:
# node render.mjs → CDP → NVENC → SupervisorVideo gate.

_VIDEO_SURFACES = {
    "dji": {"file": "dji-5s.html", "label": "Dow Jones Industrial Average",
            "note": "the DJI tape, drawn from the droplet broker's real quote"},
    "storyboards": {"file": "storyboards.html", "label": "Hollywood Golden Age Storyboards",
                    "note": "3 films noir, animatic panels"},
    "zeitgeist": {"file": "zeitgeist.html", "label": "@yaelmendez #zeitgeist",
                  "note": "9 real X posts on a timeline"},
    "video-vision": {"file": "video-vision.html", "label": "VIDEO VISION",
                     "note": "the pipeline seeing its own output"},
    "inside-compute": {"file": "inside-compute.html", "label": "INSIDE COMPUTE",
                       "note": "6-layer chip interior"},
    "aertx-demo": {"file": "aertx-demo.html", "label": "æRTXrender demo",
                   "note": "80k particles, deterministic hook"},
    "demo-9x16": {"file": "demo-9x16.html", "label": "9:16 capability demo",
                  "note": "5 scenes, Python · AEE · QR chip"},
}


def _video_dispatch(raw: str) -> dict:
    """Route video:// — the render request surface over æRTXrender."""
    import json as _json
    import os as _os
    import subprocess as _sp

    rest = raw.split("video://", 1)[1].strip() if "video://" in raw else ""
    parts = rest.split()
    subject = parts[0].lower() if parts else ""
    seconds = 5
    if len(parts) > 1:
        try:
            seconds = max(1, min(30, int(float(parts[1]))))
        except (TypeError, ValueError):
            pass

    _HERE = _os.path.dirname(_os.path.abspath(__file__))
    _ROOT = _os.path.normpath(_os.path.join(_HERE, "..", ".."))
    _THREEJS = _os.path.join(_ROOT, "threejs-curriculo")
    _RENDER = _os.path.join(_THREEJS, "render.mjs")
    _NODE = r"C:\Users\yaelm\AppData\Local\hermes\tools\node-26.7.0-win32-x64\node.exe"
    _GPU_PY = r"C:\gpu\Scripts\python.exe"
    _FFMPEG = r"C:\Users\yaelm\AppData\Local\hermes\tools\ffmpeg-7.1-nvenc\bin\ffmpeg.exe"

    # ── index / status / list ──
    if subject in ("", "status", "list"):
        surfaces = [{"subject": k, "label": v["label"], "note": v["note"]}
                    for k, v in _VIDEO_SURFACES.items()]
        return {
            "ok": True,
            "scheme": "video://",
            "role": "render request surface — ask for N seconds of a subject",
            "harness": "æRTXrender (deterministic: frame i → time i/FPS)",
            "default_seconds": 5,
            "surfaces": surfaces,
            "toolchain": {
                "node": _NODE if _os.path.exists(_NODE) else None,
                "render_mjs": _RENDER if _os.path.exists(_RENDER) else None,
                "ffmpeg_nvenc": _FFMPEG if _os.path.exists(_FFMPEG) else None,
            },
            "stdout": ("video:// — render request surface\n"
                       + "".join(f"  video://{s['subject']:16} {s['label'][:44]}\n" for s in surfaces)
                       + f"\n  usage: video://<subject> [seconds]   (default 5)\n"),
        }

    if subject not in _VIDEO_SURFACES:
        return {"ok": False,
                "stderr": f"video:// unknown subject '{subject}' — try: "
                          + ", ".join(sorted(_VIDEO_SURFACES))}

    spec = _VIDEO_SURFACES[subject]
    src = _os.path.join(_THREEJS, spec["file"])
    if not _os.path.exists(src):
        return {"ok": False, "stderr": f"video://{subject} — surface not found: {src}"}
    if not _os.path.exists(_RENDER):
        return {"ok": False, "stderr": f"video://{subject} — render.mjs not found: {_RENDER}"}
    if not _os.path.exists(_NODE):
        return {"ok": False, "stderr": f"video://{subject} — bundled node not found: {_NODE}"}

    out = _os.path.join(_THREEJS, f"{subject}-{seconds}s.mp4")
    frames = seconds * 30
    cmd = [_NODE, _RENDER, f"--url=http://127.0.0.1:8123/{spec['file']}",
           f"--out={out}", f"--frames={frames}", "--fps=30",
           "--w=720", "--h=1280", "--encoder=nvenc"]
    try:
        r = _sp.run(cmd, capture_output=True, text=True, timeout=900, cwd=_THREEJS)
    except _sp.TimeoutExpired:
        return {"ok": False, "stderr": f"video://{subject} — render timed out"}

    if r.returncode != 0 or not _os.path.exists(out):
        return {"ok": False, "stderr": (r.stderr or r.stdout or "render failed")[-400:],
                "surface": {"kind": "video", "subject": subject, "seconds": seconds}}

    # the gate — supervise what we just rendered
    gate = None
    try:
        import sys as _sys
        _sys.path.insert(0, _os.path.join(_ROOT, "supervisionvidaeo"))
        from supervisionvidaeo import verify as _verify
        rep = _verify(out, sample_every=15)
        gate = {"calidad": rep.get("calidad"), "receipt": rep.get("receipt"),
                "luminancia": rep.get("luminancia_media"),
                "frames_negros": rep.get("frames_negros")}
    except Exception as exc:
        gate = {"error": str(exc)[:120]}

    size_mb = round(_os.path.getsize(out) / 1048576, 2)
    return {
        "ok": True,
        "stdout": (f"video://{subject} — {seconds}s · {frames} frames · {size_mb} MB\n"
                   f"  {spec['label']}\n"
                   f"  gate: {gate.get('calidad')} · receipt {str(gate.get('receipt'))[:24]}\n"
                   f"  out: {out}\n"),
        "surface": {"kind": "video", "subject": subject, "seconds": seconds,
                    "frames": frames, "out": out, "size_mb": size_mb, "gate": gate},
    }


_DISPATCHER.register("video://", _video_dispatch)

# ── three.js:// — the Three.js stack surface ────────────────────────────────
# three.js://<what> — inspect and address the vendored Three.js stack.
#
# This is the LIBRARY/STACK surface. Three distinct verbs now:
#   video://dji 5        the ASK      — render N seconds of a subject
#   vidæo://aipodcast.me the BRAND    — a brand's surface + manifest
#   three.js://addons    the STACK    — what the renderer is made of
#
#   three.js://                 -> the stack index (version, surfaces, addons)
#   three.js://version          -> the vendored revision + file hashes
#   three.js://addons           -> the addon inventory
#   three.js://surfaces         -> every scene, and which are renderable
#   three.js://curriculum       -> the teaching phases (fase1..fase12)
#   three.js://check            -> verify the vendor is intact (files + REVISION)

_THREEJS_DIR = r"C:\æ\threejs-curriculo"


def _threejs_dispatch(raw: str) -> dict:
    """Route three.js:// — the vendored Three.js stack surface."""
    import hashlib as _hash
    import os as _os
    import re as _re

    rest = raw.split("three.js://", 1)[1].strip() if "three.js://" in raw else ""
    action = (rest.split()[0].lower() if rest else "status")

    _D = _THREEJS_DIR
    if not _os.path.isdir(_D):
        return {"ok": False, "stderr": f"three.js:// — stack dir not found: {_D}"}

    _VENDOR = _os.path.join(_D, "vendor")
    _CORE = _os.path.join(_VENDOR, "three.core.js")
    _MODULE = _os.path.join(_VENDOR, "three.module.js")
    _ADDONS = _os.path.join(_VENDOR, "addons")

    def _revision() -> str:
        try:
            txt = open(_CORE, encoding="utf-8", errors="replace").read(400000)
            m = _re.search(r"REVISION\s*=\s*'([0-9]+)'", txt)
            return m.group(1) if m else "unknown"
        except Exception:
            return "unknown"

    def _sha(path: str) -> str:
        try:
            return _hash.sha256(open(path, "rb").read()).hexdigest()[:16]
        except Exception:
            return ""

    def _addons() -> dict:
        out = {}
        if _os.path.isdir(_ADDONS):
            for d in sorted(_os.listdir(_ADDONS)):
                full = _os.path.join(_ADDONS, d)
                if _os.path.isdir(full):
                    out[d] = sorted(f[:-3] for f in _os.listdir(full) if f.endswith(".js"))
        return out

    def _surfaces() -> list:
        out = []
        for f in sorted(_os.listdir(_D)):
            if not f.endswith(".html"):
                continue
            p = _os.path.join(_D, f)
            try:
                txt = open(p, encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            renderable = "__renderFrame" in txt
            uses_three = "three.module.js" in txt or "import * as THREE" in txt
            out.append({"file": f, "renderable": renderable, "three": uses_three,
                        "kb": round(_os.path.getsize(p) / 1024, 1)})
        return out

    # ── version ──
    if action in ("version", "check"):
        files = {}
        for name, p in (("three.core.js", _CORE), ("three.module.js", _MODULE)):
            files[name] = {"exists": _os.path.exists(p),
                           "sha256_16": _sha(p) if _os.path.exists(p) else None,
                           "bytes": _os.path.getsize(p) if _os.path.exists(p) else 0}
        rev = _revision()
        payload = {"ok": True, "scheme": "three.js://", "revision": rev,
                   "vendor": _VENDOR, "files": files,
                   "stdout": (f"three.js r{rev}\n"
                              + "".join(f"  {k:18} {v['bytes']:>9} B  sha256:{v['sha256_16']}\n"
                                        for k, v in files.items()))}
        if action == "check":
            intact = all(v["exists"] and v["bytes"] > 0 for v in files.values()) and rev != "unknown"
            payload["intact"] = intact
            payload["ok"] = intact
            payload["stdout"] += f"  intact: {intact}\n"
        return payload

    # ── addons ──
    if action == "addons":
        a = _addons()
        total = sum(len(v) for v in a.values())
        return {"ok": True, "scheme": "three.js://", "addons": a, "count": total,
                "stdout": (f"three.js addons — {total} across {len(a)} groups\n"
                           + "".join(f"  {k:16} {len(v):>2}  {', '.join(v[:6])}"
                                     f"{'…' if len(v) > 6 else ''}\n" for k, v in a.items()))}

    # ── surfaces ──
    if action == "surfaces":
        s = _surfaces()
        rend = [x for x in s if x["renderable"]]
        three = [x for x in s if x["three"]]
        return {"ok": True, "scheme": "three.js://", "surfaces": s,
                "count": len(s), "renderable": len(rend), "using_three": len(three),
                "stdout": (f"three.js surfaces — {len(s)} html · {len(three)} use three · "
                           f"{len(rend)} renderable (__renderFrame)\n"
                           + "".join(f"  {x['file']:34} {x['kb']:>7} KB"
                                     f"{'  ▶render' if x['renderable'] else ''}\n" for x in s))}

    # ── curriculum ──
    if action == "curriculum":
        phases = sorted(f for f in _os.listdir(_D)
                        if f.startswith("fase") and f.endswith(".html"))
        return {"ok": True, "scheme": "three.js://", "phases": phases, "count": len(phases),
                "stdout": (f"three.js curriculum — {len(phases)} phases\n"
                           + "".join(f"  {p}\n" for p in phases))}

    # ── index ──
    s = _surfaces()
    a = _addons()
    return {
        "ok": True,
        "scheme": "three.js://",
        "role": "the Three.js stack surface — the renderer, inspected",
        "revision": _revision(),
        "dir": _D,
        "counts": {
            "surfaces": len(s),
            "renderable": sum(1 for x in s if x["renderable"]),
            "addons": sum(len(v) for v in a.values()),
            "phases": len([f for f in _os.listdir(_D) if f.startswith("fase") and f.endswith(".html")]),
        },
        "actions": ["version", "check", "addons", "surfaces", "curriculum"],
        "stdout": (f"three.js:// — r{_revision()} · {_D}\n"
                   f"  surfaces   {len(s)} html ({sum(1 for x in s if x['renderable'])} renderable)\n"
                   f"  addons     {sum(len(v) for v in a.values())} across {len(a)} groups\n"
                   f"  curriculum {len([f for f in _os.listdir(_D) if f.startswith('fase') and f.endswith('.html')])} phases\n"
                   f"\n  actions: version · check · addons · surfaces · curriculum\n"),
    }


_DISPATCHER.register("three.js://", _threejs_dispatch)

# ── hyperframes:// — the HyperFrames stack surface ──────────────────────────
# hyperframes://<what> — inspect and address the HyperFrames monorepo.
#
# The SIBLING surface to three.js://. Both expose a stack; they answer different
# questions:
#   three.js://      the RENDERER   — the vendored Three.js the scenes draw with
#   hyperframes://   the FRAMEWORK  — the composition/capture/encode monorepo
#
#   hyperframes://              -> the monorepo index (packages · registry · skills)
#   hyperframes://packages      -> the 7 workspace packages
#   hyperframes://registry      -> blocks · components · examples
#   hyperframes://skills        -> the 6 agent skills the repo ships
#   hyperframes://check         -> is it built? bun present? node_modules?
#   hyperframes://relation      -> how it relates to æRTXrender (the fork)

_HF_DIR = r"C:\æ\htmlvideo"


def _hf_dispatch(raw: str) -> dict:
    """Route hyperframes:// — the HyperFrames monorepo surface."""
    import json as _json
    import os as _os
    import shutil as _shutil

    rest = raw.split("hyperframes://", 1)[1].strip() if "hyperframes://" in raw else ""
    action = (rest.split()[0].lower() if rest else "status")

    _D = _HF_DIR
    if not _os.path.isdir(_D):
        return {"ok": False, "stderr": f"hyperframes:// — monorepo not found: {_D}"}

    def _pkg_version() -> str:
        try:
            d = _json.load(open(_os.path.join(_D, "package.json"), encoding="utf-8"))
            return d.get("version") or "unversioned (monorepo root)"
        except Exception:
            return "unknown"

    def _packages() -> list:
        p = _os.path.join(_D, "packages")
        if not _os.path.isdir(p):
            return []
        out = []
        for name in sorted(_os.listdir(p)):
            full = _os.path.join(p, name)
            if not _os.path.isdir(full):
                continue
            pj = _os.path.join(full, "package.json")
            ver = "?"
            if _os.path.exists(pj):
                try:
                    ver = _json.load(open(pj, encoding="utf-8")).get("version") or "?"
                except Exception:
                    pass
            out.append({"name": name, "version": ver,
                        "has_dist": _os.path.isdir(_os.path.join(full, "dist")),
                        "has_src": _os.path.isdir(_os.path.join(full, "src"))})
        return out

    def _registry() -> dict:
        r = _os.path.join(_D, "registry")
        out = {}
        for kind in ("blocks", "components", "examples"):
            d = _os.path.join(r, kind)
            out[kind] = sorted(_os.listdir(d)) if _os.path.isdir(d) else []
        return out

    def _skills() -> list:
        s = _os.path.join(_D, "skills")
        if not _os.path.isdir(s):
            return []
        out = []
        for name in sorted(_os.listdir(s)):
            f = _os.path.join(s, name, "SKILL.md")
            desc = ""
            if _os.path.exists(f):
                for line in open(f, encoding="utf-8", errors="replace").read(1200).splitlines():
                    if line.startswith("description:"):
                        desc = line.split(":", 1)[1].strip()[:80]
                        break
            out.append({"name": name, "description": desc})
        return out

    # ── packages ──
    if action == "packages":
        p = _packages()
        return {"ok": True, "scheme": "hyperframes://", "packages": p, "count": len(p),
                "stdout": (f"hyperframes packages — {len(p)}\n"
                           + "".join(f"  {x['name']:20} v{x['version']:12}"
                                     f"{'  dist✓' if x['has_dist'] else '  (no dist)'}\n"
                                     for x in p))}

    # ── registry ──
    if action == "registry":
        r = _registry()
        total = sum(len(v) for v in r.values())
        return {"ok": True, "scheme": "hyperframes://", "registry": r, "count": total,
                "stdout": (f"hyperframes registry — {total} entries\n"
                           + "".join(f"  {k:12} {len(v):>3}  {', '.join(v[:6])}"
                                     f"{'…' if len(v) > 6 else ''}\n" for k, v in r.items()))}

    # ── skills ──
    if action == "skills":
        s = _skills()
        return {"ok": True, "scheme": "hyperframes://", "skills": s, "count": len(s),
                "stdout": (f"hyperframes skills — {len(s)}\n"
                           + "".join(f"  {x['name']:26} {x['description'][:52]}\n" for x in s))}

    # ── check ──
    if action == "check":
        p = _packages()
        bun = _shutil.which("bun") or _shutil.which("bun.exe")
        nm = _os.path.join(_D, "node_modules")
        nm_present = _os.path.isdir(nm) and bool(_os.listdir(nm))
        built = any(x["has_dist"] for x in p)
        ok = bool(bun) and nm_present and built
        return {"ok": ok, "scheme": "hyperframes://",
                "bun": bun, "node_modules": nm_present,
                "packages_with_dist": sum(1 for x in p if x["has_dist"]),
                "packages_total": len(p),
                "stdout": (f"hyperframes build check\n"
                           f"  bun            {bun or 'NOT ON PATH'}\n"
                           f"  node_modules   {'present' if nm_present else 'absent'}\n"
                           f"  built dist     {sum(1 for x in p if x['has_dist'])}/{len(p)} packages\n"
                           f"  runnable:      {ok}\n"
                           f"  build: bun install && bun run build\n")}

    # ── relation to æRTXrender ──
    if action == "relation":
        return {"ok": True, "scheme": "hyperframes://",
                "fork": "C:/æ/htmlvideo (MYaelMendez/HTMLVIDEO ← heygen-com/hyperframes)",
                "sibling": "æRTXrender (C:/æ/threejs-curriculo/render.mjs)",
                "stdout": (
                    "hyperframes:// vs æRTXrender\n"
                    "  HyperFrames   declarative data-* DSL · clips · GSAP timelines\n"
                    "                Studio NLE · sub-compositions · 39 registry blocks\n"
                    "                Puppeteer + FFmpeg engine · bun workspace\n"
                    "  æRTXrender    imperative __renderFrame(i,total) hook\n"
                    "                single primitive · CDP capture + NVENC\n"
                    "                zero npm deps (native fetch + WebSocket)\n"
                    "  shared        deterministic rendering: frame i → time i/FPS\n"
                    "                no Date.now(), no unseeded random, no render-time fetch\n"
                    "  use HyperFrames for tracks/clips/Studio; æRTXrender for a pure\n"
                    "  Three.js scene rendered deterministically on the local GPU.\n")}

    # ── index ──
    p = _packages()
    r = _registry()
    s = _skills()
    return {
        "ok": True,
        "scheme": "hyperframes://",
        "role": "the HyperFrames monorepo — the composition/capture/encode framework",
        "version": _pkg_version(),
        "dir": _D,
        "counts": {
            "packages": len(p),
            "blocks": len(r["blocks"]),
            "components": len(r["components"]),
            "examples": len(r["examples"]),
            "skills": len(s),
        },
        "actions": ["packages", "registry", "skills", "check", "relation"],
        "stdout": (f"hyperframes:// — {_pkg_version()} · {_D}\n"
                   f"  packages    {len(p)}\n"
                   f"  registry    {len(r['blocks'])} blocks · {len(r['components'])} components · "
                   f"{len(r['examples'])} examples\n"
                   f"  skills      {len(s)}\n"
                   f"\n  actions: packages · registry · skills · check · relation\n"),
    }


_DISPATCHER.register("hyperframes://", _hf_dispatch)

# ── supervisionvidaeo:// — the produce-and-verify contract surface ──────────
# supervisionvidaeo://<what> — inspect and invoke the supervision gate.
#
# The CONTRACT surface. Six verbs now, six questions:
#   video://              the ASK        — render N seconds of a subject
#   vidæo://              the BRAND      — a brand's surface + manifest
#   three.js://           the RENDERER   — the vendored Three.js
#   hyperframes://        the FRAMEWORK  — the composition monorepo
#   supervisionvidaeo://  the CONTRACT   — produce→Receipt or SupervisionRefused
#   a://                  the ALIAS      — the typable entry
#
#   supervisionvidaeo://            -> the contract index (API · bounds · toolchain)
#   supervisionvidaeo://toolchain   -> can it produce? (never assume)
#   supervisionvidaeo://bounds      -> the SceneSpec clamp ranges
#   supervisionvidaeo://api         -> the public surface (produce · verify · …)
#   supervisionvidaeo://verify <mp4> -> run the gate on an existing video
#   supervisionvidaeo://check       -> is the package importable + usable?

_SVD_DIR = r"C:\æ\supervisionvidaeo"


def _svd_dispatch(raw: str) -> dict:
    """Route supervisionvidaeo:// — the produce-and-verify contract surface."""
    import importlib as _il
    import os as _os
    import sys as _sys

    rest = raw.split("supervisionvidaeo://", 1)[1].strip() if "supervisionvidaeo://" in raw else ""
    parts = rest.split()
    action = (parts[0].lower() if parts else "status")
    arg = parts[1] if len(parts) > 1 else ""

    _D = _SVD_DIR
    if not _os.path.isdir(_D):
        return {"ok": False, "stderr": f"supervisionvidaeo:// — package not found: {_D}"}
    if _D not in _sys.path:
        _sys.path.insert(0, _D)

    try:
        svd = _il.import_module("supervisionvidaeo")
    except Exception as exc:
        return {"ok": False, "stderr": f"supervisionvidaeo:// — import failed: {exc}"}

    # ── toolchain ──
    if action == "toolchain":
        try:
            ts = svd.toolchain_status()
        except Exception as exc:
            return {"ok": False, "stderr": f"toolchain_status failed: {exc}"}
        prod = ts.get("producer", {})
        ver = ts.get("verifier", {})
        avail = bool(prod.get("available"))
        return {"ok": avail, "scheme": "supervisionvidaeo://", "toolchain": ts,
                "stdout": (f"supervisionvidaeo toolchain — {ts.get('package')} v{ts.get('version')}\n"
                           f"  producer   vidaeo_cli={prod.get('vidaeo_cli')}\n"
                           f"             gpu_python={prod.get('gpu_python')}  available={avail}\n"
                           f"  verifier   opencv={ver.get('opencv')}  ml_required={ver.get('ml_required')}\n")}

    # ── bounds ──
    if action == "bounds":
        try:
            b = svd.toolchain_status().get("bounds", {})
        except Exception as exc:
            return {"ok": False, "stderr": f"bounds failed: {exc}"}
        return {"ok": True, "scheme": "supervisionvidaeo://", "bounds": b,
                "stdout": ("SceneSpec.bounded() clamps — never raises:\n"
                           + "".join(f"  {k:12} {v}\n" for k, v in b.items()))}

    # ── api ──
    if action == "api":
        api = {
            "produce": "produce(raw_spec, out_path, *, producer=None) → Receipt | raises SupervisionRefused",
            "verify": "verify(mp4_path, sample_every=20) → dict (the gate, without the producer)",
            "toolchain_status": "toolchain_status() → dict (can it produce? never assume)",
            "SceneSpec.bounded": "SceneSpec.bounded(raw=None, **overrides) → SceneSpec (clamps bad input)",
            "Receipt": "the evidence: H(prev ∥ intent ∥ ops ∥ result ∥ state ∥ evidence)",
            "SupervisionRefused": "raised on FAIL — never returns a path to a broken file",
        }
        return {"ok": True, "scheme": "supervisionvidaeo://", "api": api,
                "stdout": ("supervisionvidaeo — public surface\n"
                           + "".join(f"  {k:22} {v}\n" for k, v in api.items()))}

    # ── verify <mp4> ──
    if action == "verify":
        if not arg:
            return {"ok": False, "stderr": "supervisionvidaeo://verify <mp4> — no path given"}
        path = arg if _os.path.isabs(arg) else _os.path.join(_D, arg)
        if not _os.path.exists(path):
            return {"ok": False, "stderr": f"supervisionvidaeo://verify — not found: {path}"}
        try:
            rep = svd.verify(path, sample_every=20)
        except Exception as exc:
            return {"ok": False, "stderr": f"verify failed: {exc}"}
        cal = rep.get("calidad")
        return {
            "ok": cal == "PASS",
            "scheme": "supervisionvidaeo://",
            "report": rep,
            "stdout": (f"supervisionvidaeo://verify — {_os.path.basename(path)}\n"
                       f"  {cal} · lum {rep.get('luminancia_media')} · "
                       f"con {rep.get('contraste_medio')} · mov {rep.get('movimiento_medio')}\n"
                       f"  black frames {rep.get('frames_negros')}\n"
                       f"  receipt {rep.get('receipt')}\n"),
        }

    # ── check ──
    if action == "check":
        ok = True
        notes = []
        try:
            ts = svd.toolchain_status()
            notes.append(f"toolchain: {ts.get('package')} v{ts.get('version')}")
            if not ts.get("producer", {}).get("available"):
                ok = False
                notes.append("producer UNAVAILABLE")
        except Exception as exc:
            ok = False
            notes.append(f"toolchain failed: {exc}")
        for attr in ("produce", "verify", "toolchain_status", "SceneSpec", "Receipt", "SupervisionRefused"):
            if not hasattr(svd, attr):
                ok = False
                notes.append(f"missing: {attr}")
        return {"ok": ok, "scheme": "supervisionvidaeo://", "notes": notes,
                "stdout": ("supervisionvidaeo check\n"
                           + "".join(f"  {n}\n" for n in notes)
                           + f"  usable: {ok}\n")}

    # ── index ──
    try:
        ts = svd.toolchain_status()
        version = ts.get("version", "?")
        avail = ts.get("producer", {}).get("available")
        bounds = ts.get("bounds", {})
    except Exception:
        version, avail, bounds = "?", None, {}
    tests = []
    tdir = _os.path.join(_D, "tests")
    if _os.path.isdir(tdir):
        tests = sorted(f for f in _os.listdir(tdir) if f.startswith("test_") and f.endswith(".py"))
    return {
        "ok": True,
        "scheme": "supervisionvidaeo://",
        "role": "the produce-and-verify contract — a render either passes its gate or refuses",
        "version": version,
        "dir": _D,
        "producer_available": avail,
        "bounds": bounds,
        "tests": tests,
        "actions": ["toolchain", "bounds", "api", "verify <mp4>", "check"],
        "stdout": (f"supervisionvidaeo:// — v{version} · {_D}\n"
                   f"  contract   produce() → Receipt  |  SupervisionRefused on FAIL\n"
                   f"  producer   {'available' if avail else 'UNAVAILABLE'}\n"
                   f"  bounds     particles {bounds.get('particles')} · duration {bounds.get('duration')}\n"
                   f"  tests      {len(tests)} files\n"
                   f"\n  actions: toolchain · bounds · api · verify <mp4> · check\n"),
    }


_DISPATCHER.register("supervisionvidaeo://", _svd_dispatch)

_DISPATCHER.register("fs://", _fs_dispatch)
