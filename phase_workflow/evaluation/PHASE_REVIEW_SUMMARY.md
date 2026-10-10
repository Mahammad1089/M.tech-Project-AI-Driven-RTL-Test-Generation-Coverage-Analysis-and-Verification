# Phase-Oriented M.Tech RTL Verification — Research Review

## Development flow

| Phase | Function | Verified source |
|---|---|---|
| Phase 1 — RTL Design | Baseline and optimized ALU, FIFO, FSM, UART | `phase_01_rtl/` |
| Phase 2 — RTL Parsing | PyVerilog AST to UART knowledge JSON | `phase_02_parsing/` |
| Phase 3 — AI Verification | Hermes scenarios, independent oracle, Icarus simulation, coverage | `phase_03_ai_verification/` |
| Phase 4 — Research Evaluation | PPA, repeatability, fault sensitivity and gap closure | `phase_04_uart_novelty/`, `evaluation/` |

## Evidence-verified status

- Original technical audit: **18/18 PASS** (archived ALU, FIFO, FSM and UART evidence).
- Integrated RTL/PyVerilog/Hermes/UART workflow: **12/12 PASS**.
- AI-generated UART scenario run: **verified live model call, validated scenarios, passing simulations, and 10/10 defined functional bins**.

| Method | Scenarios | Minimum bin coverage | Checks | Failed checks |
|---|---:|---:|---:|---:|
| Directed | 10 | 60% | 30,116 | 0 |
| Deterministic random | 10 | 20% | 30,116 | 0 |
| Hermes AI initial | 10 | 100% | 36,408 | 0 |

## Historical results (independent evidence)

- ALU equivalence: 2,048/2,048 checks; 5-fF mapped area/power improvements: 13.28%/14.78%.
- FIFO equivalence: 124,008/124,008 checks, four configurations.
- FSM: 20 functionally verified variants and 147,844 independent checks.
- UART architecture: archived baseline/optimized/hybrid mapping and pre-layout estimates.

## Extended research evidence

The following follow-up studies are archived independently under `evaluation/`:
- `repeatability/`: ten-seed random strategies and independent Hermes generations.
- `fault_injection/`: original and corrected-oracle UART mutation tests.
- `feedback_closure/`: targeted feedback experiment and matched directed control.
- `phase_04_uart_novelty/research/`: literature report and evidence audit.

The evidence archive—not this summary—is authoritative for repeatability, mutation
score, feedback cost and confidence limitations. The selected Git source tree does not
include all original simulation outputs.

## Responsible research claims

- AI coverage is defined against ten scenario-based functional bins; not formal proof.
- Balanced-directed verification can match the observed AI coverage and fault sensitivity.
- Correcting reset-cycle assertions improves observability; it does not make a model smarter.
- UART mapped area and estimated power are independent of the Hermes verification result.
- The project remains simulation-only; no physical silicon or post-route proof is claimed.
- Reproducing fresh AI calls requires a supported provider/model; reports are not guaranteed identical.

## Reviewer documents

- `docs/MTech_Phase_4F_Research_Thesis_Draft.docx`
- `docs/MTech_Phase_4F_Review_Presentation.pptx`
- `evaluation/workflow_status.json` (generated local technical gate)
- `phase_04_uart_novelty/research/PHASE4E_EVIDENCE_TRACE.md` (research evidence map)

Old execution-era paths are retained internally solely for historical traceability.
