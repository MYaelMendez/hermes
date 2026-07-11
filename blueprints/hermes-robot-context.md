# Hermes Robot Context

## Premise

Robots run on local truth and project a global surface. Hermes is the conductor; Reachy is the default physical actuator; DAO is the logic; DAO LLC is the identity.

## Canonical Command Flow

```
Human intent → Private Client AI → Hermes → DAO logic → Reachy executor → DAO LLC attribution
```

## Surface Model

| Surface | Role |
|---|---|
| CLI | Hermes commands (`hermes glocal`, `hermes dao status`, `hermes reachy`) |
| VS Code | `remoteUse.reachyProbe`, `remoteUse.reachyPanel` |
| Web | `agentic.html` and marketplace viewports |
| HF Space | `hermes-reachy` domain application |
| Physical | Reachy Mini / Reachy 2 actuators |

## Identity vs Logic Separation

- `DAO` = logic surface: proposals, votes, execution contracts
- `DAO LLC` =Wyoming identity surface: formation, membership, attribution

Do not conflate. Robot actions are attributed to DAO LLC; governance is decided in DAO.

## Runtime Stack

- Hermes Agent: intent router + local control plane
- mech-lang.org: Rust robot vision + actuator runtime
- Reachy Mini: default hardware operator
- Reachy 2: full humanoid operator
- MuJoCo: simulator-first path
- HuggingFace Space: global marketplace surface
- Stripe/Doola: payments + formation rails

## Operator Commands (Target)

```
remoteUse.reachyProbe   -> minimal state read
remoteUse.reachyPanel   -> operator control surface
hermes reachy           -> 3-command entrypoint
```

## White-Label Constraint

HuggingFace Space must be white-label: no mandatory upstream branding, no telemetry fences, deterministic local-first execution. Auth is via org token, not personal identity.

## Verification Rule

UI/viewport changes verified by localhost render/build only. Backend/CLI changes use pytest.
