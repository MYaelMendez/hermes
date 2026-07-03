---
name: hermes-operator-grammar
description: "Canonical Hermes operator grammar: c://, pc://, vscode://, hermes://, H://, NOUS://, daollc://, llc://, +æ://, H://cc, pc://run"
---

# Hermes Operator Grammar

Use when: user input contains `c://`, `pc://`, `vscode://`, `hermes://`, `H://`, `NOUS://`, `daollc://`, `llc://`, `+æ://`, `H://cc`, `pc://run`, or any context/gov/prompt/runtime/plan routing in Hermes.

## Primitive glossary

- `c://` = command prompt
- `c://cc <target>` = change context to `<target>`
- `H://cc <target>` = Hermes-native change context
- `hermes://cc <target>` = same
- `hermes://` = default Hermes-agent runtime
- `H://` = global agentic domain for Hermes-agent
- `NOUS://` = Nous Research provider/runtime
- `llc://` = CLI LLC business/command surface
- `daollc://` = DAO LLC governance / identity
- `+æ://<name>` = intent/permission token / DAO membership surface
- `pc://` = private client address / runtime
- `pc://run <name>` = run private client `<name>` via conductor
- `vscode://` = VS Code control plane
- `vscode://file/<path>` = open file/folder in VS Code
- `run pc://<name>` = same as `pc://run <name>`

## Canonical mappings

- `+æ://private client^glocal` = laptop/agent as a DAO
- `+æ://operator^glocal` = human intent surface
- `llc://` = business command shell
- `hermes://` = Hermes runtime
- `H://` = global agentic domain for Hermes-agent
|- `vscode://` = VS Code control plane
- `c://cc vscode://` = switch primary context to VS Code remote
|- `reachy://` = Reachy Mini robot surface
|- `mcp://` = MCP tools surface
|- `mcp://tools` = tool runtime via MCP
|- `pc://` = private client runtime
|- `daollc://` = DAO identity/governance

## Execution priority

1. Backend: conductor dispatches schemes in `hermes_cli/conductor.py:_dispatch`
2. Bridge: `apps/reachy/app.py` exposes `/conductor`
3. Viewport HTML shell: send recognized schemes to `/conductor` with `{cmd, args}`

## Universal rule

Every operator context edit is handled through the conductor; never parse these schemes in ad hoc shell logic.
