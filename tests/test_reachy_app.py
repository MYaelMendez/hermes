from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from apps.reachy.app import app


client = TestClient(app)


def test_vlc_play_missing_target():
    response = client.post("/vlc/play", json={})
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert data["rc"] == 2
    assert data["stderr"] == "missing target"
    assert data["stdout"] == ""
    assert data["surface"] == {
        "kind": "vlc_surface",
        "address": "vlc://play/",
        "target": "",
        "runtime": "hermes-code",
    }


def test_vlc_play_success():
    fake_result = {
        "ok": True,
        "rc": 0,
        "stdout": "vlc://status pid=123 target=/tmp/sample.mp4\n",
        "stderr": "",
        "running": True,
        "pid": 123,
        "target": "/tmp/sample.mp4",
        "runtime": "hermes-code",
    }
    with patch("apps.reachy.app.VLCController.play", return_value=fake_result) as mock_play:
        response = client.post("/vlc/play", json={"target": "/tmp/sample.mp4"})
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["rc"] == 0
    assert "pid=123" in data["stdout"]
    assert data["surface"]["address"] == "vlc://play//tmp/sample.mp4"
    assert data["surface"]["target"] == "/tmp/sample.mp4"
    assert data["surface"]["runtime"] == "hermes-code"
    assert data["surface"]["kind"] == "vlc_surface"
    mock_play.assert_called_once_with("/tmp/sample.mp4")


def test_vlc_play_launch_failure():
    with patch("apps.reachy.app.VLCController.play", side_effect=RuntimeError("vlc executable not found")):
        response = client.post("/vlc/play", json={"target": "/tmp/missing.mp4"})
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert data["rc"] == 1
    assert "vlc executable not found" in data["stderr"]
    assert data["surface"]["address"] == "vlc://play//tmp/missing.mp4"


def test_vlc_fleet_status():
    fake_fleet = {
        "ok": True,
        "rc": 0,
        "stdout": "vlc://fleet status members=1\n",
        "stderr": "",
        "surface": {
            "kind": "vlc_fleet",
            "address": "vlc://fleet",
            "runtime": "hermes-code",
            "members": [
                {
                    "name": "victus-local",
                    "address": "pc://mesh/victus/local/vlc",
                    "role": "local",
                    "runtime": "hermes-code",
                    "status": "idle",
                    "ok": False,
                }
            ],
            "glocal": {
                "local": "pc://mesh/victus/local/vlc",
                "global": "pc://mesh/global/vlc",
            },
        },
        "token": "mech:vlc:status:node=fleet:runtime=hermes-code",
    }
    with patch("apps.reachy.app.vlc_fleet.dispatch", return_value=fake_fleet) as mock_dispatch:
        response = client.post("/vlc/fleet/status")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["surface"]["kind"] == "vlc_fleet"
    assert data["token"].startswith("mech:vlc:status")
    mock_dispatch.assert_called_once_with("vlc://fleet status")


def test_vlc_fleet_play():
    fake_play = {
        "ok": True,
        "rc": 0,
        "stdout": "vlc://fleet play victimus-local\n",
        "stderr": "",
        "surface": {
            "kind": "vlc_fleet",
            "address": "vlc://fleet/play/victus-local",
            "runtime": "hermes-code",
            "node": {
                "name": "victus-local",
                "address": "pc://mesh/victus/local/vlc",
                "role": "local",
                "runtime": "hermes-code",
                "status": "running",
            },
            "glocal": {
                "local": "pc://mesh/victus/local/vlc",
                "global": "pc://mesh/global/vlc",
            },
        },
        "token": "mech:vlc:play:node=victus-local:runtime=hermes-code",
    }
    with patch("apps.reachy.app.vlc_fleet.dispatch", return_value=fake_play) as mock_dispatch:
        response = client.post("/vlc/fleet/play", json={"target": "C:\\tmp\\x.mp4"})
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["surface"]["node"]["status"] == "running"
    mock_dispatch.assert_called_once_with("vlc://fleet play C:\\tmp\\x.mp4")


def test_vlc_fleet_stop():
    fake_stop = {
        "ok": True,
        "rc": 0,
        "stdout": "",
        "stderr": "",
        "surface": {
            "kind": "vlc_fleet",
            "address": "vlc://fleet/stop",
            "runtime": "hermes-code",
            "node": {"name": "victus-local", "status": "idle"},
        },
        "token": "mech:vlc:stop:node=victus-local:runtime=hermes-code",
    }
    with patch("apps.reachy.app.vlc_fleet.dispatch", return_value=fake_stop) as mock_dispatch:
        response = client.post("/vlc/fleet/stop")
    assert response.status_code == 200
    data = response.json()
    assert data["surface"]["node"]["status"] == "idle"
    mock_dispatch.assert_called_once_with("vlc://fleet stop")


def test_vlc_fleet_fullscreen():
    fake_fullscreen = {
        "ok": True,
        "rc": 0,
        "stdout": "",
        "stderr": "",
        "surface": {
            "kind": "vlc_fleet",
            "address": "vlc://fleet/fullscreen",
            "runtime": "hermes-code",
            "node": {"name": "victus-local", "status": "running"},
        },
        "token": "mech:vlc:fullscreen:node=victus-local:runtime=hermes-code",
    }
    with patch("apps.reachy.app.vlc_fleet.dispatch", return_value=fake_fullscreen) as mock_dispatch:
        response = client.post("/vlc/fleet/fullscreen")
    assert response.status_code == 200
    assert mock_dispatch.called


def test_vlc_fleet_runtime():
    fake_runtime = {
        "ok": True,
        "rc": 0,
        "stdout": "vlc://runtime agentic=vlc+superagent version=0.1\n",
        "stderr": "",
        "surface": {
            "kind": "vlc_fleet",
            "address": "vlc://runtime",
            "runtime": "hermes-code",
            "node": {"name": "victus-local", "status": "agentic-runtime"},
        },
        "token": "mech:vlc:runtime:node=victus-local:runtime=hermes-code",
    }
    with patch("apps.reachy.app.vlc_fleet.dispatch", return_value=fake_runtime) as mock_dispatch:
        response = client.post("/vlc/fleet/runtime")
    assert response.status_code == 200
    data = response.json()
    assert data["surface"]["node"]["status"] == "agentic-runtime"
    mock_dispatch.assert_called_once_with("vlc://fleet runtime")
