"""Media command surface for manifest-based execution and audit."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from hermes_cli.config import get_hermes_home


SURFACE_ID = "æ://HERMES-AGENT^media"
PRIVATE_CLIENT_GLOCAL_SURFACE = "æ://private client^glocal"
ALLOWED_SURFACES = {SURFACE_ID, PRIVATE_CLIENT_GLOCAL_SURFACE}


def _resolve_surface(value: str | None) -> str:
    candidate = str(value or "").strip()
    if not candidate:
        return SURFACE_ID
    if candidate in ALLOWED_SURFACES:
        return candidate
    raise ValueError(f"Unsupported surface: {candidate}")


def _is_allowed_surface(value: str) -> bool:
    if value in ALLOWED_SURFACES:
        return True
    return any(value == f"{base}/coevolve" for base in ALLOWED_SURFACES)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _default_manifest_path(engine: str) -> Path:
    root = get_hermes_home() / "media" / "manifests"
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    return root / f"{engine}-manifest-{stamp}.json"


def _build_command(manifest: dict[str, Any]) -> list[str]:
    engine = manifest["engine"]
    input_path = manifest["input_path"]
    output_path = manifest.get("output_path")

    if engine == "ffmpeg":
        if not output_path:
            raise ValueError("ffmpeg requires output_path")
        return ["ffmpeg", "-y", "-i", input_path, output_path]

    if engine == "vlc":
        return ["vlc", "--intf", "dummy", "--play-and-exit", input_path]

    raise ValueError(f"Unsupported media engine: {engine}")


def _read_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _iter_manifests(limit: int = 10) -> list[Path]:
    root = get_hermes_home() / "media" / "manifests"
    if not root.exists():
        return []
    manifests = sorted(root.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return manifests[: max(1, limit)]


def _plan(args) -> int:
    input_path = Path(args.input_path).expanduser().resolve()
    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        return 1

    output_path = None
    if args.output_path:
        output_path = str(Path(args.output_path).expanduser().resolve())

    surface = _resolve_surface(getattr(args, "surface", None))

    manifest = {
        "schema_version": 1,
        "surface": surface,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "engine": args.engine,
        "action": args.action,
        "member_token": args.member_token,
        "governance": args.governance,
        "input_path": str(input_path),
        "input_sha256": _sha256_file(input_path),
        "output_path": output_path,
    }
    if surface == PRIVATE_CLIENT_GLOCAL_SURFACE:
        manifest["local_only"] = True
        manifest["runtime"] = "ae://local^ollama"
        manifest["cloud"] = False

    manifest["command"] = _build_command(manifest)
    manifest["manifest_sha256"] = hashlib.sha256(
        _canonical_json({k: v for k, v in manifest.items() if k != "manifest_sha256"}).encode("utf-8")
    ).hexdigest()

    manifest_path = Path(args.manifest).expanduser().resolve() if args.manifest else _default_manifest_path(args.engine)
    _write_manifest(manifest_path, manifest)

    print("Media plan created.")
    print(f"Surface: {manifest['surface']}")
    print(f"Manifest: {manifest_path}")
    print(f"Command: {' '.join(manifest['command'])}")
    return 0


def _run(args) -> int:
    manifest_path = Path(args.manifest).expanduser().resolve()
    if not manifest_path.exists():
        print(f"Manifest not found: {manifest_path}")
        return 1

    manifest = _read_manifest(manifest_path)
    command = manifest.get("command") or _build_command(manifest)

    print(f"Surface: {manifest.get('surface', SURFACE_ID)}")
    print(f"Engine: {manifest.get('engine')}")
    print(f"Running: {' '.join(command)}")

    if args.dry_run:
        print("Dry run complete.")
        return 0

    result = subprocess.run(command)
    if result.returncode != 0:
        print(f"Media run failed (exit={result.returncode}).")
        return result.returncode

    print("Media run completed.")
    return 0


def _audit(args) -> int:
    manifest_path = Path(args.manifest).expanduser().resolve()
    if not manifest_path.exists():
        print(f"Manifest not found: {manifest_path}")
        return 1

    manifest = _read_manifest(manifest_path)
    issues: list[str] = []

    surface = str(manifest.get("surface", ""))
    if not _is_allowed_surface(surface):
        issues.append(
            "surface must be one of: "
            + ", ".join(sorted(ALLOWED_SURFACES))
            + " (or /coevolve variant)"
        )

    member_token = str(manifest.get("member_token", ""))
    if not member_token.startswith("+æ"):
        issues.append("member_token must start with +æ")

    input_path = Path(str(manifest.get("input_path", "")))
    if not input_path.exists():
        issues.append("input_path does not exist")
    else:
        expected_hash = manifest.get("input_sha256", "")
        actual_hash = _sha256_file(input_path)
        if expected_hash != actual_hash:
            issues.append("input_sha256 mismatch")

    expected_manifest_hash = manifest.get("manifest_sha256", "")
    actual_manifest_hash = hashlib.sha256(
        _canonical_json({k: v for k, v in manifest.items() if k != "manifest_sha256"}).encode("utf-8")
    ).hexdigest()
    if expected_manifest_hash != actual_manifest_hash:
        issues.append("manifest_sha256 mismatch")

    if issues:
        print("Media audit failed:")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    print("Media audit passed.")
    print(f"Manifest: {manifest_path}")
    return 0


def _viewport(args) -> int:
    manifests = _iter_manifests(getattr(args, "limit", 10))

    print("Media Desktop Agentic Entrepreneurship Viewport")
    print(f"Surface: {SURFACE_ID} | {PRIVATE_CLIENT_GLOCAL_SURFACE}")
    print(f"Manifest count (shown): {len(manifests)}")

    engine_counts: dict[str, int] = {"ffmpeg": 0, "vlc": 0}
    governance_counts: dict[str, int] = {}

    for path in manifests:
        try:
            payload = _read_manifest(path)
        except Exception:
            continue
        engine = str(payload.get("engine", "unknown"))
        engine_counts[engine] = engine_counts.get(engine, 0) + 1
        gov = str(payload.get("governance", "none"))
        governance_counts[gov] = governance_counts.get(gov, 0) + 1

    print("Engine distribution:")
    for engine, count in sorted(engine_counts.items()):
        print(f"  - {engine}: {count}")

    print("Governance distribution:")
    for gov, count in sorted(governance_counts.items()):
        print(f"  - {gov}: {count}")

    learn_sequence = get_hermes_home() / "learn" / "learn-sequence.json"
    if learn_sequence.exists():
        try:
            learn_payload = json.loads(learn_sequence.read_text(encoding="utf-8"))
            breakouts = learn_payload.get("breakouts", {})
            print(f"Learn sequence linked: yes ({len(breakouts)} breakout entries)")
        except Exception:
            print("Learn sequence linked: yes (unreadable)")
    else:
        print("Learn sequence linked: no")

    if manifests:
        print("Recent manifests:")
        for path in manifests[:5]:
            print(f"  - {path}")

    return 0


def media_command(args) -> None:
    action = getattr(args, "media_action", None)
    if action == "plan":
        raise SystemExit(_plan(args))
    if action == "run":
        raise SystemExit(_run(args))
    if action == "audit":
        raise SystemExit(_audit(args))
    if action == "coevolve":
        raise SystemExit(_coevolve(args))
    if action == "viewport":
        raise SystemExit(_viewport(args))

    print("Usage: hermes media <plan|run|audit|coevolve|viewport> ...")
    raise SystemExit(1)


def _ollama_generate_plan(goal: str, input_path: str, output_path: str, codec: str, fps: int | None, bitrate: str | None, model: str | None) -> dict[str, Any]:
    if model is None:
        model = _default_ollama_model()

    prompt = (
        "Return only JSON. No narration.\n"
        f"GOAL: {goal}\n"
        f"INPUT: {input_path}\n"
        f"OUTPUT: {output_path}\n"
        "Build a deterministic ffmpeg plan with codec/fps/bitrate/filter fields and checksum/retry rules.\n"
        "JSON shape: {codec, fps, bitrate, filters, expected_output_sha256, pass_criteria, retry_policy, notes}\n"
    )

    runtime = _resolve_local_ollama_runtime({"provider": "ollama", "default": model or "qwen2.5-coder:3b"})
    base_url = runtime["base_url"].rstrip("/") + "/v1"
    headers = {
        "Authorization": f"Bearer {runtime['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model or runtime.get("detected_model") or "qwen2.5-coder:3b",
        "messages": [
            {"role": "system", "content": "You are a deterministic media plan generator."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }

    try:
        import requests
    except Exception as exc:  # pragma: no cover - network/runtime failure path
        raise RuntimeError("requests is required for local Ollama plan generation") from exc

    response = requests.post(base_url + "/chat/completions", headers=headers, json=payload, timeout=120)
    response.raise_for_status()
    body = response.json()
    content = body["choices"][0]["message"]["content"]
    plan = json.loads(content)
    if not isinstance(plan, dict):
        raise RuntimeError("Ollama plan did not return a JSON object")
    return plan


def _resolve_local_ollama_runtime(provider_cfg: dict[str, Any]) -> dict[str, Any]:
    from hermes_cli.runtime_provider import resolve_runtime_provider

    provider = provider_cfg.get("provider", "ollama")
    model = str(provider_cfg.get("default", "") or "").strip() or None
    runtime = resolve_runtime_provider(requested=provider)
    if not runtime:
        raise RuntimeError("Local Ollama runtime is not available")
    base_url = str(runtime.get("base_url", "http://127.0.0.1:11434")).rstrip("/")
    api_key = str(runtime.get("api_key", "ollama"))
    return {
        "base_url": base_url,
        "api_key": api_key,
        "provider": str(runtime.get("provider", "ae://local^ollama")),
        "detected_model": model or runtime.get("detected_model") or "qwen2.5-coder:3b",
    }


def _default_ollama_model() -> str:
    return "qwen2.5-coder:3b"


def _coevolve_apply_plan(plan: dict[str, Any], input_path: str, output_path: str) -> tuple[list[str], dict[str, Any]]:
    codec = str(plan.get("codec", "h264_nvenc")).strip() or "h264_nvenc"
    fps = plan.get("fps")
    bitrate = str(plan.get("bitrate", "") or "").strip()
    filters = str(plan.get("filters") or "")
    filter_parts = [f"fps={int(fps)}"] if fps else []
    if filters.strip():
        filter_parts.append(filters.strip())
    vf = ",".join(filter_parts) if filter_parts else "yadif"

    command: list[str] = [
        "ffmpeg",
        "-y",
        "-hwaccel",
        "cuda",
        "-i",
        input_path,
        "-c:v",
        codec,
        "-vf",
        vf,
        output_path,
    ]
    if bitrate:
        command = [
            "ffmpeg",
            "-y",
            "-hwaccel",
            "cuda",
            "-i",
            input_path,
            "-c:v",
            codec,
            "-vf",
            vf,
            "-b:v",
            bitrate,
            output_path,
        ]

    metadata = {
        "plan_codec": codec,
        "plan_fps": fps,
        "plan_bitrate": bitrate or None,
        "plan_filters": filters or None,
    }
    return command, metadata


def _coevolve_verify(plan: dict[str, Any], manifest_path: Path, output_path: Path) -> tuple[bool, list[str]]:
    issues: list[str] = []
    expected_sha = str(plan.get("expected_output_sha256", "")).strip()
    if expected_sha:
        actual_sha = _sha256_file(output_path) if output_path.exists() else ""
        if actual_sha != expected_sha:
            issues.append(f"output_sha256 mismatch expected={expected_sha} actual={actual_sha}")
    if output_path.exists() and output_path.stat().st_size < 1024:
        issues.append("output is suspiciously small")
    return len(issues) == 0, issues


def _coevolve(args) -> int:
    surface = _resolve_surface(getattr(args, "surface", None))
    input_path = Path(args.input_path).expanduser().resolve()
    output_path = Path(args.output_path).expanduser().resolve()
    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        return 1

    manifest_path = Path(args.manifest).expanduser().resolve() if getattr(args, "manifest", None) else _default_manifest_path("ffmpeg-coevolve")
    iteration = 0
    max_retries = int(getattr(args, "retries", 3) or 0) + 1
    max_retries = min(max_retries, 4)
    last_failure: str | None = None
    plan: dict[str, Any] | None = None

    while iteration < max_retries:
        iteration += 1
        if plan is None or last_failure is not None:
            plan = _ollama_generate_plan(
                goal=str(getattr(args, "goal", "")),
                input_path=str(input_path),
                output_path=str(output_path),
                codec=str(getattr(args, "codec", "h264_nvenc")),
                fps=getattr(args, "fps", None),
                bitrate=getattr(args, "bitrate", None),
                model=getattr(args, "model", None),
            )

        command, metadata = _coevolve_apply_plan(plan, str(input_path), str(output_path))
        print(f"Coevolve run {iteration:02d}: {' '.join(command)}")

        run_manifest = {
            "schema_version": 1,
            "surface": f"{surface}/coevolve",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "engine": "ffmpeg",
            "action": f"coevolve:{getattr(args, 'goal', 'media-optimization')}",
            "member_token": getattr(args, "member_token", "+æ"),
            "governance": getattr(args, "governance", "none"),
            "input_path": str(input_path),
            "output_path": str(output_path),
            "iterations": iteration,
            "max_iterations": max_retries,
            "plan": plan,
            "command": list(command),
            **metadata,
        }
        run_manifest["input_sha256"] = _sha256_file(input_path)
        run_manifest["command"] = list(command)
        run_manifest["manifest_sha256"] = hashlib.sha256(
            _canonical_json({k: v for k, v in run_manifest.items() if k != "manifest_sha256"}).encode("utf-8")
        ).hexdigest()
        _write_manifest(manifest_path, run_manifest)

        try:
            result = subprocess.run(command, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except FileNotFoundError as exc:
            print(f"Media engine not found: {exc}")
            last_failure = f"media engine not found: {exc}"
            plan = None
            continue

        if result.returncode != 0:
            log = (result.stdout or b"").decode("utf-8", "replace")[-2048:]
            last_failure = f"ffmpeg exit={result.returncode}\n{log}"
            plan = None
            continue

        passed, issues = _coevolve_verify(plan, manifest_path, output_path)
        if passed:
            print("Media coevolve passed.")
            print(f"Manifest: {manifest_path}")
            print(f"Iterations: {iteration}")
            print(f"Output: {output_path}")
            return 0

        last_failure = "; ".join(issues)
        plan = None

    print("Media coevolve failed after bounded retries.")
    print(last_failure or "unknown failure")
    print(f"Manifest: {manifest_path}")
    return 2
