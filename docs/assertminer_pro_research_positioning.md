# Research positioning, metric alignment and claim boundaries

**Project:** AI-Driven RTL Test Generation, Coverage Analysis and Verification  
**Base paper:** Y. Wang et al., “AssertMiner-pro: Enhanced module-level spec generation and assertion mining with LLM guided by top-down hierarchical strategies,” *Integration*, vol. 110, art. 102797, 2026. DOI: https://doi.org/10.1016/j.vlsi.2026.102797.

## 1. Suggested abstract wording (for the manuscript)

This work presents a simulation-oriented AI-assisted RTL verification workflow informed by AST-based design analysis and LLM-guided verification. In contrast to AssertMiner-pro, which mines module-level specifications and deep assertions using top-down hierarchical context, this project uses PyVerilog-derived RTL knowledge to guide Hermes test-scenario generation, validates scenarios and executes self-checking simulations with Icarus Verilog, and measures predefined functional coverage. In the archived initial UART comparison, ten scenarios covered 10/10 defined categories with Hermes, versus 6/10 with a simple directed suite and 2/10 with a payload-random suite. These methods did not have identical simulation-cycle budgets, and a separately evaluated balanced-directed reference also achieved 10/10. A separately recorded 15-mutant corrected-checker evaluation reports complete detection for both AI and directed suites on its selected fault set. The contribution is an integrated, traceable RTL-to-test-to-feedback workflow, not a reproduction of AssertMiner-pro’s formal assertion-mining method or evidence of superiority on its formal benchmarks.

## 2. Related work and specific difference

AssertMiner-pro extracts structural RTL information and propagates specification context down the module hierarchy to generate and filter fine-grained SystemVerilog assertions, with formal coverage and mutation-based evaluation. Our project instead emphasizes *executable scenario generation, simulation checking, and coverage-guided testing*. The two approaches share AST-guided/LLM-assisted verification ideas but have different primary outputs (assertions versus stimuli), checking methodologies (formal versus dynamic simulation), and coverage denominators. Our current data do not establish superior deep assertion quality or formal coverage over AssertMiner-pro.

## 3. Metric alignment (do not compare unlike quantities)

| Metric | Current project evidence | Honest interpretation |
|---|---|---|
| Initial scenario-category coverage | Hermes 10/10; simple directed 6/10; payload-random 2/10 | Ten predefined functional bins, **not** RTL branch, statement, or toggle coverage. |
| Comparison budget | Ten scenarios per initial strategy; cycle counts differ | Equal scenario count is **not** equal simulation work. |
| Mutation sensitivity | Separate 15-mutant corrected-checker study reports 100% for AI and directed methods | Analogous to an error-detection ratio only when the mutant denominator and checker rules are explicitly defined. Do **not** numerically compare with the paper's EDR on different circuits/fault sets. |
| Structural coverage | No saved Verilator `coverage.dat`/`coverage.info` in the latest project audit | **Not measured in that audit**; do not claim a line/toggle advantage. |
| PPA | Archived hybrid UART block estimates: 5.55% less area, about 1.01% less modeled power than baseline pair | Pre-layout, separately mapped block estimates, not a formal verification gain or a post-layout result. |

## 4. Publication and viva claim boundary

**Use:** “A complementary AST-informed, coverage-guided AI test-generation and simulation-verification workflow, evaluated with archived functional, mutation and pre-layout PPA evidence.”

**Avoid:** “Outperforms AssertMiner-pro,” “achieves 100% RTL/code coverage,” “proves formal correctness,” or “autonomously derived all protocol requirements.” Scenario categories and allowed scenario kinds are constrained by the existing prompt/contract; a balanced-directed control also attains complete defined-bin coverage. An assertion embedded in a simulation testbench does not by itself establish formal-property verification.

**Scope:** Documentation/positioning only. Existing four phases, RTL, testbenches, simulation results, mutation data and PPA evidence remain unchanged.
