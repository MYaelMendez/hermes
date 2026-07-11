#!/usr/bin/env python3
"""Verify contest submission integrity across release manifest and attestation."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SUBMISSION_ROOT = REPO_ROOT / "contest-submission"
RELEASE_MANIFEST_PATH = SUBMISSION_ROOT / "vscode-remote-use" / "release-manifest-vscode-vlc-ffmpeg.json"
ATTESTATION_PATH = SUBMISSION_ROOT / "ATTESTATION.md"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def to_repo_relative(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT.resolve())).replace("\\", "/")


def parse_attestation_table(attestation_text: str) -> dict[str, tuple[int, str]]:
    rows: dict[str, tuple[int, str]] = {}
    pattern = re.compile(r"^\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|\s*([0-9a-f]{64})\s*\|\s*$")
    for line in attestation_text.splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        rel_path = match.group(1).strip().replace("\\", "/")
        size_bytes = int(match.group(2))
        sha256 = match.group(3)
        rows[rel_path] = (size_bytes, sha256)
    return rows


def resolve_attested_file(rel_path: str) -> Path:
    normalized = rel_path.replace("\\", "/")
    if normalized.startswith("contest-submission/"):
        return REPO_ROOT / normalized
    submission_candidate = SUBMISSION_ROOT / normalized
    if submission_candidate.exists():
        return submission_candidate
    return REPO_ROOT / normalized


def attestation_has_path(rows: dict[str, tuple[int, str]], repo_relative_path: str) -> bool:
    normalized = repo_relative_path.replace("\\", "/")
    if normalized in rows:
        return True
    if normalized.startswith("contest-submission/"):
        short = normalized[len("contest-submission/") :]
        if short in rows:
            return True
    return False


def main() -> int:
    errors: list[str] = []

    if not RELEASE_MANIFEST_PATH.exists():
        print(f"Missing release manifest: {RELEASE_MANIFEST_PATH}")
        return 1
    if not ATTESTATION_PATH.exists():
        print(f"Missing attestation: {ATTESTATION_PATH}")
        return 1

    release_manifest = json.loads(RELEASE_MANIFEST_PATH.read_text(encoding="utf-8"))
    attestation_text = ATTESTATION_PATH.read_text(encoding="utf-8")
    attestation_rows = parse_attestation_table(attestation_text)

    artifact = release_manifest.get("artifact", {})
    vsix_rel = str(artifact.get("vsix_path", "")).replace("\\", "/")
    if not vsix_rel:
        errors.append("release manifest missing artifact.vsix_path")
        vsix_path = None
    else:
        if ":/" in vsix_rel:
            # Normalize absolute path inside manifest to local Path
            vsix_path = Path(vsix_rel)
        else:
            vsix_path = REPO_ROOT / vsix_rel

    if vsix_path and not vsix_path.exists():
        errors.append(f"VSIX path from manifest does not exist: {vsix_path}")

    if vsix_path and vsix_path.exists():
        actual_size = vsix_path.stat().st_size
        actual_sha = sha256_file(vsix_path)
        manifest_size = int(artifact.get("size_bytes", -1))
        manifest_sha = str(artifact.get("sha256", ""))
        if manifest_size != actual_size:
            errors.append(
                f"release manifest size mismatch: expected {actual_size}, found {manifest_size}"
            )
        if manifest_sha != actual_sha:
            errors.append(
                f"release manifest sha256 mismatch: expected {actual_sha}, found {manifest_sha}"
            )

    for rel_path, (expected_size, expected_sha) in attestation_rows.items():
        absolute = resolve_attested_file(rel_path)
        if not absolute.exists():
            errors.append(f"attestation references missing file: {rel_path}")
            continue
        actual_size = absolute.stat().st_size
        actual_sha = sha256_file(absolute)
        if actual_size != expected_size:
            errors.append(
                f"attestation size mismatch for {rel_path}: expected {actual_size}, found {expected_size}"
            )
        if actual_sha != expected_sha:
            errors.append(
                f"attestation sha256 mismatch for {rel_path}: expected {actual_sha}, found {expected_sha}"
            )

    release_manifest_rel = to_repo_relative(RELEASE_MANIFEST_PATH)
    if not attestation_has_path(attestation_rows, release_manifest_rel):
        errors.append("attestation does not include release manifest entry")

    if vsix_path and vsix_path.exists():
        vsix_rel_repo = to_repo_relative(vsix_path)
        if not attestation_has_path(attestation_rows, vsix_rel_repo):
            errors.append("attestation does not include VSIX entry")

    if errors:
        print("Submission integrity check failed:")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("Submission integrity check passed.")
    print(f"Release manifest: {RELEASE_MANIFEST_PATH}")
    print(f"Attestation: {ATTESTATION_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
