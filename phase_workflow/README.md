# AI-Driven RTL Verification — Final Four-Phase Project

**Technical verification status:** PASS — 12/12 phase-workflow requirements (local evidence audit).
**Legacy requirements:** PASS — 18/18 (historical evidence).
**Project delivery stage:** local source reproducibility verified; remote publication is a separate action.

## Official development flow

| Phase | Name | Main directory |
|---|---|---|
| 1 | **RTL Design** | `phase_01_rtl/` |
| 2 | **RTL Parsing to Python** | `phase_02_parsing/` |
| 3 | **AI/LLM Verification** | `phase_03_ai_verification/` |
| 4 | **UART Novelty** | `phase_04_uart_novelty/` |

**Start with `docs/FINAL_PHASE_REVIEW_INDEX.md`, then `docs/FINAL_PHASE_MASTER_WORKFLOW.md`.**

- **Phase 4 is UART Novelty.** Research evaluation, functional coverage, fault sensitivity and UART mapped PPA are its evidence—not an additional phase.
- The existing source paths for legacy experiments remain available because several scripts depend on them. Reviewers should use the four phase directories as their primary interface.
- RTL is parsed into Python-readable knowledge JSON; RTL itself is not translated to Python.
- Hermes proposes constrained scenarios. Verilog testbenches and Icarus simulation perform the functional checks.
- Defined UART coverage is 10 bins, not exhaustive RTL correctness. Balanced-directed verification matched Hermes at full coverage and corrected mutation score.
- Local pre-layout area and estimated power results must not be presented as silicon measurements or as improvements caused by AI.
- Third-party Nangate45 files must not be redistributed without appropriate licensing.

## Reproduce local source tests

```bash
python3 -m unittest discover -s phase_workflow/tests -p 'test*.py' -v
python3 phase_workflow/phase_03_ai_verification/uart_ai_pipeline.py --mode baseline
python3 phase_workflow/tools/final_audit.py
```

The complete 12/12 audit requires the local generated evidence. A source-only Git checkout has previously passed 72/72 file integrity, Python syntax, six unit tests and regenerated UART directed/random baselines. Live Hermes and technology-dependent PPA were not replayed in that isolated checkout.
