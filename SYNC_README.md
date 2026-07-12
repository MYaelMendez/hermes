# Sync Index & Droplet PDS — local dev corpus

Indexing + synchronization of our sovereign blueprints / skills / strategies.

## Droplet (already live)
- `aevps` MCP² broker / sovereign-state PDS at `http://129.212.180.252:3000`
  (neuromitosis id 550039957, DO atl1). `compute: rtx3050://ready`.
- Record API: `POST /xrpc/ae.vps.record` with `{"nsid":..., "value":...}` → signed 201.
- Known nsids: `ae.core#sovereignState`, `ae.core#ledgerEvent`, `ae.core#meshPeer`, `ae.core#fleetNode`.
- Status: `GET /xrpc/ae.vps.status`.

## Local index
- `index_corpus.py` → walks `C:\æ\hermes-fork` (excl. vendored `website/`, `contest-submission/`,
  junk dirs), writes `SYNC_INDEX.json` (446 files: 373 skills, 23 blueprints, 11 docs,
  6 manifests, 32 other) + `SYNC_INDEX_EXT.json` (C:\æ outside fork; mostly cloned/temp repos).
- `SYNC_INDEX.json` carries path + size + first-heading title per file.

## Sync to droplet
- `sync_to_droplet.py` pushes:
  - `ae.core#sovereignState` → manifest (counts + generated + pointer)
  - `ae.core#ledgerEvent`   → each of the 23 blueprints (title+path+body)
  - `ae.core#meshPeer`      → skill/strategy index (422 paths+titles)
- Run: `python sync_to_droplet.py` (or `--dry-run`). Env `VPS_HOST`/`VPS_PORT` override.

## Reset recovery
`PYTHONPATH=. python index_corpus.py && python sync_to_droplet.py`
re-indexes locally and re-pushes to the droplet. The droplet is the durable
mirror; local `SYNC_INDEX.json` is the working copy.

## Edge contract
No secrets are indexed or synced. `+æ://secrets` (custody: `C:\æ\secrets\`) stays
local-only; only the vault node appears in the neuromitosis mesh surface.
