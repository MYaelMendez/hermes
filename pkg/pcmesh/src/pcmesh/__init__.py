from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class PCMeshContract:
    id: str
    agent: str
    sandbox: str
    address: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PCNode:
    id: str
    agent: str
    sandbox: str
    address: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "idle"
    last_seen: str = ""


class PCNamespace:
    def __init__(self, name: str) -> None:
        self.name = name
        self._nodes: Dict[str, PCNode] = {}
        self._order: List[str] = []

    def register(self, node: PCNode) -> PCNode:
        self._nodes[node.id] = node
        if node.id not in self._order:
            self._order.append(node.id)
        return node

    def node(self, id: str) -> Optional[PCNode]:
        return self._nodes.get(id)

    def dispatch(self, id: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        node = self.node(id)
        if not node:
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
            "stdout": f"pc://mesh/{self.name}/{id} -> {node.agent}\n",
            "stderr": "",
            "surface": {
                "kind": "private_client",
                "namespace": self.name,
                "id": node.id,
                "address": node.address,
                "agent": node.agent,
                "sandbox": node.sandbox,
                "dispatch": "bounded",
                "metadata": node.metadata,
            },
        }

    def list_nodes(self) -> List[Dict[str, Any]]:
        out = []
        for id in self._order:
            node = self._nodes[id]
            out.append({
                "id": node.id,
                "address": node.address,
                "agent": node.agent,
                "sandbox": node.sandbox,
                "status": node.status,
            })
        return out


class PCMesh:
    def __init__(self, default_user: str = "local") -> None:
        self.default_user = default_user
        self._namespaces: Dict[str, PCNamespace] = {}
        self._global: Dict[str, PCNode] = {}
        self._global_order: List[str] = []

    def namespace(self, user: Optional[str] = None) -> PCNamespace:
        name = user or self.default_user
        if name not in self._namespaces:
            self._namespaces[name] = PCNamespace(name=name)
        return self._namespaces[name]

    def register_global(self, node: PCNode) -> PCNode:
        self._global[node.id] = node
        if node.id not in self._global_order:
            self._global_order.append(node.id)
        return node

    def node_global(self, id: str) -> Optional[PCNode]:
        return self._global.get(id)

    def dispatch_global(self, id: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        node = self.node_global(id)
        if not node:
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
            "stdout": f"pc://{id} -> {node.agent}\n",
            "stderr": "",
            "surface": {
                "kind": "private_client",
                "namespace": "global",
                "id": node.id,
                "address": node.address,
                "agent": node.agent,
                "sandbox": node.sandbox,
                "dispatch": "bounded",
                "metadata": node.metadata,
            },
        }

    def namespaces(self) -> List[str]:
        return sorted(self._namespaces.keys())
