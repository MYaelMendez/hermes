"""Local launch helper for the secret_source_bridge system.

Starts the HTTP bridge backed by LocalBridgeSecretSource.

Defaults:
  Host: 127.0.0.1:7890
  Store: ~/.hermes/secrets/local_bridge.json
"""
from __future__ import annotations

import os

from secret_source_bridge.server import run
from secret_source_bridge import LocalBridgeSecretSource


def main() -> None:
    host = os.environ.get("HERMES_SECRET_BRIDGE_HOST", "127.0.0.1")
    port = int(os.environ.get("HERMES_SECRET_BRIDGE_PORT", "7890"))
    store_path = os.environ.get(
        "HERMES_SECRET_BRIDGE_PATH",
        str((Path.home() / ".hermes" / "secrets" / "local_bridge.json")),
    )
    os.environ["HERMES_SECRET_BRIDGE_PATH"] = store_path
    plugin = LocalBridgeSecretSource()
    run(host=host, port=port, plugin=plugin)


if __name__ == "__main__":
    main()
