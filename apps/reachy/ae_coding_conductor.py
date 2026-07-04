from fastapi import APIRouter
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
            metadata={"role": "orchestrator"},
        ),
        PCSurfaceContract(
            id="viewport",
            agent="hermes-viewport",
            sandbox="surface",
            address="pc://viewport",
            metadata={"role": "c2-shell"},
        ),
        PCSurfaceContract(
            id="media",
            agent="ffmpeg",
            sandbox="media",
            address="pc://media",
            metadata={"role": "media-pipeline"},
        ),
        PCSurfaceContract(
            id="vscode",
            agent="vscode-bridge",
            sandbox="editor",
            address="pc://vscode",
            metadata={"role": "editor-control-plane"},
        ),
    ]
    for surface in defaults:
        MESH.register(surface)


class PlanRequest(BaseModel):
    intent: str
    target_dir: str | None = WORKSPACE


class RunRequest(BaseModel):
    agent: str = "hermes-local"
    intent: str
    files: list[str] | None = None


class SurfaceRequest(BaseModel):
    id: str
    agent: str
    sandbox: str
    address: str
    metadata: dict | None = None


@router.get("/health")
def health():
    _ensure_mesh()
    return {
        "ok": True,
        "surface": "ae-engineering-hub",
        "workdir": WORKSPACE,
        "mesh_surfaces": len(MESH._surfaces),
    }


@router.get("/plan")
def plan_get(intent: str = "", target_dir: str = WORKSPACE):
    _ensure_mesh()
    return {
        "mode": "plan",
        "intent": intent,
        "target": target_dir,
        "steps": ["scope", "trace", "execute", "verify", "commit"],
        "agents": ["hermes-agent", "claude-code", "codex", "opencode"],
        "mesh": {
            "default_client": "conductor",
            "available": [s["id"] for s in MESH.list_surfaces()],
        },
    }


@router.post("/plan")
def plan_post(req: PlanRequest):
    _ensure_mesh()
    return {
        "mode": "plan",
        "intent": req.intent,
        "target": req.target_dir,
        "steps": ["scope", "trace", "execute", "verify", "commit"],
        "agents": ["hermes-agent", "claude-code", "codex", "opencode"],
        "mesh": {
            "default_client": "conductor",
            "available": [s["id"] for s in MESH.list_surfaces()],
        },
    }


@router.post("/run")
def run(req: RunRequest):
    _ensure_mesh()
    surface = MESH.surface(req.agent.split("/", 1)[-1] if "/" in req.agent else req.agent)
    agent = surface.agent if surface else req.agent
    surface_id = surface.id if surface else req.agent
    address = surface.address if surface else f"pc://{req.agent}"
    sandbox = surface.sandbox if surface else "workspace"
    return {
        "ok": True,
        "mode": "run",
        "agent": agent,
        "intent": req.intent,
        "scope": {
            "workdir": WORKSPACE,
            "recent_files": req.files or [],
            "private_client": address,
            "sandbox": sandbox,
        },
    }


@router.post("/trace")
def trace(intent: str = "", payload: dict | None = None):
    _ensure_mesh()
    return {
        "ok": True,
        "mode": "trace",
        "intent": intent,
        "path": ["intent", "plan", "execute", "verify", "surface"],
        "latest_payload": payload or {},
        "mesh": {
            "default_client": "conductor",
            "available": [s["id"] for s in MESH.list_surfaces()],
        },
    }


@router.get("/skills")
def skills():
    _ensure_mesh()
    return {
        "surface": "ae-engineering-hub",
        "skills": [
            "hermes-operator-grammar",
            "subagent-driven-development",
            "test-driven-development",
            "systematic-debugging",
            "code-review",
            "plan",
            "requesting-code-review",
        ],
        "mesh": [s["id"] for s in MESH.list_surfaces()],
    }


@router.get("/agents")
def agents():
    _ensure_mesh()
    return {
        "surface": "ae-engineering-hub",
        "agents": [
            "hermes-agent",
            "claude-code",
            "codex",
            "opencode",
        ],
        "mesh": [s["id"] for s in MESH.list_surfaces()],
    }


@router.get("/workspace")
def workspace():
    _ensure_mesh()
    return {"workdir": WORKSPACE}


@router.get("/mesh/surfaces")
def mesh_surfaces():
    _ensure_mesh()
    return {
        "ok": True,
        "mode": "mesh",
        "default_client": "conductor",
        "surfaces": MESH.list_surfaces(),
    }


@router.post("/mesh/dispatch/{id}")
def mesh_dispatch(id: str, payload: dict | None = None):
    _ensure_mesh()
    return MESH.dispatch(id, payload)


@router.post("/mesh/register")
def mesh_register(req: SurfaceRequest):
    _ensure_mesh()
    surface = PCSurfaceContract(
        id=req.id,
        agent=req.agent,
        sandbox=req.sandbox,
        address=req.address,
        metadata=req.metadata or {},
    )
    registered = MESH.register(surface)
    return {
        "ok": True,
        "mode": "mesh",
        "surface": {
            "id": registered.id,
            "address": registered.address,
            "agent": registered.agent,
            "sandbox": registered.sandbox,
            "metadata": registered.metadata,
        },
    }
