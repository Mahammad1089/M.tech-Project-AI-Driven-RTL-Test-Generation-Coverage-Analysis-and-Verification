# Final Execution Guide — Four Phases

Use the exact four-phase workflow documented in `FINAL_PHASE_MASTER_WORKFLOW.md`.

Verification order: RTL snapshots → PyVerilog AST → Hermes scenario generation → deterministic validator → Icarus simulation → functional coverage → targeted feedback → UART Novelty evaluation.

Baseline reproduction: `python3 phase_workflow/phase_03_ai_verification/uart_ai_pipeline.py --mode baseline`. Full local audit: `python3 phase_workflow/tools/final_audit.py`. Do not present a clean source-only checkout as an automatic replay of paid Hermes calls or mapped PPA.
