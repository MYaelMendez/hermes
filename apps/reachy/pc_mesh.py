from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class PCSurfaceContract:
    id: str
    agent: str
    sandbox: str
    address: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class PCMesh:
    def __init__(self) -> None:
        self._surfaces: Dict[str, PCSurfaceContract] = {}
        self._order: List[str] = []

    def register(self, surface: PCSurfaceContract) -> PCSurfaceContract:
        self._surfaces[surface.id] = surface
        if surface.id not in self._order:
            self._order.append(surface.id)
        return surface

    def surface(self, id: str) -> Optional[PCSurfaceContract]:
        return self._surfaces.get(id)

    def dispatch(self, id: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        surface = self.surface(id)
        if not surface:
            return {
                "ok": False,
                "rc": 2,
                "stdout": "",
                "stderr": f"unknown pc:// surface: {id}",
                "surface": {"kind": "unknown"},
            }
        return {
            "ok": True,
            "rc": 0,
            "stdout": f"pc://{id} → {surface.agent}\n",
            "stderr": "",
            "surface": {
                "kind": "private_client",
                "id": surface.id,
                "address": surface.address,
                "agent": surface.agent,
                "sandbox": surface.sandbox,
                "dispatch": "bounded",
                "metadata": surface.metadata,
            },
        }

    def list_surfaces(self) -> List[Dict[str, Any]]:
        out = []
        for id in self._order:
            s = self._surfaces[id]
            out.append({
                "id": s.id,
                "address": s.address,
                "agent": s.agent,
                "sandbox": s.sandbox,
            })
        return out


MESH = PCMesh()
