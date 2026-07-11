# Hermes Glocal DAO Charter

## Mission

Coordinate local-truth execution and global-surface distribution for Hermes glocal operations.

## Scope

- govern deterministic runtime standards,
- manage release/attestation treasury policy,
- define DAO membership and proposal flow.

## Principles

1. Local-first execution truth.
2. Deterministic manifests and hash-attested artifacts.
3. Bounded retries with fail-closed behavior.
4. Transparent membership and proposal records.

## Decision Process

- Proposals live under `dao/governance/proposals.json`.
- A proposal moves through: `draft -> review -> accepted|rejected`.
- Accepted proposals become enforceable via repo code/config updates.

## Treasury Policy

Treasury records live under `dao/treasury/ledger.json` and must reference hash-verifiable artifacts when applicable.
