# Hermes Viewport Computer Blueprint

## Premise

HTML is the skill, but the viewport computer is the **global Hermes surface**. Every operator, agent, module, and subagent runs through one executable HTML shell. It is not a web page; it is the control plane born again as a browser-native runtime.

## Why "private client"?

In distributed systems, a **private client** is an autonomous execution surface: bounded, sovereign, local-first, with its own state, credential scope, and capability contract. Hermes private clients are exactly that.

- each subagent = private client
- viewport computer = private client runtime
- conductor = private client orchestrator
- DAO = governance/logic layer above private clients

This naming is intentional. `privateclient.ai` is therefore:
- an architectural primitive, not a brand needing traffic
- a legitimate CS concept rendered as Hermes governance
- the canonical address scheme for every Hermes private client: `pc://`

## Operator grammar

These agentic primitives are **necessary prior to building up**.

- `c://` = command prompt
- `c://cc` = change context
- `llc://` = cli.llc command interface
- `hermes://` = default Hermes-agent runtime
- `H://` = global agentic domain for Hermes-agent
- `H://cc <target>` = Hermes global-domain change context
- `NOUS://` = Nous Research provider/runtime
- `vscode://` = VS Code control plane / editor surface
- `c://cc vscode://` = change control plane to VS Code remote/editor
- `reachy://` = Reachy Mini robot/operator surface
- `mcp://` = Model Context Protocol tools surface
- `mcp://tools` = tool runtime via MCP
- `daollc://` = DAO LLC governance / identity
- `pc://` = private client address / runtime
- `pc://run <name>` = run private client `<name>` via conductor
- `+æ://` = intent/permission token issued by DAO LLC membership

Mappings:

- `+æ://private client^glocal` = laptop/agent as a DAO
- `+æ://operator^glocal` = human intent surface
- `llc://` = business/brand surface
- `c://cc pc://` = switch to private client runtime
- `c://cc daollc://` = switch to DAO LLC governance context
- `pc://` = address a specific subagent/private client
- `hermes://` / `H://` = canonical/default Hermes runtime
- `NOUS://` = Nous Research provider/runtime
- Hermes conductor = intent router above all schemes

No shell is built without this grammar.

## Global contract

- `hermes viewport open` → launches viewport computer
- `html-as-skill` → canonical viewport template contract
- Subagent → receives a local viewport instead of raw text channels
- Domain mapping → every domain gets a viewport slice, same tokens, same prompt rhythm

## Primary surfaces

01 PROMPT → `>_æ|` intent input
02 MODEL → local/remote inference via WebLLM/WebMCP intent routing
03 EXECUTE → Hermes conductor → DAO logic → `🤖` executor → DAO LLC attribution
04 TRUST → private client governance, credential/budget guardrails
05 ATTEST → deterministic manifest + attestation hash retroactively

## Design invariants

- gold-on-void
- JetBrains Mono / Orbitron
- ASCII-safe command model
- one template, many surfaces
- subagent bootstrap path uses viewport as handshake

## Operator commands

```txt
hermes viewport open
hermes viewport status
remoteUse.reachyProbe
remoteUse.reachyPanel
```

## Verification

- localhost render/build check for HTML surfaces
- pytest for CLI/backend only
- viewport shell must expose `>_æ|` terminal and DAO separation line
