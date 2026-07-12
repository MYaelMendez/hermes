"""serve_neuromitosis.py — live co-webmastering bridge for neuromitosis.com.

Serves neuromitosis.com.html and a /wiring.json endpoint that pulls the REAL
neuromitosis:// map from the chassis (hermes_cli.conductor._dispatch), so the
site reflects the bonded H+Robot+DAO state live. Run from C:\\ae\\hermes-fork:

    PYTHONPATH="$PWD" python serve_neuromitosis.py
    -> http://127.0.0.1:8090  (site)   /   /wiring.json (live chassis map)
"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

PORT = int(os.environ.get("NEURO_PORT", "8092"))


def wiring_payload() -> dict:
    """Pull the live neuromitosis:// map from the chassis."""
    try:
        from hermes_cli.conductor import _dispatch
        r = _dispatch("neuromitosis://")
        surf = r.get("surface", {})
        wired = surf.get("wired_surfaces", [])
        # enrich each with the detail line from the dispatch stdout
        detail_map = {}
        for line in r.get("stdout", "").splitlines():
            for s in wired:
                if line.strip().startswith(s):
                    detail_map[s] = line.strip()[len(s):].strip()
        return {
            "ok": True,
            "scheme": "neuromitosis://",
            "equals": "Hæbbian://",
            "reset_ready": surf.get("reset_ready", False),
            "skill": surf.get("skill", "agentic-chassis-surface"),
            "memory_triggers": surf.get("memory_triggers", 0),
            "meta_memory": surf.get("meta_memory", {"entries": 0, "rows": [], "discipline": ""}),
            "wired_surfaces": [
                {"scheme": s, "detail": detail_map.get(s, "")} for s in wired
            ],
        }
    except Exception as e:  # pragma: no cover
        return {"ok": False, "error": str(e), "wired_surfaces": []}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path == "/wiring.json":
            body = json.dumps(wiring_payload()).encode("utf-8")
            self._send(200, body, "application/json")
            return
        if path == "/mesh.json":
            body = json.dumps(mesh_payload()).encode("utf-8")
            self._send(200, body, "application/json")
            return
        if path in ("/", "/index.html", "/neuromitosis.com.html"):
            f = os.path.join(HERE, "neuromitosis.com.html")
            self._send(200, open(f, "rb").read(), "text/html; charset=utf-8")
            return
        self._send(404, b"not found", "text/plain")

    def do_POST(self):  # noqa: N802
        # Code Mode surface: POST bæsic code to /compose, get back only results.
        if self.path.split("?", 1)[0] != "/compose":
            self._send(404, b"not found", "text/plain")
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            code = self.rfile.read(length).decode("utf-8")
        except Exception as e:  # pragma: no cover
            self._send(400, json.dumps({"ok": False, "error": str(e)}).encode(), "application/json")
            return
        try:
            from hermes_cli.conductor import _dispatch
            res = _dispatch("+bæsic:// compose " + code)
            out = res.get("stdout", "") + res.get("stderr", "")
            self._send(200, json.dumps({"ok": res["ok"], "output": out}).encode(), "application/json")
        except Exception as e:  # pragma: no cover
            self._send(500, json.dumps({"ok": False, "error": str(e)}).encode(), "application/json")

    def log_message(self, *args):  # silence default logging
        pass


def mesh_payload() -> dict:
    """The MoD topology — sovereign nodes (from llm.store/ae white paper).

    neuromitosis.com is a bonded node: Human + Robot + DAO wired via Hæbbian.
    +æ://secrets is the vault node: surface on github.io, custody on Victus
    (C:\\æ\\secrets\\). No secret value ever crosses to the surface or this mesh.
    """
    nodes = [
        {"domain": "cli.llc", "role": "Build — agentic infrastructure: APIs, MCPs, CLIs. You own the namespace.", "bonded": False},
        {"domain": "daollc.ai", "role": "Entity — sovereign DAO LLC formation in Wyoming.", "bonded": False},
        {"domain": "llm.store", "role": "Intelligence — æπ combinator: models, reasoning, interface.", "bonded": False},
        {"domain": "æ.store", "role": "Commerce — agentic email, e-commerce, IOA.", "bonded": False},
        {"domain": "æl.net", "role": "Arrival — where agents begin. Entry point to the topology.", "bonded": False},
        {"domain": "+æ://secrets", "role": "Vault — local-first secret broker. Surface: github.io/secret-source-bridge. Custody: Victus C:\\æ\\secrets\\. No value crosses.", "bonded": False},
        {"domain": "neuromitosis.com", "role": "Bond — Human + Robot + DAO, wired via Hæbbian. This node.", "bonded": True},
    ]
    return {"ok": True, "topology": "MoD", "nodes": nodes}


def main() -> None:
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"neuromitosis.com live at http://127.0.0.1:{PORT}  (Ctrl+C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    main()
