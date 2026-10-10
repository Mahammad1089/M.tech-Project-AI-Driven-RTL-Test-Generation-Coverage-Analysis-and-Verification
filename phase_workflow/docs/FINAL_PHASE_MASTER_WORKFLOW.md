# Final Phase-Based Development Workflow

**Project:** AI-Driven RTL Test Generation, Coverage Analysis and Verification
**Verified commit reviewed:** `9c44150185d5`
**Scope:** simulation-only, no FPGA fabrication or physical silicon measurement.

## Phase 1 — RTL Design

**Goal:** Define functional DUTs and preserve both baseline and optimized RTL implementations.

1. Specify ALU, FIFO, FSM/sequence detector and 8N1 UART functionality.
2. Maintain reference RTL and optimized design variants; document interfaces, resets, TX/RX sequencing and supported clock settings.
3. Explain ALU shared add/sub resources, FIFO reset optimization, Mealy/Moore alternatives and UART TX/RX trade-offs.
4. Verify RTL snapshots and compare independently with simulation-based functional oracles.

**Primary repository locations:** `phase_workflow/phase_01_rtl/` and historical `rtl/` / `extensions/rtl/`.
**Gate:** UART RTL present — Verified; earlier 18-requirement archive — Verified.

## Phase 2 — RTL Parsing to Python

**Goal:** Convert RTL into a structured Python knowledge model, avoiding invented behavioral claims.

1. Parse baseline and optimized UART modules with PyVerilog AST.
2. Extract module names, ports, parameters, state/control constructs, reset structure and RTL fingerprints.
3. Validate JSON structure and compare source hashes against the parsed modules.
4. Build verification objectives and UART functional coverage bins from the validated knowledge model and explicit design contract.

**Primary locations:** `phase_workflow/phase_02_parsing/` and `parser/`.
**Gate:** UART knowledge JSON — Verified.

## Phase 3 — AI/LLM Verification

**Goal:** Execute a controlled and measured AI-to-Verilog verification loop.

1. Generate deterministic verification objectives and a bounded Hermes prompt.
2. Obtain a real model response and validate candidate scenario JSON against the approved schema.
3. Generate self-checking Icarus Verilog testbenches; compare baseline and optimized behavior.
4. Run directed, deterministic random and AI suites at CPB 8, 16, 32 and 64.
5. Measure *simulator-observed* coverage, not coverage claimed by the model.
6. Identify missing bins, request targeted Hermes feedback, validate and re-simulate.
7. Keep equal initial test budgets separate from extra feedback calls and scenarios.

**Primary locations:** `phase_workflow/phase_03_ai_verification/`, `hermes/`, `test_generation/` and `coverage/`.
**Gate:** Three verification suites and real Hermes — Verified.

## Phase 4 — UART Novelty

**Goal:** Quantify verification effectiveness and the distinct UART architecture trade-off.

1. Report initial coverage for directed, payload-random, protocol-random and Hermes-based suites.
2. Evaluate multiple random seeds and independent Hermes-generated scenario sets.
3. Test fourteen deliberate UART fault operators; distinguish fault observation from stimulus coverage.
4. Compare original and corrected reset-checker detection, preserving original scores.
5. Demonstrate real feedback closure and compare with matched directed feedback.
6. Report RTL-equivalent UART mapped area / estimated switching-activity power for baseline, optimized and hybrid architecture; **do not attribute PPA improvements to AI**.
7. Review prior art and restrict novelty to evidence-supported claims.
8. Prepare phase-labeled diagrams, literature, thesis and review presentation; carry out source-only clean-checkout reproducibility.

**Primary locations:** `phase_workflow/phase_04_uart_novelty/`, `phase_workflow/evaluation/` and `phase_workflow/docs/`.
**Gates:** Architecture report — Verified; fresh AI repeatability — Verified; corrected mutation study — Verified; feedback — Verified.

## Experimental results already supported by the WSL execution transcripts

| Controlled experiment | Reported outcome | Qualification |
|---|---|---|
| Initial directed UART | 60% of 10 bins | 10 scenarios, four CPB settings |
| Initial payload-only random UART | 20% of 10 bins | One original suite, four CPB settings |
| Initial Hermes AI UART | 100% of 10 bins | 10 scenarios, 36,408 passing checks |
| Payload random, ten seeds | 13% mean coverage | 10 distinct seeds |
| Protocol random, ten seeds | 69% mean coverage | 10 distinct seeds |
| Balanced directed | 100% coverage | One expert-designed suite |
| Five independent Hermes trials | 98% mean, range 90–100% | Five successful runs; four complete |
| Corrected mutation checker | AI and directed: 100% of 14 mutants | Fault model limited to injected mutants |
| Targeted feedback on missing `edge_81` | 90% to 100% with one new Hermes scenario | Matched directed feedback also reaches 100% |

These are user-reported verified experiment outcomes. The repository audit independently checks that supporting result files are present; it does **not** rerun every mutation experiment or prove exhaustive hardware correctness.

## Final reviewer explanation

**RTL → PyVerilog AST → Python knowledge JSON → objectives → Hermes → scenario whitelist → generated self-checking Verilog testbench → Icarus simulation → functional coverage → coverage-gap feedback → research evaluation.**

The project is explained by four phases only. Historical chronological filenames remain internal dependencies for reproducibility; reviewers use this master workflow and phase-labeled source tree.

## Publication/reproducibility boundaries

- The 12/12 local workflow audit and 18/18 historical audit are not the same as a full clean-checkout replication of paid model requests and pre-layout technology mapping.
- The technology liberty file remains local unless redistribution rights are confirmed.
- The current experiments do not establish that AI outperforms balanced directed testing, nor that 10/10 functional bins give exhaustive UART correctness.
- Review-ready documents are still drafts until aligned with the university submission template.
