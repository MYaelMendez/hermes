# Glocal Monorepo Operating Model

This repository now carries a formal local-first monorepo contract in [glocal-monorepo.json](../glocal-monorepo.json).

## Objective

Run one repository as a deterministic glocal system where:

- runtime defaults to local inference and local media execution,
- VS Code UI and Hermes CLI share a common surface vocabulary,
- submission artifacts are reproducible and hash-attested.

## Primitive

The key primitive is `glocal-git`:

1. Local git repo is execution truth (`C:/æ/hermes-fork`).
2. Global viewport exports are the distribution surface (`æ://private client^glocal/skills/agentic.html`).

This maps one monorepo into two synchronized domains:

- Local truth: deterministic manifests, hashes, local runtime.
- Global surface: HTML/CSS/JS viewports for store, webview, and browser.

## Monorepo Domains

1. core-python: CLI, runtime, gateway, policy.
2. vscode-remote-use: extension UX and remote-use command surface.
3. skills: reusable skill packages and templates.
4. contest-submission: immutable release manifests and attestations.

## Control Plane

The highest-authority files for behavior are:

1. hermes_cli/main.py
2. hermes_cli/media.py
3. vscode-remote-use/package.json
4. vscode-remote-use/src/extension.ts

## Operating Rule

If extension behavior, CLI behavior, and submission metadata diverge, bring them back to contract alignment before shipping.

## Continuous Context Mapping

Run this to emit an up-to-date local context map:

```bash
python scripts/glocal_context_map.py
```

Focused glocal primitive status:

```bash
python scripts/glocal_git_status.py
```

This outputs:

- active surfaces and runtime mode,
- workspace ownership boundaries,
- control-plane file checksums,
- submission artifact inventory,
- canonical verification commands.

## Integrity Gate

Run integrity verification before packaging or submission updates:

```bash
python scripts/verify_submission_integrity.py
```

This validates:

- release-manifest VSIX size/hash matches artifact,
- attestation table entries match on-disk files,
- release-manifest and VSIX are both included in attestation.

CI workflow: `.github/workflows/glocal-integrity.yml`.

## ML Workstation Phase 1

Phase 1 scaffold is available under `ml/`:

- `scripts/ml_quick_eval.py`
- `scripts/ml_register_run.py`
- `ml/experiments/registry.json`

Monorepo npm scripts:

- `npm run glocal:git`
- `npm run glocal:verify`
- `npm run ml:quick-eval`
- `npm run ml:register-run`

## Migration Phases

1. Phase 0 (current): add contract + context map without breaking existing paths.
2. Phase 1: centralize release metadata generation from one source.
3. Phase 2: enforce policy gates in CI for surface/runtime mismatch.
4. Phase 3: expose context map in VS Code command panel.
