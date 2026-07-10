# Victus Capability Map

Canonical hardware/toolchain reference for the Victus machine. Facts below are verified live-probe data — trust them over assumptions.

- **Machine:** Victus by HP Gaming Laptop 15-fa2xxx
- **Mesh address:** `pc://mesh/victus/local`
- **OS:** Windows 11 Home, build 26200

## Chassis

| Attribute | Value |
|-----------|-------|
| Model | Victus by HP Gaming Laptop 15-fa2xxx |
| OS | Windows 11 Home (build 26200) |
| Mesh address | `pc://mesh/victus/local` |

## Compute

| Component | Spec |
|-----------|------|
| CPU | Intel Core i5-13420H |
| Cores / threads | 8 cores / 12 threads |
| Base clock | 2.1 GHz |
| RAM | 32 GB total (~17 GB free at probe) |
| GPU | NVIDIA RTX 3050 6GB Laptop |
| VRAM | 6144 MiB |
| GPU driver | 592.27 |
| CUDA toolkit | nvcc release 13.3, V13.3.73 (installed) |

## Storage

| Volume | Total | Free |
|--------|-------|------|
| C: | 476 GB | 131 GB |

## Toolchain — Present

| Tool | Version |
|------|---------|
| python | 3.11.15 & 3.13.14 |
| node | 22.17 |
| npm | 10.9.2 |
| uv | 0.11.26 |
| cargo / rustc | 1.96.1 |
| git | 2.50 |
| gh | 2.95 |
| ffmpeg | 8.1.2 |
| code (VS Code) | 1.128 |
| nvcc (CUDA) | 13.3 |
| wasm-pack | 0.15.0 |
| cl.exe / link.exe | MSVC BuildTools 2022 — installed, NOT on PATH |

## Toolchain — Missing

| Tool | Impact |
|------|--------|
| docker | No containers |

> MSVC `cl.exe`/`link.exe` ARE installed via VS 2022 BuildTools (14.44.35207) at
> `C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/`.
> They just aren't on PATH. To use them: add that dir to PATH (plus `LIB`/`INCLUDE`) or run
> `"C:/Program Files/Microsoft Visual Studio/2022/BuildTools/VC/Auxiliary/Build/vcvars64.bat"`.
> `wasm-pack` was installed via `cargo install wasm-pack` (0.15.0) — WASM packaging is UNBLOCKED.

## Rust Targets

- `wasm32-unknown-unknown` (installed)
- `x86_64-pc-windows-msvc` (installed)

## Capability Envelope

### Can do
- GPU inference (CUDA + WebGPU)
- 12-thread parallel builds
- Rust → WASM compile + `wasm-pack` packaging
- Native Windows `.exe` / Tauri linking (with `vcvars64` / PATH set)
- FFmpeg media pipeline
- Full git / gh / VS Code agentic loop
- WebLLM

### Blocked
- Containers (docker)

## Notes
- Native compile was previously believed blocked by missing MSVC — that was WRONG. BuildTools 2022 is installed; only PATH is missing. Verified 2026-07-09.
- CUDA toolkit (nvcc 13.3) is installed and functional.
