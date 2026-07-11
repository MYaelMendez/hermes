# Hermes Secret Source Bridge

Local-first sovereign secret manager for Hermes desktop.
Origin point: `privateclient.ai`

## Boundaries

- No raw secrets in docs, logs, UI payloads, or example badges
- No cloud/remote vault dependencies
- All writes are atomic `.tmp` → rename
- All exports are local-file scoped

## Artifacts

- `secret_source_bridge/__init__.py` — SecretSource plugin
- `secret_source_bridge/server.py` — localhost broker
- `secret_source_bridge/tests.py` — conformance + behavior tests
- `config.example.yaml` — Hermes `secrets.sources` example

## Verification

- `pytest secret_source_bridge/tests.py` → 20 passed
- ad-hoc HTML bridge checker → checks passed

## Security

Store path defaults to `~/.hermes/secrets/local_bridge.json`.
Treat it like a local credential store: filesystem permissions only,
no remote sync, no browser sync, no telemetry.

# Hermes Secret Source Bridge

Local-first sovereign secret manager for Hermes desktop.
Origin point: `privateclient.ai`

## Setup

1. Copy `config.example.yaml` into your Hermes config as `secrets.sources`.
2. Ensure the store file is writable and set permissions to owner-only.
3. Restart Hermes desktop or reload plugins.

## Hermes config snippet

```yaml
secrets:
  redact_secrets: true
  sources:
    - name: local_bridge
      enabled: true
      override_existing: true
      timeout_seconds: 120
      path: ~/.hermes/secrets/local_bridge.json
```

## Environment override

- `HERMES_SECRET_BRIDGE_PATH` overrides the default store path.

## Actions API

The local_bridge source supports:

- add / update / remove
- list / reveal / search_by_kind
- export_env / import_json
- bulk_upsert / rotate_note / stats / clear

## Security stance

- No cloud/remote vault required
- No raw secrets in docs, logs, UI payloads, or README examples
- Store file should remain local and permission-restricted
