# #opensourceware

#250USA
#æ^neuroplasticity

## Breakout 002: Accelerator

## I. Phase

- Breakout 001: **250-baseline**
- Breakout 002: **Accelerator**

## II. Goal

Turn successful formations into higher-rate replicated outcomes using local hardware + deterministic runtime.

## III. Prerequisites

- Breakout 001 passed baseline:
  - 250 formations with shared state
  - deterministic input → deterministic output
  - `AE_LOCAL_OLLAMA_RUN_OK` confirmed
  - Hermes CLI smoke `AE_LOCAL_OLLAMA_CLI_SMOKE_OK` confirmed
-出战 locally:
  - `ae://local^ollama`
  - `mech-lang`
  - `+æ@vlc` + `ae://ffmpeg^omniverse+live`

## IV. Accelerator Contract

```
Breakout 002 = Base 250 + 2 variables
```

| Group | Variable A | Variable B |
|-------|----------|----------|
| 000-124 | baseline | baseline |
| 125-187 | +1 | same prompt |
| 188-249 | +2 | same prompt |

## V. Rule

- Only change ONE variable per cohort
- Keep prompt identical across all 250
- Run on Victus i5/RTX GA uration only

## VI. Output

- cohort delta JSON:
  - cohort_id
  - variable_a
  - variable_b
  - formation_count
  - primary_metric
  - neuroplasticity_reward_signal
- proof media encoded by `ae://ffmpeg^omniverse+live`
- hashed manifest published to `+æ` governance layer

## VII. Pass Criteria

- determinant primary metric improvement from 125-187 cohort relative to 000-124 baseline
- deterministic baseline improvement from 188-249 cohort relative to 125-187 cohort
- `AE_LOCAL_OLLAMA_RUN_OK` maintained across all runs
- full audit trail: input hash, output hash, timestamp, runner id

## VIII. Next Level

Once 002 passes: **Accelerator tier unlocks local RTX execution**.
- `cuda_deterministic_enabled = true`
