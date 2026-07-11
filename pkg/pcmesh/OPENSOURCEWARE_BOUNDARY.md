OPENSOURCEWARE BOUNDARY

This package boundary is intended for public release.
Do not include secrets, credentials, or private tokens here.

Origin: `privateclient.ai`
Milestone: `secret_source_bridge`

Keep-only:
- source/
- tests/
- LICENSE
- README.md
- pyproject.toml
- secret_source_bridge artifacts (`__init__.py`, `server.py`, `tests.py`)

Keep-out:
- .env
- auth.json
- any API keys, tokens, passwords, private keys
- any repo-specific paths or internal runtime assumptions not safely generalizable
- raw secret material in docs, logs, UI payloads, or badge examples
