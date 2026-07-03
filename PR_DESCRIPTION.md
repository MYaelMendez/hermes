# Hermes Conductor — Scheme Dispatcher + Operator Grammar

## Summary

Adds a standalone, provider-neutral scheme dispatcher for Hermes intent routing.
This introduces `SchemeDispatcher` as a compact, testable abstraction for
operator URI grammar, plus first-class viewport/runtime surface definitions.

## Scope

- `hermes_cli/conductor.py` — refactored to `SchemeDispatcher` with runtime
  registration, longest-prefix matching, and stable `run_hermes(payload)`
  contract
- `tests/hermes_cli/test_conductor.py` — dispatcher policy tests
- `SPEC.md` — canonical operator grammar spec
- `CAPABILITIES.md` — runtime/scheme/bridge capabilities
- `skills/hermes-operator-grammar/SKILL.md` — reusable operator grammar skill

## Behavior

- Registered schemes are matched by longest prefix, not registration order
- Builtin schemes include: `c://cc`, `pc://`, `pc://run`, `mcp://`,
  `vscode://`, `reachy://`, `H://`, `hermes://`, `NOUS://`, `llc://`,
  `daollc://`, `intent://`
- Unknown input falls back to bounded hermes CLI subprocess execution
- Returns stable contract: `ok`, `rc`, `stdout`, `stderr`, `surface`, `scheme`

## Verification

```
python -m pytest tests/hermes_cli/test_conductor.py -q
# 11 passed
```

Relevant targeted suite:
```
python -m pytest tests/hermes_cli -q -k "not (gateway or systemd or session_browse or update_gateway_restart or update_autostash or test_home_expansion or test_absolute_path_triggers_completion)"
# 506 passed
```

## Notes

- 2 pre-existing Windows-only failures remain in `test_path_completion.py`;
  they are unrelated to this change
- Rust/WASM crate draft present but not buildable in this environment
- `contest-submission/` is intentionally untouched outside this PR scope
