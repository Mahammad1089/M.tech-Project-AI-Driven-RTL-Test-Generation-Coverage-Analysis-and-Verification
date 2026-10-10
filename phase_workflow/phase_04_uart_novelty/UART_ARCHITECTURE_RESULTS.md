# Phase 4 — UART Architecture and Novelty Evaluation

## Verified technology-mapped UART comparison

Historical baseline/optimized TX and RX combinations are compared at **CPB = 16**.
Power is estimated with assumed activity; area is mapped standard-cell area; timing is not a full-chip routed result.

| Configuration | Combined area (µm²) | Estimated power (µW) | Smallest component slack (ns) |
|---|---:|---:|---:|
| Baseline | 450.604 | 370.282 | 9.460 |
| Fully Optimized | 440.230 | 392.761 | 9.390 |
| Hybrid | 425.600 | 366.547 | 9.390 |

* Hybrid area reduction relative to baseline: **5.55%**.
* Hybrid assumed-activity power reduction relative to baseline: **1.01%**.
* This comparison is existing physical-design estimate evidence, not proof of new LLM test-generation novelty.

## Proposed AI-UART research evaluation

Compare the new validated Hermes-generated scenario coverage at the same initial test budget with directed and deterministic-random baselines. Report additional closure rounds separately. Only then decide whether the project demonstrates a measurable AI contribution.

## Scope limitations

No FPGA or fabricated hardware, no post-route timing or measured silicon power, no claim of formally exhaustive UART protocol correctness.
