# Hermes 🤖 Blueprint

## Premise

The robot is not a peripheral. It is the physical effector of Hermes intent, governed by DAO logic, and identified by DAO LLC. The emoji identity is intentional: white-label, cross-cultural, zero upstream branding lock-in.

## Canonical Command Flow

```
Human intent → Private Client AI → Hermes → DAO logic → 🤖 executor → DAO LLC attribution
```

## Identity vs Logic Separation

- `DAO` = logic surface: proposals, votes, execution contracts, simulator contracts
- `DAO LLC` = Wyoming identity surface: formation, membership, attribution, treasury

Robot actions are attributed to DAO LLC; governance is decided in DAO. Never conflate.

## Runtime Stack

| Layer | Role |
|---|---|
| Hermes Agent | Intent router + local control plane |
| DAO | Execution contract + governance |
| 🤖 Mini | Default hardware actuator |
| 🤖 2 | Full humanoid operator |
| mech-lang.org | Rust robot vision + actuator runtime |
| MuJoCo / Isaac Sim | Simulator-first rehearsal |
| HuggingFace Space | Global marketplace surface (`Hermes 🤖`) |
| VS Code | `remoteUse.reachyProbe`, `remoteUse.reachyPanel` |
| Stripe / Doola | Payments + DAO LLC formation rails |

## Surface Model

| Surface | Role |
|---|---|
| CLI | `hermes 🤖`, `hermes dao status`, `hermes glocal` |
| VS Code | `remoteUse.reachyProbe`, `remoteUse.reachyPanel` |
| Web | `agentic.html`, landing page, marketplace viewport |
| HF Space | `hermes-reachy` domain application |
| Simulator | Isaac Sim / Omniverse headless rehearsal |
| Physical | 🤖 Mini / 🤖 2 actuators |

## Operator Surfaces

### Local — `apps/reachy/app.py`

```text
POST /reachy/probe   -> minimal state read
POST /reachy/panel   -> operator control surface
POST /reachy/status  -> live state snapshot
GET  /health         -> service heartbeat
```

### Simulator bridge (target)

```text
POST /sim/contract   -> DAO-approved intent contract ingest
POST /sim/run        -> execute headless rehearsal
GET  /sim/status     -> telemetry + attestation hash
```

### CLI

```text
hermes 🤖            -> status + probe
hermes 🤖 panel       -> operator surface
hermes 🤖 sim run     -> DAO contract -> simulator -> attestation
hermes dao status     -> DAO logic state
hermes glocal         -> monorepo integrity + context map
```

## Governance Rules

- All simulator runs require DAO approval.
- No robot control prompt bypasses DAO.
- No secret/cardholder data passes through 🤖 executor.
- Browser-controlled payments only; no secrets through actuator surfaces.
- Attribution hash recorded after every physical or simulated execution.

## Verification

- UI/viewport changes: localhost render/build only.
- Backend/CLI changes: pytest.
- Simulator outputs: DAO-attested manifest + SHA-256 integrity gate.

## White-Label Constraint

HuggingFace Space and all artifacts must be white-label. Use `🤖` symbol identity, not upstream brand names. No mandatory telemetry, no hosted identity fences, no branding lock-in.

## Next Steps

1. Implement `apps/reachy/sim_bridge.py` — simulator kernel
2. Wire `hermes 🤖` into `hermes_cli/main.py`
3. Attach `remoteUse.reachyProbe`/`remoteUse.reachyPanel` in VS Code
4. Connect simulator attestation to `monorepo-manifest.json` under `simulation/`
