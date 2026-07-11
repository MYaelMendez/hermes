#!/usr/bin/env python3
"""Install local Hermes cron jobs for computer vitals monitoring."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.cronjob_tools import cronjob


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install Hermes cron jobs for local computer vitals")
    parser.add_argument("--schedule", default="every 15m", help="Schedule for recurring vitals checks")
    parser.add_argument("--deliver", default="local", help="Delivery target (local, origin, telegram:chat_id, etc.)")
    parser.add_argument("--name", default="Local Computer Vitals", help="Cron job name")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    vitals_script = repo_root / "scripts" / "computer_vitals.py"

    prompt = (
        "Run this local command exactly once and use its output to report actionable computer health alerts.\\n"
        f"Command: python {vitals_script} --format json --history\\n"
        "Response policy:\\n"
        "- If any critical alerts exist, summarize top actions immediately.\\n"
        "- If only warn alerts exist, summarize concise mitigation steps.\\n"
        "- If no alerts, respond with [SILENT]."
    )

    result = json.loads(
        cronjob(
            action="create",
            schedule=args.schedule,
            prompt=prompt,
            name=args.name,
            deliver=args.deliver,
        )
    )

    if not result.get("success"):
        print(f"Failed to install vitals cron job: {result.get('error', 'unknown error')}")
        return 1

    print("Installed vitals cron job.")
    print(f"Job ID: {result.get('job_id')}")
    print(f"Schedule: {result.get('schedule')}")
    print(f"Deliver: {result.get('deliver')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
