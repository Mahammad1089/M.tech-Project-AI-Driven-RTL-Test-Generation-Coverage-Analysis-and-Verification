# AI-Driven RTL Test Generation, Coverage Analysis and Verification

M.Tech major project, VLSI Design, Department of ECE, RGMCET (Autonomous).

## Summary

An LLM-generated test suite detected all 15 injected faults in a UART design at four clock-divider settings (300 of 300 mutant runs), while same-budget random suites detected 47% to 82%. The project builds a coverage-driven flow in which an LLM proposes RTL test scenarios from AST-extracted design knowledge, and measures them with function-bin coverage, RTL line coverage and mutation testing. It is a complementary study to AssertMiner-pro (see below), not a reproduction or a replacement of it.

## Relationship to the base paper

**Base paper:** Y. Wang, J. Zhou, H. Lyu, B. Chen, M. Shi, Z. Chao, T. Wang, H. Li, "AssertMiner-pro: Enhanced module-level spec generation and assertion mining with LLM guided by top-down hierarchical strategies," *Integration, the VLSI Journal* 110 (2026) 102797, doi:10.1016/j.vlsi.2026.102797.

AssertMiner-pro extracts reliable structure from RTL with an AST, derives a specification for each module top-down through the call hierarchy, and has an LLM mine SystemVerilog assertions from those specifications in one pass. It evaluates the assertions with formal coverage (JasperGold) and mutation testing, and reports the error detection ratio (EDR).

This project keeps the idea of grounding the LLM in AST-extracted structure and evaluating with coverage plus mutation testing. It differs in four ways.

| | AssertMiner-pro | This project |
| --- | --- | --- |
| LLM output | SVA assertions | Test scenarios, validated before simulation |
| Generation | One pass, invalid assertions filtered out | Feedback of coverage gaps into the next prompt (shown on the FSM and FIFO studies) |
| Evaluation tools | JasperGold (formal), commercial | Icarus Verilog, Verilator, Yosys, PyVerilog (open source) |
| Model | GPT-4o | `upstage/solar-mini4:free` through Hermes Agent v0.21.3, one call per generation |
| Top-down hierarchical specs | Yes, the central contribution | **Not yet implemented; planned** (see Roadmap) |

The two works are complementary: assertions check behaviour, and stimulus exercises it.

## Related work

Several recent works also close the loop between an LLM and coverage feedback for RTL verification, and this project sits in that line as well:

- UVM^2, an LLM-aided UVM machine that refines test stimuli from coverage feedback (arXiv 2504.19959).
- AgentDV, a closed-loop agentic framework combining LLM test generation, tool execution and coverage feedback (arXiv 2608.27148).
- ChipFuzzer, an LLM-driven hardware fuzzing framework with a coverage-guided stage (arXiv 2607.10340).
- An earlier study feeding EDA-tool coverage reports back into LLM testbench generation (arXiv 2406.17132).

This project does not claim to be the first closed-loop LLM test generator. Its distinguishing elements are the AST-grounded knowledge step, the fault-injection evaluation with an explicitly extended oracle, and full provenance of every LLM call.

## Metric mapping to the base paper

| Base paper | This project | Note |
| --- | --- | --- |
| Error detection ratio (detected mutants / injected mutants) | Kill rate (killed runs / mutant runs), per suite | A run is one suite, one mutant and one clock setting; 15 hand-written mutants |
| Branch, statement and toggle coverage (formal, JasperGold) | RTL line coverage (closest counterpart to statement coverage) and toggle coverage, from Verilator simulation | Branch coverage is not measured. Not directly comparable with formal results |
| N / S / P: generated, syntax-correct and FPV-passed assertions | Scenarios generated, validated by the framework, then simulated | Reported per generation call |
| Module-level coverage tables | Per-module coverage | Planned with the hierarchy extension |
| No cost reporting | About 15,050 tokens in and 2,000 out per generation, mean 28.9 s over 5 trials | Free-tier model, no monetary cost |

## Key results (UART; TX and RX in baseline and optimized versions)

**Equivalence.** 1,845,552 of 1,845,552 comparisons passed at clock dividers 8, 16, 32 and 64 (TX 332,376; RX 1,512,400; hybrid loopback 776). These are per-cycle comparisons from 273 TX and 260 RX frames, not distinct tests.

**Area and power** (Nangate 45 nm typical, 10 ns clock). The selected hybrid (baseline TX with optimized RX) is 425.600 um^2 against 450.604 um^2, a 5.55% reduction, with 1.0% lower estimated power. The optimized TX alone is larger and uses more power, so it was rejected. Power assumes 0.1 transitions per ns.

**Coverage at clock divider 16.**

| Measure | Directed | Random | AI suite |
| --- | --- | --- | --- |
| Function bins (of 10) | 6 | 2 | 10 |
| RTL line coverage, all lines | 92.6% | 92.6% | 97.1% |
| RTL line coverage, excluding 4 unreachable `default` branches | 95.4% | 95.4% | 100% |
| Toggle coverage (includes testbench) | 64.3% | 66.1% | 66.1% |

**Fault injection** (15 mutants, 27 suites, 4 clock settings, 1,620 runs, 108 clean controls with no false alarms).

| Method | Suites | Killed / runs | Kill rate |
| --- | --- | --- | --- |
| AI suites | 5 | 300 / 300 | 100% |
| Archived AI suite | 1 | 60 / 60 | 100% |
| Balanced directed | 1 | 60 / 60 | 100% |
| Protocol-aware random | 10 | 492 / 600 | 82.0% |
| Payload-only random | 10 | 284 / 600 | 47.3% |

## What this project claims, and what it does not

**Supported by the evidence**

- Bin-informed AI generation detects faults that same-budget random testing misses, in all 5 independent trials at all 4 clock settings.
- The optimized receiver is equivalent to the baseline on the tested stimulus, and the hybrid reduces area by 5.55%.
- On the FSM and FIFO studies, feeding coverage gaps back into generation closed them (FSM: +25.0 points; FIFO: 90% to 100% with one extra scenario).
- Every LLM call is traceable to a session record with model, tokens and prompt.

**Not claimed**

- That the AI beats a good hand-built directed suite: both reach 100% fault detection.
- That this work is more powerful than, or a replacement for, AssertMiner-pro. It uses a different output type, tool chain and design scale.
- That the feedback loop closed gaps on the UART: the first AI attempt already reached 10 of 10 bins.
- Results at scale, on formal analysis, or on designs from the base paper's benchmark set.

## Limitations

- **Oracle changed after the fact.** The first checker could not see the reset-timing fault (0 of 108 detections for every suite). The oracle was extended with stronger assertions, giving 52 of 108 kills, without changing any scenario. Only that one mutant differs between the two checkers.
- **A post-hoc mutant.** The fifteenth mutant was added after the coverage analysis showed that only the AI suites executed the false-start branch. Its result is the same under both checkers.
- **Bins and mutants overlap by design,** so informed suites beat uninformed random suites partly by construction.
- **The LLM selects from a hand-written menu** of five scenario kinds, with a hand-written contract. The 10-of-10 bin result partly reflects that, which is the gap the planned hierarchy step addresses.
- **Narrow scope:** one small design, simulation rather than formal analysis, coverage at one clock divider, one AI suite in the line-coverage measurement.
- **Estimates:** power uses an assumed activity; timing slack is nearly identical for all variants.
- **Reproducibility risk:** a free model tier expired once during the project (HTTP 404 on `solar-pro4:free`). Pin the model, as below.

## Reproduce

```bash
source .venv/bin/activate          # PyVerilog 1.3.0 lives here
python -m pip install pyverilog==1.3.0

# Tool versions used: Icarus Verilog 12.0, Verilator 5.032, Yosys 0.52

# Mutation study, 15 mutants, corrected checker (dry run first)
python3 phase_workflow/tools/phase4e_false_start_checker.py --dry-run --scope all
python3 phase_workflow/tools/phase4e_false_start_checker.py --scope all

# Summary check of saved milestone results
python3 validate_project_results.py
```

**LLM.** Scenarios were generated by `upstage/solar-mini4:free` (provider `nous`) through Hermes Agent v0.21.3 in one-shot mode. To pin the model for a new run, pass `-m upstage/solar-mini4:free --provider nous` to the Hermes command, or set it in your Hermes configuration. Check `hermes model` if the free tier is no longer available.

**Technology library (not included).** PPA results use the Nangate 45 nm Open Cell Library (typical corner). It is distributed by Nangate under its own license and is not committed here. Download it from the official source and place it at `extensions/technology/nangate45/NangateOpenCellLibrary_typical.lib`.

## Repository layout

| Path | Contents |
| --- | --- |
| `phase_workflow/phase_01_rtl` | Benchmark RTL, including the UART variants |
| `phase_workflow/phase_02_parsing` | PyVerilog AST extraction and saved knowledge JSON |
| `phase_workflow/phase_03_ai_verification` | Hermes bridge, scenario generation, testbench generator and results |
| `phase_workflow/phase_04_uart_novelty` | UART integrated research report |
| `phase_workflow/evaluation` | Fault injection, feedback closure and repeatability studies |
| `phase_workflow/tools` | Mutation and checker tools, including the `phase4e_*` extension |
| `extensions/results/day30` | UART, ALU, FIFO and FSM equivalence and PPA evidence |

## Roadmap

1. **Top-down hierarchy (the base paper's central idea).** A small system with call depth 3, general call-graph and I/O-table extraction, LLM-derived module specifications, per-module scenarios with a coverage feedback loop, and a flat-against-hierarchical mutation study. See `phase_workflow/phase_05_hierarchy/` once started.
2. LLM-written assertions as checkers, combining the base paper's output type with the closed loop.
3. A design from the base paper's benchmark set (for example I2C or UART from IWLS 2005) for a direct comparison.
4. Automatic mutant generation.
