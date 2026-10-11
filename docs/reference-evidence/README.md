# Project reference evidence

This repository includes review summaries and selected reproducibility evidence for the
AI-Driven RTL Test Generation, Coverage Analysis and Verification project.

## Where to look

- `phase_workflow/evaluation/REVIEW_READINESS.json`: recorded review readiness.
- `phase_workflow/evaluation/verification_summary.json`: recorded verification summary.
- `phase_validation_results.txt`: source inventory and static Python validation.
- `phase_actual_evidence.zip`: selected UART simulation JSON results and logs.
- `phase_review_package.zip`: phase source-code and validation report snapshot.
- `phase_workflow/evaluation/{fault_injection,repeatability,feedback_closure}/`:
  selected small audit/summary files, where available.

## Data retained locally (not uploaded by this script)

Large fault-injection run directories, complete generated testbench and log copies,
backup files, full extracted source reports, and the Nangate technology library
remain in WSL. They are intentionally excluded to avoid repository bloat or
unreviewed licensing/privacy issues.

The uploaded materials are selected evidence records, not a replacement for
rerunning the full verification workflow.
