# Phase 4C-2 — Independent Hermes UART generation trials

## Protocol

- Every trial starts a fresh Hermes one-shot call with the **same frozen prompt**.
- Exactly ten JSON scenarios are required and checked by the project whitelist validator.
- Each accepted set is independently simulated with Icarus at CPB 8, 16, 32, and 64.
- Frozen UART RTL source hashes are checked; original reports, scenarios and audits are not overwritten.
- Failed Hermes calls, invalid scenarios or failed simulations count as **unsuccessful trials**, not discarded samples.
- Same scenario budget does not equalize simulation cycles, model latency, inference cost or human engineering effort.

## Results

| Trial | Hermes | Valid 10 | Simulation | Min coverage | Checks | Cycles | Hermes elapsed (s) |
|---|---|---|---|---:|---:|---:|---:|
| 01 | PASS | PASS | PASS | 100.0% | 36408 | 18144 | 45.139 |
| 02 | PASS | PASS | PASS | 100.0% | 36408 | 18144 | 28.507 |
| 03 | PASS | PASS | PASS | 100.0% | 36408 | 18144 | 32.759 |
| 04 | PASS | PASS | PASS | 100.0% | 36408 | 18144 | 29.841 |
| 05 | PASS | PASS | PASS | 90.0% | 36408 | 18144 | 31.941 |

## Statistics and interpretation

- Planned Hermes trials: **5**
- Complete passing trials: **5**
- Failed/incomplete trials: **0**
- Mean coverage among successful simulations only: **98.0%** (n=5).
- Complete 10/10 functional-bin coverage: **4** successful trial(s).
- Invalid/malformed model outputs are excluded from the coverage mean but INCLUDED in failure counts.
- The archived initial Hermes AI result of 100% is a separate earlier trial and is not counted again.
- Protocol-aware random mean (ten seeds) was 69%; balanced directed attained 100% in one trial.
- A 100% functional-bin score is not mutation coverage, formal completeness or proof of zero RTL defects.
- Calling the same model repeatedly does not ensure statistically independent samples if the provider is deterministic.
- Record the model/provider and costs manually if known; this script does not expose API configuration.

Overall execution status: **PASS**

## Research follow-ups

- Negative/mutation testing to quantify actual fault detection.
- Compare with stronger directed strategies, and account for simulation cycles and model usage.
- Literature-based prior-art and novelty study; final submission reproduction.
