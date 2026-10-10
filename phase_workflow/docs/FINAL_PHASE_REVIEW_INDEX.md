# Final M.Tech Review — Phase-Based File Index

## Start here

1. `FINAL_PHASE_MASTER_WORKFLOW.md` — full architecture-to-research execution sequence.
2. `FINAL_PHASE_FILE_CHECK_REPORT.md` — required file, status and integrity checklist.
3. `FINAL_PHASE_REVIEW_INDEX.md` — this index.
4. `FINAL_OUTPUT_VALIDATION.md` — audit findings and limitations.
5. `MTech_Final_Phase_Thesis_Draft.docx` — final phase-labelled editable thesis draft.
6. `MTech_Final_Phase_Master_Workflow_Guide.docx` — final phase guide.
7. `MTech_Final_Phase_Review_Presentation.pptx` — final phase-labelled presentation.

## Phase 1 — RTL Design

`phase_workflow/phase_01_rtl/benchmarks/` and `phase_workflow/phase_01_rtl/uart/` contain functional and optimized RTL examples. Explain purpose, interfaces, reset behavior, FSM structure and architecture changes.

## Phase 2 — RTL Parsing to Python

`phase_workflow/phase_02_parsing/extract_uart.py` performs AST extraction. The generated `results/uart_knowledge.json` is local experiment evidence and is not necessarily available in a fresh source-only checkout.

## Phase 3 — AI/LLM Verification

`phase_workflow/phase_03_ai_verification/` contains the interface, scenario validator, testbench generator and orchestration. Coverage data and raw Hermes responses are in local evidence directories, not in the minimal source review ZIP.

## Phase 4 — UART Novelty

`phase_workflow/phase_04_uart_novelty/`, `phase_workflow/evaluation/`, and `phase_workflow/docs/` contain architecture/PPA comparisons, experimental scripts, summaries, literature and presentation drafts.

## Live reviewer demonstration (safe sequence)

```bash
cd ~/Mtech_project/AI_RTL_Verification
python3 -m unittest discover -s phase_workflow/tests -v
python3 phase_workflow/phase_03_ai_verification/uart_ai_pipeline.py --mode baseline
python3 phase_workflow/tools/final_audit.py
```

The baseline command reruns deterministic UART simulations locally. The audit will only pass in an environment with the already generated evidence. For fresh Hermes runs and PPA work, provide the configured models, simulator tooling and a legitimately obtained technology library.

## Data provenance

The original experiment/source tree is preserved separately. The private file map in `.git/phase_final_review/` records how chronological files correspond to the four phases without putting those legacy names into the reviewer-facing documents.
