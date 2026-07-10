"""
Tests for the Rust/WASM hands of the +æ^glocal host loop.
Verifies the local toolchain (wasm32 target + cargo) can compile a crate to
.wasm, and that run degrades honestly when no wasm runtime is on PATH.
"""
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from environments.rust_wasm_tools import build_wasm, run_wasm, toolset  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "testdata" / "wasm_hello"


def test_wasm32_target_present():
    assert shutil.which("cargo") is not None
    out = __import__("subprocess").run(["rustup", "target", "list", "--installed"],
                                       capture_output=True, text=True, timeout=30)
    assert "wasm32-unknown-unknown" in out.stdout


def test_build_wasm_produces_artifact():
    res = build_wasm(str(FIXTURE), use_pack=False)
    assert res["ok"] is True, res.get("error")
    wasm = Path(res["wasm"])
    assert wasm.exists() and wasm.suffix == ".wasm"
    assert res["bytes"] > 0


def test_run_wasm_degrades_without_runtime():
    built = build_wasm(str(FIXTURE), use_pack=False)
    res = run_wasm(built["wasm"])
    # wasmtime not on PATH on Victus -> honest capability report, not a crash
    assert res.get("reason") == "no_runtime"
    assert res["ok"] is False


def test_toolset_build():
    ts = toolset(str(FIXTURE))
    assert set(ts.keys()) == {"rust_build_wasm", "rust_run_wasm"}
    res = ts["rust_build_wasm"](None)
    assert res["ok"] is True
