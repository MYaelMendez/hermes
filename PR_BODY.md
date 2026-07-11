## Summary

Hermes ships **no CUDA/NVIDIA skill**. This adds the first one, formalizing the `>_n:`
operator grammar (`>_n: → nvidia (NemoClaw) → compute`, per AGENTS.md) as a concrete,
agent-addressable GPU compute surface.

Scope:
- **SKILL.md** — the `>_n:` NemoClaw pattern, `nvidia-smi` host bridge for VS Code webviews,
  the VS Code webview `file://` pitfall, WebGPU fallback, the `[N/A]`→`n/a` NaN guard, a
  checkable verification checklist, **and the compiler layer** (nvcc kernels + NVIDIA CUDA
  Tile IR as the backend under the surface).
- **references/host-bridge.md** — the full `remoteUse.nvidia` extension handler plus the
  complete webview↔host message contract.
- **templates/nvidia-tiles.html** — the shipped green-NVIDIA 6-tile surface (GPU / Compute
  Path / Processes / Bench / Routes / Envelope).

## Why this belongs upstream

- `mlops/` has no CUDA skill today (only `evaluation`, `huggingface-hub`, `inference`,
  `models`). Every other major compute path has a skill; CUDA was the gap.
- It is scoped to the Hermes operator grammar (`>_n:`) and the `remoteUse.*` VS Code surface
  system, so it slots in beside `optimizing-attention-flash` and the surface-dev skills.

## Verification

- `npm run compile` (tsc) exits 0
- `pytest secret_source_bridge/tests.py tests/hermes_runtime/test_computer_use.py` → 28/28
- SKILL.md frontmatter validated (name + ≤1024-char description + version/author/license/metadata)
- No secrets hardcoded
- Surface render-verified (headless Edge)

## Related

- CUDA Tile IR (NVIDIA/cuda-tile): https://github.com/NVIDIA/cuda-tile — the MLIR kernel
  compiler infra that sits under this surface (linked in Resources).

## Test plan

- [ ] `skills_list` / skill loader picks up `mlops/cuda` after a fresh session
- [ ] `remoteUse.nvidia` opens the NVIDIA Tiles surface and telemetry populates via `nvidia-smi`
- [ ] `nvcc matmul.cu -o matmul` compiles on a node with the CUDA toolkit (per Workflow 4)
