"""Minimal local HTTP bridge for secret_source_bridge.

Serves localhost hermiphication-safe operations from the local_bridge secret source.
"""
from __future__ import annotations

import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from secret_source_bridge import LocalBridgeSecretSource


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 7890
BASE_PATH = "/hermes/v1/secret"


class SecretBridgeHandler(BaseHTTPRequestHandler):
    plugin = LocalBridgeSecretSource()

    def log_message(self, format, *args):
        return

    def _cors(self, code=200, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "http://localhost:* http://127.0.0.1:*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._cors(204)
        self.wfile.write(b"")

    def _response(self, payload, code=200):
        self._cors(code)
        self.wfile.write(json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if not length:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _unwrap(self, result):
        doc = dict(result.document or {})
        doc.setdefault("selections", [])
        return {"document": doc}, 200

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.rstrip("/") == f"{BASE_PATH}/list":
            self._get_list()
            return
        if parsed.path.rstrip("/") == f"{BASE_PATH}/fetch":
            self._get_fetch()
            return
        self._response({"error": f"not found: {parsed.path}", "error_kind": "ACTION_NOT_ALLOWED"}, 404)

    def _get_list(self):
        qs = parse_qs(urlparse(self.path).query)
        kind = (qs.get("kind", [""])[0] or "").strip().lower() or None
        raw = self.plugin.action("list", {"kind": kind or ""})
        payload, code = self._unwrap(raw)
        self._response(payload, code)

    def _get_fetch(self):
        raw = self.plugin.fetch()
        payload, code = self._unwrap(raw)
        self._response(payload, code)

    def do_POST(self):
        parsed = urlparse(self.path)
        body = self._read_body()
        operation = body.get("operation") or (parsed.path.rstrip("/").split("/")[-1] or "")
        operation = (operation or "").strip().lower()
        if not operation:
            self._response({"error": "operation is required", "error_kind": "PAYLOAD_INVALID"}, 400)
            return
        allowed = {"validate_entry", "add", "update", "remove", "reveal", "export_env", "import_json", "clear", "stats", "search_by_kind", "bulk_upsert", "rotate_note"}
        if operation not in allowed:
            self._response({"error": f"unsupported operation: {operation}", "error_kind": "ACTION_NOT_ALLOWED"}, 400)
            return
        raw = self.plugin.action(operation, body if isinstance(body, dict) else {})
        payload, code = self._unwrap(raw)
        self._response(payload, code)


def run(host=None, port=None, plugin=None):
    if host is None:
        host = os.environ.get("HERMES_SECRET_BRIDGE_HOST", DEFAULT_HOST)
    if port is None:
        port = int(os.environ.get("HERMES_SECRET_BRIDGE_PORT", DEFAULT_PORT))
    if plugin is not None:
        SecretBridgeHandler.plugin = plugin
    server = HTTPServer((host, port), SecretBridgeHandler)
    print(f"secret_source_bridge server listening on http://{host}:{port}{BASE_PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
