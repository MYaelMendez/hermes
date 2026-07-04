from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from apps.reachy.pc_mesh import MESH, PCSurfaceContract

router = APIRouter()
WORKSPACE = r"C:\æ\hermes-fork"

_MESH_INITIALIZED = False


def _ensure_mesh() -> None:
    global _MESH_INITIALIZED
    if _MESH_INITIALIZED:
        return
    _MESH_INITIALIZED = True
    defaults = [
        PCSurfaceContract(
            id="conductor",
            agent="hermes-agent",
            sandbox="workspace",
            address="pc://conductor",
            metadata={"role": "orchestrator", "namespace": "global"},
        ),
        PCSurfaceContract(
            id="viewport",
            agent="hermes-viewport",
            sandbox="surface",
            address="pc://viewport",
            metadata={"role": "c2-shell", "namespace": "global"},
        ),
        PCSurfaceContract(
            id="media",
            agent="ffmpeg",
            sandbox="media",
            address="pc://media",
            metadata={"role": "media-pipeline", "namespace": "global"},
        ),
        PCSurfaceContract(
            id="vscode",
            agent="vscode-bridge",
            sandbox="editor",
            address="pc://vscode",
            metadata={"role": "editor-control-plane", "namespace": "global"},
        ),
    ]
    for surface in defaults:
        MESH.register_global(surface)


class PlanRequest(BaseModel):
    intent: str
    target_dir: str | None = WORKSPACE
    user: str | None = None


class RunRequest(BaseModel):
    agent: str = "hermes-local"
    intent: str
    files: list[str] | None = None
    user: str | None = None


class SurfaceRequest(BaseModel):
    id: str
    agent: str
    sandbox: str
    address: str
    metadata: dict | None = None


class AgentRequest(BaseModel):
    agent: str
    intent: str


@router.get("/health")
def health():
    _ensure_mesh()
    return {
        "ok": True,
        "surface": "ae-engineering-hub",
        "workdir": WORKSPACE,
        "mesh_global_surfaces": len(MESH._global),
        "mesh_namespaces": MESH.namespaces(),
    }


@router.get("/plan")
def plan_get(intent: str = "", target_dir: str = WORKSPACE, user: str | None = None):
    _ensure_mesh()
    namespace = MESH.namespace(user)
    return {
        "mode": "plan",
        "user": user or MESH.default_user,
        "intent": intent,
        "target": target_dir,
        "steps": ["scope", "trace", "execute", "verify", "commit"],
        "agents": ["hermes-agent", "claude-code", "codex", "opencode"],
        "mesh": {
            "default_client": "conductor",
            "namespace": user or MESH.default_user,
            "available_global": [s["id"] for s in _global_surfaces()],
            "available_user": [s["id"] for s in namespace.list_surfaces()],
        },
    }


@router.post("/plan")
def plan_post(req: PlanRequest):
    _ensure_mesh()
    namespace = MESH.namespace(req.user)
    return {
        "mode": "plan",
        "user": req.user or MESH.default_user,
        "intent": req.intent,
        "target": req.target_dir,
        "steps": ["scope", "trace", "execute", "verify", "commit"],
        "agents": ["hermes-agent", "claude-code", "codex", "opencode"],
        "mesh": {
            "default_client": "conductor",
            "namespace": req.user or MESH.default_user,
            "available_global": [s["id"] for s in _global_surfaces()],
            "available_user": [s["id"] for s in namespace.list_surfaces()],
        },
    }


@router.post("/run")
def run(req: RunRequest):
    _ensure_mesh()
    mesh_user = req.user or MESH.default_user
    agent_key = req.agent.split("/", 1)[-1] if "/" in req.agent else req.agent
    surface = MESH.surface_global(agent_key) or MESH.namespace(mesh_user).surface(agent_key)
    agent = surface.agent if surface else req.agent
    address = surface.address if surface else f"pc://{req.agent}"
    sandbox = surface.sandbox if surface else "workspace"
    return {
        "ok": True,
        "mode": "run",
        "agent": agent,
        "intent": req.intent,
        "user": mesh_user,
        "scope": {
            "workdir": WORKSPACE,
            "recent_files": req.files or [],
            "private_client": address,
            "sandbox": sandbox,
        },
    }


@router.post("/trace")
def trace(intent: str = "", payload: dict | None = None, user: str | None = None):
    _ensure_mesh()
    return {
        "ok": True,
        "mode": "trace",
        "user": user or MESH.default_user,
        "intent": intent,
        "path": ["intent", "plan", "execute", "verify", "surface"],
        "latest_payload": payload or {},
        "mesh": {
            "default_client": "conductor",
            "namespace": user or MESH.default_user,
            "available_global": [s["id"] for s in _global_surfaces()],
        },
    }


@router.get("/skills")
def skills():
    _ensure_mesh()
    return {
        "surface": "ae-engineering-hub",
        "conductor": "hermes-agent",
        "skills": [
            "hermes-operator-grammar",
            "subagent-driven-development",
            "test-driven-development",
            "systematic-debugging",
            "code-review",
            "plan",
            "requesting-code-review",
        ],
        "mesh": {
            "global": [s["id"] for s in _global_surfaces()],
            "namespaces": MESH.namespaces(),
            "local": [s["id"] for s in MESH.namespace(MESH.default_user).list_surfaces()],
        },
    }


@router.get("/agents")
def agents():
    _ensure_mesh()
    return {
        "surface": "ae-engineering-hub",
        "conductor": "hermes-agent",
        "agents": [
            "hermes-agent",
            "claude-code",
            "codex",
            "opencode",
        ],
        "mesh": {
            "global": [s["id"] for s in _global_surfaces()],
            "namespaces": MESH.namespaces(),
            "local": [s["id"] for s in MESH.namespace(MESH.default_user).list_surfaces()],
        },
    }


@router.get("/workspace")
def workspace():
    return {"workdir": WORKSPACE}


@router.get("/mesh/namespaces")
def mesh_namespaces():
    _ensure_mesh()
    return {
        "ok": True,
        "mode": "mesh",
        "default": MESH.default_user,
        "namespaces": MESH.namespaces(),
        "global_surfaces": [s["id"] for s in _global_surfaces()],
    }


@router.get("/mesh/global/surfaces")
def mesh_global_surfaces():
    _ensure_mesh()
    return {
        "ok": True,
        "mode": "mesh",
        "namespace": "global",
        "surfaces": _global_surfaces(),
    }


@router.post("/mesh/global/dispatch/{id}")
def mesh_global_dispatch(id: str, payload: dict | None = None):
    _ensure_mesh()
    return MESH.dispatch_global(id, payload)


@router.get("/mesh/surfaces")
def mesh_local_surfaces(user: str | None = None):
    _ensure_mesh()
    namespace = MESH.namespace(user)
    return {
        "ok": True,
        "mode": "mesh",
        "namespace": user or MESH.default_user,
        "surfaces": namespace.list_surfaces(),
    }


@router.post("/mesh/dispatch/{id}")
def mesh_local_dispatch(id: str, payload: dict | None = None, user: str | None = None):
    _ensure_mesh()
    namespace = MESH.namespace(user)
    return namespace.dispatch(id, payload)


@router.post("/mesh/register")
def mesh_register(req: SurfaceRequest, user: str | None = None):
    _ensure_mesh()
    namespace = MESH.namespace(user)
    surface = PCSurfaceContract(
        id=req.id,
        agent=req.agent,
        sandbox=req.sandbox,
        address=req.address,
        metadata=req.metadata or {},
    )
    registered = namespace.register(surface)
    return {
        "ok": True,
        "mode": "mesh",
        "user": user or MESH.default_user,
        "surface": {
            "id": registered.id,
            "address": registered.address,
            "agent": registered.agent,
            "sandbox": registered.sandbox,
            "metadata": registered.metadata,
        },
    }


def _global_surfaces() -> List[Dict[str, Any]]:
    out = []
    for id in MESH._global_order:
        s = MESH._global[id]
        out.append({
            "id": s.id,
            "address": s.address,
            "agent": s.agent,
            "sandbox": s.sandbox,
        })
    return out
