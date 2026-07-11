# #opensourceware

#250USA
#æ^softwarefactory

## Reachy Software Factory — VS Code → æ:// → robot:// → HuggingFace

**Thesis:** VS Code is the factory floor. The Hermes Agent extension is the
operator's hands. `æ://` is the language every robot app is written in.
`robot://` is the product template; `reachy://` is the flagship. HuggingFace
is the distribution rail — and because Reachy is Pollen Robotics / HuggingFace
hardware, a marketplace of Reachy apps **on HF is native traffic, not borrowed.**
That is the elite traffic creator.

## I. The Assembly Line

```
Human intent
  → VS Code (factory floor)
    → Hermes Agent extension (operator's hands)
      → æ:// agentic-language-chassis (the language)
        → robot:// (product template; reachy:// = flagship instance)
          → agentic.html + robot manifest (the buildable unit)
            → @vscode/vsce / package step (the press)
              → HuggingFace Space/repo (distribution)
                → Reachy marketplace (traffic → DAOLLC + Stripe)
```

Every stage is already a real primitive in this monorepo — the factory wires
them into one conveyor.

## II. The Buildable Unit — a "Reachy app"

A Reachy app is the atomic product this factory presses. It is:

| Part | File | Role |
|---|---|---|
| Viewport | `agentic.html` | gold-on-void boot-sequence UI, the app's face |
| Manifest | `robot.json` | declares `robot://reachy` binding, capabilities, DAOLLC attribution |
| Wiring | `æ://` scheme calls | how the app talks to the flagship (`reachy://<action>`) |
| Card | `README.md` | HF Space card: title, tags, screenshot, CTA to DAOLLC formation |

The manifest is the contract: `robot://reachy` resolves through the verified
conductor (`_robot_surface`, flagship=True) onto the sovereign mesh
`pc://mesh/victus/local`. One code path, every robot rides it.

## III. Factory Stages (each a future artifact)

1. **Scaffolder** — a VS Code command (`remoteUse.newReachyApp`) that emits the
   buildable-unit skeleton: `agentic.html` + `robot.json` + `reachy://` wiring
   + HF card. The `robot://` app generator.
2. **Press** — package step: validate the manifest against the conductor
   (`reachy://` must resolve, flagship=True), lint the HTML viewport, bundle.
3. **Distribution rail** — publish to a HuggingFace Space/repo via `hf` CLI;
   the Space *is* the storefront tile.
4. **Marketplace surface** — the `hermes-reachy-marketplace.html` storefront
   (already in `templates/`) lists published Reachy apps; gold-on-void, the
   traffic magnet. Each tile links to a live HF Space + a DAOLLC formation CTA.

## IV. Why HuggingFace Is the Right Rail

- Reachy Mini is **Pollen Robotics / HuggingFace** hardware — the audience is
  already there. Publishing Reachy apps to HF Spaces puts the storefront where
  the robot's buyers live.
- HF Spaces render HTML/Gradio natively → an `agentic.html` Reachy app runs as
  a Space with zero server of our own.
- HF is a discovery engine (search, trending, likes) → findable by name, the
  distribution instinct: name the apps so they surface (`Reachy · <verb>`).
- Every Space back-links to DAOLLC formation (Doola) → traffic converts to
  Wyoming DAO LLC formations, the #250 goal.

## V. Relationship to the Governance Protocol

This factory is the **authoring/distribution** half; the
`reachy-daollc-operator-protocol` is the **governance/execution** half. A Reachy
app built here runs under that protocol: Private Client AI → Hermes → DAO logic
→ Reachy executor → DAO LLC attribution. No actuator command bypasses
governance. The factory presses the app; the protocol governs its runtime.

## VI. Scheme Grammar (verified)

```
robot://              abstract embodiment scheme       (robot://<model> <node>)
robot://reachy  ─┐
reachy://        ─┴─  flagship surface (Reachy Mini)   flagship=True
pc://mesh/victus/local   the sovereign mesh every robot rides
æ://                 the agentic-language-chassis (the language above them all)
```

All verified in `hermes_cli/conductor.py` (26 pytest passed). `æ://` is the
scalar/top — the superagent — so there is no tier above it; the factory speaks
æ all the way down.

## VII. Why This Wins

- **Native traffic:** Reachy apps on HF reach Reachy owners directly.
- **One language:** every app is æ:// — no per-app protocol reinvention.
- **Local-first:** authored + tested on Victus RTX, no cloud dependency.
- **Convert-by-design:** every storefront tile → DAOLLC formation → #250.
- **Open-sourceware:** the factory itself is the worked example; anyone can
  fork it and press their own robot marketplace.

## VIII. Proof of Concept (path)

1. Scaffolder emits one Reachy app skeleton (`Reachy · wave`).
2. Manifest validates: `reachy://wave` resolves flagship on the mesh.
3. Publish to a HuggingFace Space; render the agentic.html viewport.
4. List it on `hermes-reachy-marketplace.html`.
5. Capture first click-through to DAOLLC formation → referral loop.

**æ.store — the namespace that connects all of it.**

#hermiphicationisinevitable
