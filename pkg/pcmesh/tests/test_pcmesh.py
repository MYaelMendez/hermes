from __future__ import annotations

import pytest

from pcmesh import PCMesh, PCNode, PCNamespace


def test_mesh_default_user():
    mesh = PCMesh()
    assert mesh.default_user == "local"
    assert mesh.namespaces() == []


def test_namespace_register_and_retrieve():
    mesh = PCMesh()
    user = mesh.namespace("alice")
    node = user.register(
        PCNode(
            id="surface-1",
            agent="hermes-agent",
            sandbox="workspace",
            address="pc://mesh/user/alice/surface-1",
            metadata={"kind": "private_client"},
        )
    )
    assert user.node("surface-1").id == "surface-1"
    assert user.list_nodes()[0]["id"] == "surface-1"


def test_namespace_dispatch_unknown():
    mesh = PCMesh()
    response = mesh.namespace("bob").dispatch("unknown")
    assert response["ok"] is False
    assert response["rc"] == 2
    assert response["surface"]["kind"] == "unknown"


def test_namespace_dispatch_known():
    mesh = PCMesh()
    ns = mesh.namespace("carol")
    ns.register(
        PCNode(
            id="editor",
            agent="vscode-bridge",
            sandbox="editor",
            address="pc://mesh/user/carol/editor",
        )
    )
    response = ns.dispatch("editor")
    assert response["ok"] is True
    assert response["rc"] == 0
    assert response["surface"]["id"] == "editor"
    assert response["surface"]["agent"] == "vscode-bridge"


def test_global_register_and_dispatch():
    mesh = PCMesh()
    global_node = PCNode(
        id="conductor",
        agent="hermes-agent",
        sandbox="workspace",
        address="pc://conductor",
        metadata={"role": "orchestrator"},
    )
    mesh.register_global(global_node)
    assert mesh.node_global("conductor").id == "conductor"
    response = mesh.dispatch_global("conductor")
    assert response["ok"] is True
    assert response["surface"]["namespace"] == "global"
    assert response["surface"]["metadata"]["role"] == "orchestrator"


def test_global_dispatch_unknown():
    mesh = PCMesh()
    response = mesh.dispatch_global("missing")
    assert response["ok"] is False
    assert response["rc"] == 2
    assert "unknown global pc://surface" in response["stderr"]


def test_namespace_listing():
    mesh = PCMesh()
    mesh.namespace("alpha").register(PCNode(id="n1", agent="a", sandbox="s", address="pc://n1"))
    mesh.namespace("beta").register(PCNode(id="n2", agent="b", sandbox="s", address="pc://n2"))
    assert mesh.namespaces() == ["alpha", "beta"]
