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


class PCNamespace:
    def __init__(self, name: str, parent: "PCMesh") -> None:
        self.name = name
        self.parent = parent
        self._surfaces: Dict[str, PCSurfaceContract] = {}
        self._order: List[str] = []

    def register(self, surface: PCSurfaceContract) -> PCSurfaceContract:
        key = surface.id
        self._surfaces[key] = surface
        if key not in self._order:
            self._order.append(key)
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
                "stderr": f"unknown pc://surface: {self.name}/{id}",
                "surface": {"kind": "unknown"},
            }
        return {
            "ok": True,
            "rc": 0,
            "stdout": f"pc://mesh/{self.name}/{id} → {surface.agent}\\n",
            "stderr": "",
            "surface": {
                "kind": "private_client",
                "namespace": self.name,
                "id": surface.id,
                "address": surface.address,
                "agent": surface.agent,
                "sandbox": surface.sandbox,
                "dispatch": "bounded",
                "conductor": "hermes-agent",
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


class PCMesh:
    def __init__(self, default_user: str = "local") -> None:
        self.default_user = default_user
        self._namespaces: Dict[str, PCNamespace] = {}
        self._global: Dict[str, PCSurfaceContract] = {}
        self._global_order: List[str] = []

    def namespace(self, user: Optional[str] = None) -> PCNamespace:
        name = user or self.default_user
        if name not in self._namespaces:
            self._namespaces[name] = PCNamespace(name=name, parent=self)
        return self._namespaces[name]

    def register_global(self, surface: PCSurfaceContract) -> PCSurfaceContract:
        key = surface.id
        self._global[key] = surface
        if key not in self._global_order:
            self._global_order.append(key)
        return surface

    def surface_global(self, id: str) -> Optional[PCSurfaceContract]:
        return self._global.get(id)

    def dispatch_global(self, id: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        surface = self.surface_global(id)
        if not surface:
            return {
                "ok": False,
                "rc": 2,
                "stdout": "",
                "stderr": f"unknown global pc://surface: {id}",
                "surface": {"kind": "unknown"},
            }
        return {
            "ok": True,
            "rc": 0,
            "stdout": f"pc://{id} → {surface.agent}\\n",
            "stderr": "",
            "surface": {
                "kind": "private_client",
                "namespace": "global",
                "id": surface.id,
                "address": surface.address,
                "agent": surface.agent,
                "sandbox": surface.sandbox,
                "dispatch": "bounded",
                "conductor": "hermes-agent",
                "metadata": surface.metadata,
            },
        }

    def namespaces(self) -> List[str]:
        return sorted(self._namespaces.keys())


MESH = PCMesh(default_user="local")
