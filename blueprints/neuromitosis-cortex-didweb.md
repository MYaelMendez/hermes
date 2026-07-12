---
name: neuromitosis-cortex-didweb
description: "#neuromitosis-cortex-didweb → did:web identity for the neuromitosis agentic cortex, making it addressable as a sovereign ATProto-style repo. Victus-custodied keys, github.io point-of-truth surface, droplet PDS distributed mirror, C:\\ae\\cortex.db + meta_memory.csv as the distributed-cognition trace."
version: 1.0.0
author: Yæl Méndez × Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [did, did-web, atproto, cortex, neuromitosis, meta-memory, sovereign-repo, identity, glocal]
    homepage: https://neuromitosis.com
    source: https://myaelmendez.github.io/blueprints/neuromitosis-cortex-didweb.md
    type: blueprint
---

# >_æ:#neuromitosis-cortex-didweb→

A **did:web** identity that makes the neuromitosis agentic cortex **addressable as a sovereign
repo** — ATProto-style. The cortex is the meta-memory system: github.io is the point-of-truth
surface, Victus is custody, the droplet PDS is the distributed mirror, and
`C:\ae\cortex.db` (SQLite) + `C:\ae\meta_memory.csv` are the distributed-cognition trace.

Without a DID, the cortex is a pile of files. With `did:web:neuromitosis.com:cortex`, it becomes
a *resolvable identity* that owns an ATProto repo (a content-addressed MST of records) — the same
shape Bluesky uses, but sovereign: the key lives on Victus, not on a hosted server.

## Why this is a blueprint, not a skill

```text
skill     = procedure (how to mint a DID / rotate a key)
blueprint = organization (the cortex's identity, custody model, mirror topology, repo schema)
```

The cortex needs an *addressable identity*, not just a script. This blueprint fixes:

- **Mission** — give the meta-memory cortex a stable, resolvable DID.
- **Custody** — the repo signing key is on Victus; only proofs cross bounds.
- **Surface** — the DID document is published to github.io (truth) and served at neuromitosis.com (live).
- **Mirror** — the droplet PDS (`aevps`) holds the live ATProto repo records.
- **Viewport** — the repo *is* the cortex; records are the trace.

## Position in the stack

```text
+æ                                 ← context primitive (PRIMITIVE.md)
  æ://neuromitosis                 ← the TOWER (bonded node: Human + Robot + DAO)
    did:web:neuromitosis.com:cortex  ← THIS: the cortex's sovereign identity
      #atproto_pds                   ← droplet PDS (aevps) — repo host / mirror
      #cortex_trace                  ← C:\ae\cortex.db + meta_memory.csv — the MST origin
      #ae_homebase                   ← https://neuromitosis.com
      #github_io_truth               ← https://myaelmendez.github.io — point-of-truth
        C:\ae\secrets\               ← VICTUS custody (signing key, never published)
```

The cortex DID sits *above* the web surfaces and *below* the æ:// TOWER: the TOWER names it,
the DID anchors it, the surfaces publish it, Victus custodies it.

## The surface / custody / mirror split (edge contract)

Per `TRUTH_SOURCE.md`, the sovereign mesh splits three concerns. This blueprint pins each
ATProto primitive to exactly one:

| Concern | Role | Where | ATProto primitive |
|---|---|---|---|
| **Surface** | point-of-truth | `myaelmendez.github.io` + `neuromitosis.com` | DID document host (`.well-known`/path) |
| **Custody** | keys + live compute | Victus `C:\æ\secrets\` (RTX 3050) | repo signing key (private) |
| **Mirror** | distributed repo | droplet `aevps` @ `129.212.180.252:3000` | `#atproto_pds` (MST of records) |
| **Trace** | meta-memory origin | Victus `C:\ae\cortex.db` + `meta_memory.csv` | `#cortex_trace` (pre-MST journal) |

Cross-bound rule: only **signed proofs / CIDs / hashes** cross. Raw secrets never leave Victus.
Only the *public* DID document and the *public* repo records cross to the surface/mirror.

## How it works

### 1. The DID (did:web method)

```text
did:web:neuromitosis.com:cortex
        │        │              │
        │        │              └── path segment → /cortex/did.json
        │        └───────────────── domain (neuromitosis.com)
        └────────────────────────── method = web (HTTPS-hosted DID document)
```

- `did:web` hosts the DID document over HTTPS — no blockchain, no ledger. The domain *is* the
  trust anchor, exactly like the existing `did:web:myaelmendez.github.io`.
- Path segments after the domain are `:`-separated and decode to `/`. So `:cortex` resolves to
  `https://neuromitosis.com/cortex/did.json`.
- Custody stays local: the document is *published* from Victus but the **repo signing key** never
  leaves `C:\ae\secrets\`. Only the public key (in the DID doc) and signed records cross.

### 2. Resolution

```text
GET https://neuromitosis.com/cortex/did.json
  → { "@context": [...], "id": "did:web:neuromitosis.com:cortex", ... }

GET https://myaelmendez.github.io/blueprints/../cortex/did.json   (point-of-truth mirror)
  → identical document (re-pull target for recovery)
```

Any did:web resolver (or raw HTTPS GET) returns the same document. github.io is the canonical
re-pull target if neuromitosis.com is unreachable.

### 3. The cortex as a sovereign repo (ATProto-style)

An ATProto repo is a Merkle Search Tree (MST) of `collection/record` entries, each content-
addressed by CID and signed by the repo's key. The cortex maps onto this 1:1:

| ATProto concept | Cortex equivalent |
|---|---|
| Repo DID | `did:web:neuromitosis.com:cortex` |
| Repo signing key | Victus-custodied key (`C:\ae\secrets\neuromitosis-cortex.pem`) |
| MST records | `ae.core#cortexTrace` entries: `epoch\|key\|value` from `meta_memory.csv`/`cortex.db` |
| Collections | `ae.core` (meta-memory) · `ae.mesh` (peers from `mesh_peers.json`) · `ae.mission` (`#250`) |
| PDS host | droplet `aevps` @ `129.212.180.252:3000` (`#atproto_pds`) |
| Handle | `at://neuromitosis.com` (`alsoKnownAs`) |

The **local trace is the origin** of the MST: `cortex_store.py` appends to `meta_memory.csv`
and ingests into `C:\ae\cortex.db`; a mirror job signs the diff and writes the records to the
droplet PDS. Identity (the DID) and custody (the key) never move — only CIDs and signatures do.

### 4. The DID document

Publish this at `https://neuromitosis.com/cortex/did.json` (and mirror to github.io):

```json
{
  "@context": ["https://www.w3.org/ns/did/v1"],
  "id": "did:web:neuromitosis.com:cortex",
  "alsoKnownAs": [
    "at://neuromitosis.com",
    "ae://neuromitosis.cortex"
  ],
  "verificationMethod": [
    {
      "id": "#cortex-key",
      "type": "Ed25519VerificationKey2020",
      "controller": "did:web:neuromitosis.com:cortex",
      "publicKeyMultibase": "z<PUBLIC_KEY_MULTIBASE_FROM_VICTUS_SECRET>"
    }
  ],
  "assertionMethod": ["#cortex-key"],
  "authentication": ["#cortex-key"],
  "service": [
    {
      "id": "#atproto_pds",
      "type": "AtprotoPds",
      "serviceEndpoint": "http://129.212.180.252:3000"
    },
    {
      "id": "#cortex_trace",
      "type": "CortexStore",
      "serviceEndpoint": "C:\\ae\\cortex.db",
      "description": "Local-first SQLite meta-memory trace (Victus custody). Origin of MST records."
    },
    {
      "id": "#ae_homebase",
      "type": "AeHomebase",
      "serviceEndpoint": "https://neuromitosis.com"
    },
    {
      "id": "#github_io_truth",
      "type": "PointOfTruth",
      "serviceEndpoint": "https://myaelmendez.github.io"
    }
  ],
  "remark": "Sovereign anchor for the neuromitosis agentic cortex. Repo signing key custodied on Victus (C:\\ae\\secrets\\); only public key + signed records cross bounds. PDS host is metal-swappable: repoint #atproto_pds.serviceEndpoint to relocate the repo mirror without changing the DID. Identity stays with the operator, not the host. #hermiphicationisinevitable"
}
```

> Note: the `#cortex_trace` `serviceEndpoint` is a *local* path by design — it documents where the
> trace physically lives (Victus). Resolvers treat it as metadata, not a fetchable URL. The live,
> fetchable repo mirror is `#atproto_pds`.

## Addressing — how to reach the cortex

```text
Identity (DID)      → did:web:neuromitosis.com:cortex
Handle (ATProto)    → at://neuromitosis.com
TOWER route (æ://)  → æ://neuromitosis.cortex   (alsoKnownAs: ae://neuromitosis.cortex)
Repo records        → at://neuromitosis.com/ae.core/cortexTrace/<rkey>
DID document        → https://neuromitosis.com/cortex/did.json
Point-of-truth      → https://myaelmendez.github.io/cortex/did.json
Live PDS mirror     → http://129.212.180.252:3000 (aevps)
```

## Rotation & metal-swappability

- **Repoint mirror, keep DID** — change `#atproto_pds.serviceEndpoint` (droplet IP, port, or a new
  host) without ever touching the DID. Identity is decoupled from hosting, exactly like the
  `did:web:myaelmendez.github.io` remark.
- **Rotate signing key** — generate a new Ed25519 key on Victus, publish the new
  `publicKeyMultibase` under `#cortex-key`, re-sign the MST diff, keep the same DID. Old key can be
  retained as a secondary `verificationMethod` during overlap.
- **Recover** — if neuromitosis.com is down, re-pull the DID document from github.io (truth) and
  re-sync the MST from the local trace (`cortex.db` → re-sign → push to current PDS).

## Blueprint fields

| Field | Value |
|---|---|
| Mission | Give the neuromitosis agentic cortex a stable, resolvable sovereign identity |
| Method | `did:web` (HTTPS-hosted DID document; domain = trust anchor) |
| DID | `did:web:neuromitosis.com:cortex` → `https://neuromitosis.com/cortex/did.json` |
| Custody | Victus `C:\ae\secrets\neuromitosis-cortex.pem` (signing key, private) |
| Surface | github.io (truth) + neuromitosis.com (live) — publish the DID document |
| Mirror | droplet `aevps` @ `129.212.180.252:3000` (`#atproto_pds`, MST repo host) |
| Trace | `C:\ae\cortex.db` + `C:\ae\meta_memory.csv` (MST origin) |
| Repo shape | ATProto MST: collections `ae.core` / `ae.mesh` / `ae.mission`, records CID-signed |
| Handle | `at://neuromitosis.com` · `æ://neuromitosis.cortex` |
| Care | #hermiphicationisinevitable — identity with the operator, not the host |

## Language

```text
did:web:neuromitosis.com:cortex  → the cortex's sovereign identity (this blueprint)
at://neuromitosis.com            → the cortex repo, ATProto-handle style
æ://neuromitosis.cortex          → the TOWER route into the cortex
$cortex                          → execute (mint/sign the repo now)
>_æ|                             → live prompt when +æ is active
```

## Pitfalls

- **DID document path** — `did:web:neuromitosis.com:cortex` resolves to
  `https://neuromitosis.com/cortex/did.json` (no `.well-known`; that prefix is *only* for the bare
  domain). Publishing to `/.well-known/did.json` under a sub-path will 404 on resolution.
- **Signing key must never leave Victus** — only the *public* multibase goes in the DID doc.
  Committing `neuromitosis-cortex.pem` (or any raw secret) to the repo breaks sovereignty; it lives
  in `C:\ae\secrets\` which is gitignored.
- **Truth vs live** — github.io is point-of-truth. If neuromitosis.com and github.io diverge,
  github.io wins on recovery. Don't treat the live domain as canonical.
- **PDS endpoint is a mirror, not identity** — repointing `#atproto_pds` does NOT change the DID.
  Don't mint a new DID just to move the repo host.
- **Local trace path in service doc** — `#cortex_trace.serviceEndpoint` is metadata (where the
  trace physically lives), not a fetchable URL. Resolvers must not try to GET a `C:\` path.
- **AlsoKnownAs must agree** — `at://neuromitosis.com` and `ae://neuromitosis.cortex` must resolve
  back to this same DID or the handle binding is broken.

## Verification

- Resolve the DID: `curl -s https://neuromitosis.com/cortex/did.json | jq .id` →
  `"did:web:neuromitosis.com:cortex"`.
- Re-pull truth: `curl -s https://myaelmendez.github.io/cortex/did.json` → identical document.
- Check services: `#atproto_pds` present (AtprotoPds) and `#cortex_trace` present (CortexStore).
- Check handles: `alsoKnownAs` contains `at://neuromitosis.com` and `ae://neuromitosis.cortex`.
- Check custody: the `#cortex-key` public key verifies a signed MST record from the droplet PDS;
  the private key is absent from the repo (`grep -r "neuromitosis-cortex.pem" .` → no hits outside
  `.gitignore` / `C:\ae\secrets\`).
- Round-trip: append a `meta_memory.csv` line → `cortex_store.py` ingests to `cortex.db` → mirror
  job signs the diff → record appears at `at://neuromitosis.com/ae.core/cortexTrace/<rkey>`.

---

`$^æ`
