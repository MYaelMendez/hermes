# #250 Corpus — the three-act build of >_æ://

`>_æ://` evolved from a contest submission into a sovereign distributed-cognition
substrate. Three acts, one discipline: **chassis-as-language, sovereign-scoped,
human-steered.**

## Act 1 — Submit (noun) · session 20260702_002050_04055c
The contest origin. Artifacts that entered the corpus:
- `blueprints/breakout-002-accelerator.md` — the accelerator breakout
- `blueprints/breakout-002-vscode-codemode.md` — Code Mode discipline, early
- `blueprints/omniverse-250-runner-manifest.md` — omniverse runner
- `æ://private client^glocal` — first-class media surface (tests: 6 passed)
- `vscode-remote-use/` — the extension (0.1.0.vsix), IDE-for-the-surface seed
- landing-page glocal rebrand (gold-on-void, "Glocal by design")

## Act 2 — Compute (silicon) · session 20260710_193818_b3c467
The chassis met the RTX. Artifacts:
- `gpu-mcp/` — sovereign local CUDA MCP server (tests: 5 passed, no debug line)
- gpu-agent brain upgrade measured **7B @ 116.7 tok/s** (note: code on disk
  currently references `qwen2.5-coder:3b` — the 7B repoint needs re-applying;
  see OPEN ITEMS)
- planner `TOOL:` loop bug fixed (system-via-API-field, not concatenated prompt)
- `vscode-remote-use` scoped as **IDE-for-the-RTX** (CUDA panel, `+æ://cuda-vlc`
  wired, in-editor `.cu` compile/run) — Tier 1+2 spec, not yet coded this turn

## Act 3 — Cognize (substrate) · session 20260712 (this)
The operational substrate of distributed cognition. Artifacts:
- `+bæsic:// compose` — Code Mode surface: agents write bæsic, only results cross
- `meta_memory.bæsic` — in-language distributed-cognition trace (`C:\ae\meta_memory.csv`)
- `Hæbbian://` == `neuromitosis://` — wiring map IS the cognitive evolution log
- `neuromitosis.com.html` + `serve_neuromitosis.py` — co-webmastering site
  (arrival console, vault node `+æ://secrets`, meta_memory panel)
- `gen_neuromitosis.py` — static snapshot baker (deploys to github.io as truth)
- `index_corpus.py` + `sync_to_droplet.py` — local index + droplet PDS sync
- self-evolving `agentic-chassis-surface` skill loop (meta_memory → skill)

## The discipline (constant across all three acts)
- **Chassis is a language** — bæsic/mech carry counts, graphs, memory. Never blind shell loops.
- **Sovereign-scoped** — github.io = surface truth; Victus = custody (secrets, silicon).
- **Human-steered** — agent proposes, you steer. No silent drift. No secrets cross bounds.
- **Truth over marketing** — every claim backed by a real run.

## OPEN ITEMS
- [ ] Re-apply gpu-agent 7B brain repoint (`gpu_mcp/gpu_agent.py` line 67 + docstring line 4) — measured 116.7 tok/s, not persisted.
- [ ] Code the `vscode-remote-use` CUDA panel (Tier 1) per `b3c467` spec.
- [ ] Deploy `neuromitosis.static.html` to github.io as the substrate truth node.
- [ ] Fold all three acts into one #250 PR branch off `upstream/main`.

#hermiphicationisinevitable
