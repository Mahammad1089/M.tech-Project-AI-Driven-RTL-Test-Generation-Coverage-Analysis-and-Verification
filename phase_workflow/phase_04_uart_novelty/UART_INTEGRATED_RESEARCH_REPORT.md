# Phase 4 — Combined UART Research Evaluation

## Experimental separation

The UART architecture comparison is **previously verified, pre-layout mapped evidence**. The UART Hermes functional coverage evaluation is a separate **new experiment**. Do not infer AI hardware area or power improvements from the two reports.

## A. Historic baseline / optimized / hybrid UART architectures

| Option | Combined area (µm²) | Estimated power (µW) | Minimum individual slack (ns) |
|---|---:|---:|---:|
| Baseline | 450.604 | 370.282 | 9.460 |
| Fully Optimized | 440.230 | 392.761 | 9.390 |
| Hybrid | 425.600 | 366.547 | 9.390 |

## B. UART test-generation strategy comparison

| Test strategy | Scenarios at initial budget | Minimum coverage across CPBs | Checks | Simulation cycles | Status |
|---|---:|---:|---:|---:|---|
| Directed | 10 | 60.0% | 30116 | 14984 | PASS |
| Deterministic random | 10 | 20.0% | 30116 | 14984 | PASS |
| Hermes — initial | 10 | 100.0% | 36408 | 18144 | PASS |

## C. AI-driven feedback closure

- Hermes source status: `HERMES_CHAT_ONESHOT`.
- AI scenarios after feedback: `10`.
- Minimum measured AI coverage: `100.0`.
- Coverage target met: `True`.
- Full integrated experimental status: **PASS**.

## D. Research-claim guardrails

- AI efficiency improvements may be claimed only when same-budget recorded metrics substantiate them.
- A 100% result refers to the ten defined functional test bins, not complete UART protocol state-space proof.
- The RX/TX RTL remains unchanged, and all experiments are simulation only.
- The PPA library is external; power is assumed-activity estimated, and timing is pre-layout.
- Publication-level novelty requires verified peer-reviewed prior-art comparison.

## Evidence locations

- Phase 2 UART knowledge: `phase_02_parsing/results/uart_knowledge.json`
- Hermes prompts, scenario validation and simulations: `phase_03_ai_verification/results/`
- Original UART architecture comparison: `phase_04_uart_novelty/reference/`
- Automated final acceptance: `evaluation/workflow_status.json`
