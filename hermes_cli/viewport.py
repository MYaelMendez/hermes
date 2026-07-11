"""Global Hermes viewport computer primitive."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _print(msg: str) -> None:
    print(msg, flush=True)


def _main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "open":
        host = "0.0.0.0"
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 5173
        surface = sys.argv[3] if len(sys.argv) > 3 else "http://127.0.0.1:7860"
        template = REPO / "templates" / "hermes-local-ai.html"
        if not template.exists():
            _print("template not found: " + str(template))
            return 2

        _print("Opening viewport: " + str(template))
        _print("Surface: " + surface)

        try:
            from fastapi import FastAPI, Request
            from fastapi.responses import HTMLResponse
            import uvicorn
        except Exception as e:
            _print("fastapi/uvicorn unavailable: " + str(e))
            return 3

        html = template.read_text(encoding="utf-8")
        app = FastAPI(title="Hermes Viewport", version="0.1")

        @app.get("/", response_class=HTMLResponse)
        async def index(_: Request) -> HTMLResponse:
            return HTMLResponse(html)

        @app.get("/health")
        async def health() -> dict:
            return {"ok": True, "service": "hermes-viewport"}

        _print("Serving on http://" + host + ":" + str(port))
        uvicorn.run(app, host=host, port=port)
        return 0
    print("Usage: python -m hermes_cli.viewport open <port?> <surface?>")
    return 2


def viewport_command(args) -> int:
    cmd = getattr(args, "viewport_action", None) or "status"
    if cmd == "open":
        return cmd_viewport_open(args)
    if cmd == "status":
        print("viewport: scaffolded")
        print("template: " + str(REPO / "templates" / "hermes-local-ai.html"))
        return 0
    print("unknown viewport action: " + cmd)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main())
