# Scalar Supremacy

Rule: the most scalable formal implementation supersedes less scalable alternatives.

In `conductor.py`, this prevents runaway surface expansion by blocking bare
scalar authority forms that have no deterministic policy binding at that layer.

Blocked forms:
- `status` as a bare scalar tail for mutable schemes
- `+æ://status`, `pc://status`, `daollc://status`

Effect: merge writes are gated by the current executor resource bound.
