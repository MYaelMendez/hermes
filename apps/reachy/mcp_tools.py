"""MCP tools bridge for Hermes conductor."""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/mcp/tools")
async def mcp_tools() -> JSONResponse:
    return JSONResponse({
        "ok": True,
        "tools": [
            {"name": "filesystem", "desc": "read/write/list workspace files"},
            {"name": "exec", "desc": "run bounded shell commands"},
            {"name": "search", "desc": "search repo symbols/content"},
            {"name": "browser", "desc": "headless browser actions"},
            {"name": "vision", "desc": "image/screenshot understanding"},
        ],
    })


@router.post("/mcp/invoke")
async def mcp_invoke(payload: dict) -> JSONResponse:
    tool = str(payload.get("tool", "")).strip()
    args = dict(payload.get("args", {}) or {})
    if not tool:
        return JSONResponse({"ok": False, "rc": 2, "stdout": "", "stderr": "missing tool"})
    return JSONResponse({
        "ok": True,
        "rc": 0,
        "stdout": json.dumps({"tool": tool, "args": args}),
        "stderr": "",
    })
