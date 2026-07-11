# ML Workstation (Phase 1)

This folder is a local-first ML experiment scaffold for Hermes glocal monorepo.

## What It Adds

- deterministic quick evaluation script,
- experiment registry with config/metrics hashing,
- no-cloud baseline path for local iteration.

## Files

- `experiments/registry.json`: append-only run registry.
- `../scripts/ml_quick_eval.py`: computes exact-match accuracy from line-aligned files.
- `../scripts/ml_register_run.py`: registers config + metrics into registry with hashes.

## Example

1. Evaluate predictions.

```bash
python scripts/ml_quick_eval.py \
  --expected data/expected.txt \
  --predicted data/predicted.txt \
  --output ml/experiments/metrics-sample.json
```

2. Register run.

```bash
python scripts/ml_register_run.py \
  --name baseline-local \
  --config ml/experiments/config-sample.json \
  --metrics ml/experiments/metrics-sample.json \
  --notes "phase-1 local baseline"
```

## Rule

Every run must include:

- a config artifact,
- a metrics artifact,
- reproducible hashes recorded in registry.
