# Phase-Based Execution and Review Guide

## Objective and scope

Integrate an end-to-end RTL → PyVerilog/Python knowledge → Hermes AI scenario generation → deterministic testbench → UART verification → feedback closure flow. Retain mapped PPA results as complementary UART architecture analysis. The four DUTs remain ALU, FIFO, sequence detector and UART. This is a simulation-only research project.

## All required tasks (do not skip)

| ID | Phase | Action | Completion evidence | Gate |
|---|---|---|---|---|
| P1.01 | 1 | Preserve the current verified Git commits and archive | Existing tracked source and master audit | Historic PASS |
| P1.02 | 1 | Snapshot ALU/FIFO/FSM/UART original and optimized RTL | Phase RTL paths + SHA manifest | `organize.py` |
| P1.03 | 1 | Validate design interface, reset, CPB restrictions and UART 8N1 behavior | RTL declarations + existing functional report | Existing evidence |
| P2.01 | 2 | Check PyVerilog and environment tools | Dependency check output | User WSL |
| P2.02 | 2 | Parse all four UART Verilog modules into AST | `uart_knowledge.json` AST origin | New |
| P2.03 | 2 | Extract ports, parameters, clocked FSMs, state names, protocol assumptions | Validated model fields | New |
| P2.04 | 2 | Hash all parsed UART RTL and reject changed source | SHA-256 per module | New |
| P3.01 | 3 | Derive UART objectives and coverage bins | `objectives.json` | New |
| P3.02 | 3 | Create controlled Hermes prompt | `hermes/initial_prompt.txt` | New |
| P3.03 | 3 | Run real Hermes and capture raw response + call failure modes | Raw Hermes JSON | New |
| P3.04 | 3 | Reject malformed/unsafe scenarios with strict whitelist | Validated scenarios JSON | New |
| P3.05 | 3 | Generate self-checking Verilog testbenches | `tb_uart_phase.v` per suite/configuration | New |
| P3.06 | 3 | Run Icarus compile/simulation with CPB 8/16/32/64 | compile/sim logs | New |
| P3.07 | 3 | Verify TX/RX baseline vs optimized cycle outputs + transmitted byte and framing errors | Zero failed checks | New |
| P3.08 | 3 | Run equal-budget directed and deterministic random baselines | Coverage summaries | New |
| P3.09 | 3 | Extract observed coverage bins rather than model-proposed bins | `COVERAGE=` simulation marker | New |
| P3.10 | 3 | Identify uncovered bins and send a feedback prompt | feedback prompt + raw Hermes JSON | New |
| P3.11 | 3 | Simulate closure scenarios and record before/after coverage | `ai_feedback_*` simulation reports | New |
| P3.12 | 3 | Compare initial 10-scenario budgets fairly; report closure effort separately | `evaluation_summary.json` | New |
| P4.01 | 4 | Preserve original UART baseline/optimized/hybrid verification and PPA | `uart_report.json` | Historic PASS |
| P4.02 | 4 | Explain TX shift register, RX shift register and hybrid selection | Review documentation + PPA CSV | Historic PASS |
| P4.03 | 4 | Establish AI-UART research contribution through measured test efficiency | AI versus directed/random coverage/time/results | New |
| P4.04 | 4 | Record limitations: protocol timing, path portability, power activity and pre-layout PPA | Review scope guide | Documentation |
| EV.01 | Evaluation | Run phase-level acceptance audit, keeping old and new statuses separate | `evaluation/workflow_status.json` | New |
| EV.02 | Evaluation | Update thesis with only verified new measurements and novelty comparison | Thesis revision | Pending |
| EV.03 | Evaluation | Review references and research novelty against current literature | Related-work comparison | Pending |
| EV.04 | Evaluation | Package result logs, source code and phase view without restricted cell libraries | Evidence archive | Pending |
| EV.05 | Evaluation | Perform a final clean WSL run and validate review demonstration | Reproducibility transcript | Pending |

## Exact commands and acceptance criteria

**Phase 1, non-destructive staging**

```bash
cd ~/Mtech_project/AI_RTL_Verification
python3 phase_workflow/tools/organize.py
python3 phase_workflow/tools/organize.py --check-only
```

Acceptance: 18 recorded master requirements PASS; original source SHA hashes identical to review snapshots; no originals changed.

**Phase 2, parsing**

```bash
bash phase_workflow/tools/check_dependencies.sh
python3 phase_workflow/phase_02_parsing/extract_uart.py
python3 -m json.tool phase_workflow/phase_02_parsing/results/uart_knowledge.json >/dev/null
```

Acceptance: PyVerilog AST parser succeeds on four real RTL modules, validates state/clock/port contract, emits hashes and a 10-bin coverage model. The reader must distinguish AST-extracted structural facts from project-specific protocol requirements.

**Phase 3A, deterministic non-AI baselines**

```bash
python3 -m unittest discover -s phase_workflow/tests -v
python3 phase_workflow/phase_03_ai_verification/uart_ai_pipeline.py --mode baseline
```

Acceptance: Both directed and randomized runs pass across CPB 8/16/32/64; evidence includes explicit zero failed checks, recognized coverage markers, logs, scenario arrays, simulation counts and run times.

**Phase 3B, real AI test generation and coverage closure**

```bash
python3 phase_workflow/phase_03_ai_verification/uart_ai_pipeline.py --mode all
```

Acceptance: Hermes invocation status PASS; raw JSON safely parsed; no unauthorized commands embedded in test generation; UART scoreboard passes; ten required bins covered on each CPB; coverage and simulation cost compared with the equal-budget baselines. If Hermes or a tool is unavailable, the correct status is **PENDING**, not PASS. Importing arbitrary candidate JSON does not prove Hermes was used.

**Phase 4, evaluate the research contribution**

```bash
python3 phase_workflow/phase_04_uart_novelty/build_integrated_report.py
python3 phase_workflow/tools/final_audit.py
```

Acceptance: every gate prints PASS. Previous UART PPA must remain explicitly mapped/pre-layout and not be mischaracterized as new experimental AI results. A claim of improved coverage requires the measured comparison to support it; do not presume AI outperforms directed testing.

## Review discussion outline

1. **Problem:** manual verification effort and missed UART timing/protocol corner cases.
2. **Input:** original, optimized and hybrid-compatible UART Verilog modules.
3. **Parsing:** PyVerilog AST extracts a structured module/port/state/parameter knowledge model in Python.
4. **Reasoning:** Hermes receives the model, coverage objectives and gaps and proposes structured cases.
5. **Validation:** a whitelist of scenarios stops arbitrary executable code from entering verification.
6. **Testbench:** the deterministic generator emits a self-checking TB; the LLM is not the oracle.
7. **Oracle:** reference byte, framing checks, TX/RX per-cycle equivalence and reset tests.
8. **Coverage:** measured functional bins, not claims in Hermes output.
9. **Feedback:** uncovered bins drive follow-up Hermes queries.
10. **Evaluation:** equal-budget directed/random/AI comparison plus additional closure effort.
11. **UART hardware trade-off:** independently verified mapped area and assumed-activity power comparison.
12. **Novelty:** only claims established by controlled experiments and prior-art review.

## Historic-result preservation and naming

Review-visible filenames and sections use **phases**, not a timeline. The original project retains immutable older source paths and test logs, because changing them would break historical scripts, checksums and evidence references. The private provenance map links review aliases back to original source file locations and hashes. Do not delete or mass-replace historical source identifiers.
