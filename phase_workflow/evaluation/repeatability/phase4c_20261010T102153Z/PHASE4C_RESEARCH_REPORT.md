# Phase 4C — UART verification repeatability and stronger baselines

## Scope and provenance

- All experiments are simulation-only; frozen UART RTL is unmodified.
- Each run uses exactly 10 initial scenarios and CPB 8,16,32,64.
- The archived Hermes-AI result is **one earlier independent model call**, not a multi-trial distribution.
- Original payload-only random baseline cannot exercise framing, reset, busy or paired-frame operations.
- The protocol-aware random baseline has access to the same five scenario kinds as Hermes and a pool of coverage-targeted payloads.
- The balanced directed baseline explicitly targets the ten known bins, so it is a stronger human-directed comparator.
- Protocol-aware random draws are with replacement and may repeat scenarios.
- Simulation cycle counts and model inference time/cost are not equalized by a ten-scenario budget.

## Results

| Suite | Seeds/trials | Mean coverage | Std. dev. | Range | 100% coverage trials |
|---|---:|---:|---:|---:|---:|
| Payload-only random | 10 | 13.0% | 6.749 | 10.0–30.0% | 0/10 |
| Protocol-aware random | 10 | 69.0% | 9.944 | 50.0–80.0% | 0/10 |
| Balanced directed | 1 | 100.0% | N/A | 100.0–100.0% | 1/1 |
| Original Hermes AI (single call) | 1 | 100.0% | N/A | N/A | 1/1 |

## Interpretation limits

One successful Hermes AI call is insufficient for a claim of statistically superior model performance.
The balanced-directed and protocol-aware random comparisons expose the limitations of the original payload-only baselines.
The ten functional bins are coverage objectives, not formal completeness or discovery of real design faults.
Independent Hermes generations, model/provider identification, inference time/cost, literature review,
negative tests, and clean-environment reproducibility remain separate evidence tasks.

The full machine-readable simulation evidence and scenario files are under `simulation_runs/`.
