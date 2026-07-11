# #opensourceware · #osw — THE WORKED EXAMPLE

> **This monorepo is not built *for* #250. It *is* #250 —**
> the reference example of #opensourceware (#osw): one person, one sovereign
> stack, proving that agency — not just knowledge — can be open-sourced.

```
OCW → OSW
Open CourseWare democratized knowledge.
Open SourceWare democratizes agency.
```

## The mission

- **#opensourceware #250** — help start **250 American businesses**.
- **The challenge** — sponsors help start **250,000**.
- **The care** — equip new owners with a working sovereign stack, not a slide deck.

## Why this corpus is the example

One operator (一人公司 / one-person company) runs the entire loop locally:
intent → language → runtime → agent → business. No cloud dependency, no
remote secrets, no gatekeeper. If it runs here, on one laptop, it runs for
the next 250 — and the 250,000 after them. That is the proof.

## The stack (the body, by limb)

Every group below is one limb of a single body — the sovereign stack that lets
one person spin up a business.

| # | Limb | Role | Anchor artifacts |
|---|------|------|------------------|
| ① | **æ:// chassis** | agentic-language runtime | `hermes_cli/conductor.py` (aectx router), `qc64_basic.py` (+bæsic://), `mech/` |
| ② | **vscode surface** | the operator's hands | `vscode-remote-use/` (extension, webLLM → æ:// chassis) |
| ③ | **hermes runtime** | the brain | `hermes_runtime/`, `hermes_cli/` (dao, media, viewport, gateway) |
| ④ | **reachy clerk** | the physical agent (Stripe) | `apps/reachy/` |
| ⑤ | **blueprints** | org / protocol grammar | `blueprints/*.md` (DAO, +æ protocols, mech-lang, reachy) |
| ⑥ | **HTML surfaces** | the viewports | `templates/*.html`, `landingpage/` |
| ⑦ | **scripts / tools** | the workshop | `scripts/`, `tools/vlc/`, `crates/`, `pkg/` |
| ⑧ | **infra / manifests** | the monorepo spine | `monorepo-manifest.json`, `glocal-monorepo.json`, `.github/` |

## The naming ladder (canonical)

```
#opensourceware #250          →  the mission
æ://                          →  agentic-language-chassis (aectx router)
  æ://basic  (+bæsic://)      →  qc64 BASIC chassis (verified runtime)
  æ://mech                    →  mech-lang reactive dataflow (spec grammar)
  æ://glocal-agent            →  sovereign local agent → GPU-MCP
  +æ://cc                     →  command & control surface
vscode://                     →  viewport HOST (v = viewport, the mandate)
pc://mesh/victus/local        →  canonical sovereign mesh
```

## Boundaries (truth over marketing)

- **Verified:** æ:// chassis routes 30 live schemes (23 pytest passed); qc64
  BASIC runs; vscode extension compiles (tsc clean).
- **Spec-only:** mech-lang — `mechc` v0.3.5 fails silently on its own tests;
  Mech is grammar we model against, not a runtime we lean on yet (revisit v0.4).
- **Local-only:** RTX 3050 6GB, ollama brain, no cloud, no remote secrets.

## Lineage

Every commit in this corpus carries the trailer:

```
#opensourceware #250
```

Because when you tell the truth, you don't have to remember anything.

**æ.store — the namespace that connects all of it.**

#hermiphicationisinevitable
