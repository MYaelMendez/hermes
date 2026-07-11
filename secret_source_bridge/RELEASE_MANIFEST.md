# secret_source_bridge — Release Manifest

Release status: draft
Milestone: secret_source_bridge
Origin point: privateclient.ai

## Verification

| Check | Command | Result |
|-------|---------|--------|
| pytest | `pytest secret_source_bridge/tests.py` | 20 passed |
| computer_use pytest | `pytest tests/hermes_runtime/test_computer_use.py` | 8 passed |
| html bridge verification | ad-hoc checker | 20/20 checks passed |
| vscode-remote-use compile | `npm run compile` | exit 0 |

## Packaging

- Artifact: `vscode-remote-use-0.1.0.vsix`
- Size: `199763` bytes
- SHA256: `8f29158d4f3a3b99cba86a2dbe07a773ece5553d18438d6ad142a431c12f6187`

## Boundary

- Boundary doc: `secret_source_bridge/OPENSOURCEWARE_BOUNDARY.md`
- Keep-out: secrets, tokens, passwords, auth.json, machine-specific paths
- Keep-in: plugin source, server, tests, boundary/release docs

## Next

- Register `local_bridge` in Hermes config.yaml as default secret source
- Wire HTML bridge ui to backend broker
- Validate no raw secrets flow across Hermes secret-source boundary
