# #opensourceware

#250USA
#æ^neuroplasticity

## Reachy daollc Operator Protocol

## I. Operator Stack

| Layer | Role |
|---|---|
| Human | Intent source |
| Private Client AI | Command prompt target; local closed-loop agent |
| Hermes | Intent router / local control plane |
| DAO | Logic surface: proposals, votes, governance, execution contracts |
| DAO LLC | Identity surface: Wyoming DAO LLC formation, member roster, legal charter |
| Reachy Mini | Default hardware operator; physical actuator for DAO execution |
| mech-lang.org | Rust robot-vision runtime; parse/render layer for actuator primitives |
| NVIDIA Omniverse | Simulator for mass formation + training |
| Stripe / Doola | Formation rails + payments |

## II. Private Client AI

Definition:
- The **only** surface that accepts raw human command prompts
- Closed to external network by default
- Maps every prompt to a permitted daollc action
- Never exposes raw robot control or Wyoming membership directly to the operator
- Trained in critical-period windows: 30/60/90-day onboarding cycles

Properties:
- Local-first inference
- Tool-call restricted to allowed daollc memberships and Reachy operators
- Audit trail of every command → action → outcome

## III. Reachy Default Operator

Definition:
- The canonical hardware operator for every daollc.ai robotic entity
- Every physical daollc robot defaults to Reachy-class form
- Reachy membership is the first Wyoming DAO LLC robotic membership issued
- Other robot forms may be added later; Reachy remains the default template

Responsibilities:
- Execute physical-world daollc actions under private client AI direction
- Operate under mech-lang.org robot-vision guidance
- Maintain Wyoming DAO LLC membership compliance
- Report state/telemetry to the daollc simulator

## IV. Command Flow

```
Human intent → Private Client AI → Hermes → DAO logic → Reachy executor → DAO LLC attribution
```

- Private Client AI accepts raw human prompts only at the edge.
- Hermes routes to DAO logic first; no actuator command bypasses governance.
- DAO execution contracts are approved by DAO logic, not by raw operator whim.
- Reachy executes under DAO authority and reports state/telemetry.
- DAO LLC identity records attributed actions, membership, and charter compliance.

## V. Membership Semantics

- Private Client AI ≠ Wyoming member; it is a tool of a member
- Reachy Mini = Wyoming DAO LLC member/entity
- Human operator holds membership; Reachy executes under it
- Multiple humans can share one Reachy operator; all actions are attributed

## VI. Why This Wins

- Usable: entrepreneur doesn’t learn Rust, mech-lang, or Wyoming law
- Compliant: closed allowlist, US-person eligibility, Wyoming DAO charter
- Scalable: 250,000 formations simulated in Omniverse before live deployment
- Referral-driven: successful entrepreneurs refer more entrepreneurs via critical-period success
- Open-sourceware: no smart-contract literacy barrier, no lock-in

## VII. Proof of Concept

1. Form single Wyoming DAO LLC via Doola
2. Issue Reachy Mini as first robotic member
3. Deploy private client AI to local Hermes instance
4. Run command flow end-to-end
5. Capture success + referral
