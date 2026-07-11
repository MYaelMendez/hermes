# Local Computer Vitals via Hermes Cron

This setup keeps tabs on local machine health and turns vitals into actionable alerts.

## Scripts

- `scripts/computer_vitals.py`: collect CPU, memory, disk, and GPU (if available) vitals.
- `scripts/install_vitals_cron.py`: install a recurring Hermes cron job that runs the vitals script.

## Manual Snapshot

```bash
python scripts/computer_vitals.py --format markdown --history
```

Useful options:

- `--path C:\\` choose monitored disk path
- `--fail-on-critical` exit code 2 when critical alerts exist
- `--output <path>` custom output location

Default output location:

- `~/.hermes/monitor/latest-vitals.json` (or markdown if format is markdown)
- optional history: `~/.hermes/monitor/vitals-history.jsonl`

## Install Recurring Cron Monitor

```bash
python scripts/install_vitals_cron.py --schedule "every 15m" --deliver local
```

This creates a cron job that:

1. Runs the local vitals script.
2. Emits actionable mitigation steps when warnings/critical alerts exist.
3. Returns `[SILENT]` when no noteworthy alerts exist.

## NPM Shortcuts

```bash
npm run vitals:check
npm run vitals:cron-install
```

## Inspect Jobs

```bash
hermes cron list
hermes cron status
```
