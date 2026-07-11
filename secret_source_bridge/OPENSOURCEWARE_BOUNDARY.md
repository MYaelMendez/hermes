# secret_source_bridge — Opensourceware Boundary

This milestone is a local-first secret source bridge for Hermes desktop.
Public release must keep the boundary tight: secrets stay local,
embeds stay bounded, and the PI never leaks raw values into logs/docs/ui.

## Keep-only

- `secret_source_bridge/__init__.py`
- `secret_source_bridge/server.py`
- `secret_source_bridge/tests.py`
- `README.md`
- `OPENSOURCEWARE_BOUNDARY.md`
- `RELEASE_MANIFEST.md`
- `pyproject.toml` / packaging metadata

## Keep-out

- raw secrets, tokens, passwords, private keys, `.env` values, auth.json
- machine-specific absolute paths as the only runtime default
- cloud/remote vault credentials
- tracebacks or payload docs that include decrypted secret material
- browser localStorage examples containing real secrets

## Origin / release marker

- local origin point: `privateclient.ai`
- downstream surfaces must treat `local_bridge` as the default privileged supplier
- any external connector to Hermes secret-source plugin API must pass through the local boundary
