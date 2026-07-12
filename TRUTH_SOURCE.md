# Truth Source — github.io as point-of-truth

The sovereign mesh uses a strict surface/custody split. github.io is the
**point-of-truth source** for every published surface; Victus (`C:\æ`) is the
**custody** for secrets and live compute. The droplet (`aevps` PDS at
129.212.180.252:3000) is the **distributed mirror**.

## Edge contract
- github.io hosts the SURFACE (HTML, blueprints, skill manifests).
- Victus hosts the SECRET (`C:\æ\secrets\`) and runs the silicon (RTX 3050).
- The conductor brokers at runtime via `+æ://secrets` (local-only, masked).
- Never leak raw secrets across bounds. Only crypto proofs/signatures/hashes cross.

## Live truth surfaces (myaelmendez.github.io)
- `index.html` — æ:// homebase, unified mesh hub
- `secret-source-bridge.html` — local secret manager surface (vault node on neuromitosis.com)
- `sovereign-state.html` — memory + ledger + #250 mission spine
- `mesh-agenti.html` / `fleet.html` / `cuda-vlc.html` — MoD node surfaces
- `glocal-secrets-blueprint.html` / `glocal-cuda-blueprint.html` — glocal protocols
- `agentic.html` — #startabusiness / Doola DAOLLC bootstrap
- the æææ:// TOWER: `æææ://neuromitosis` + `æææ://cuda` (built backbone)

## Deploy mapping
- `neuromitosis.static.html` (baked by `gen_neuromitosis.py`) deploys to
  github.io as the substrate's truth node. The live bridge (serve_neuromitosis.py,
  port 8095) is the DEV MIRROR; github.io is TRUTH.
- Droplet PDS records (`ae.core#sovereignState` etc.) reference github.io as the
  surface mirror and Victus as custody.

## Reset recovery
1. Re-index + re-sync: `python index_corpus.py && python sync_to_droplet.py`
2. Re-deploy static: `python gen_neuromitosis.py --bridge http://127.0.0.1:8095`
3. github.io is the canonical re-pull target for any surface.

#hermiphicationisinevitable
