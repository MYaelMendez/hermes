#!/usr/bin/env python3
"""Deterministic quick evaluator for line-aligned prediction files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Quick exact-match evaluation")
    parser.add_argument("--expected", required=True, help="Expected labels file (1 label per line)")
    parser.add_argument("--predicted", required=True, help="Predicted labels file (1 label per line)")
    parser.add_argument("--output", required=True, help="Output metrics JSON path")
    return parser.parse_args()


def read_lines(path: Path) -> list[str]:
    return [line.rstrip("\n") for line in path.read_text(encoding="utf-8").splitlines()]


def main() -> int:
    args = parse_args()
    expected_path = Path(args.expected).expanduser().resolve()
    predicted_path = Path(args.predicted).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not expected_path.exists():
        print(f"Missing expected file: {expected_path}")
        return 1
    if not predicted_path.exists():
        print(f"Missing predicted file: {predicted_path}")
        return 1

    expected = read_lines(expected_path)
    predicted = read_lines(predicted_path)
    if len(expected) != len(predicted):
        print("Expected and predicted line counts differ.")
        print(f"expected={len(expected)} predicted={len(predicted)}")
        return 1

    total = len(expected)
    correct = sum(1 for e, p in zip(expected, predicted) if e == p)
    accuracy = (correct / total) if total else 0.0

    payload = {
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print("Quick eval completed.")
    print(json.dumps(payload, indent=2))
    print(f"metrics_path={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
