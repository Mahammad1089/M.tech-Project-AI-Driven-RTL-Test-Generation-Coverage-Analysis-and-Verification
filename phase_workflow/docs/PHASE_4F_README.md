# Phase 4F — Thesis and Review Presentation

Prepared 10 October 2026. This deliverable is a **technical thesis draft**, not an institute-approved final dissertation or published research article.

## Reviewer-facing deliverables

- `MTech_Phase_4F_Research_Thesis_Draft.docx` — editable research thesis draft using four project phases rather than day-wise working steps; includes problem, prior art, flow, experimental methodology, results, scientific limitations, references and evidence paths.
- `MTech_Phase_4F_Review_Presentation.pptx` — editable, 21-slide technical review deck using the same phase-based explanation and controlled comparisons.
- `SHA256SUMS.txt` — hashes for package integrity.

## Claims and results to present accurately

- Historical RTL audit 18/18 PASS; phase-workflow audit 12/12 PASS; Phase 4E evidence audit PASS.
- Fresh Hermes AI: 5 valid trials, 98% mean of **ten defined functional coverage bins**, 4/5 reaching ten-bin closure. The balanced-directed control reached 100% in one suite; AI was **not superior to this strong directed baseline**.
- Corrected 14-mutant UART study: 108 clean controls + 1512 mutant simulations at CPB 8, 16, 32, 64. Fresh Hermes and balanced-directed 100% mutation scores on the **selected fault operators**. The corrected reset oracle contributed to this improvement.
- Measured Hermes feedback: one additional `0x81` loopback scenario closed Trial 5 from 90% (10 scenarios) to 100% (11 scenarios). A matched directed 11-scenario run also closed the gap.
- Pre-layout technology-mapped hybrid UART area 425.600 µm² and estimated power 366.547 µW, relative to baseline 450.604 µm² and 370.282 µW. This is independent of the AI verification contribution.

## Installation principles

Place these review-facing documents under `phase_workflow/docs/` in the user's existing WSL repository. Never delete or rename the original day-wise source/evidence or old final audit. Do not overwrite differing files without review. Never assume there is permission to redistribute a proprietary or third-party `.lib` technology file.

## Submission-readiness checks (Phase 4G)

1. Replace institute-specific placeholders with the university's official title/certificate/approval/declaration format.
2. Verify every number against the Phase 4E audit and latest local JSON evidence; update slides if any later experiment changes a result.
3. Record model/provider identifier, exact prompts, tool versions, RTL hashes, available costs/token use and timing methodology.
4. Test a clean checkout in WSL or an isolated directory with reproducible setup instructions and hash validation; no destructive cleanup.
5. Remove secrets or sensitive information from archives and shell logs; review license terms for `.lib` and third-party assets.
6. Keep the original `results/` and historical day-wise traces as immutable evidence; the `phase_workflow/` view is the presentation layer.
7. Verify slides display correctly in PowerPoint/LibreOffice; validate thesis citations and bibliography using the full papers before journal submission.

## Reproducibility source file locations

- `phase_workflow/evaluation/workflow_status.json`
- `phase_workflow/phase_03_ai_verification/results/evaluation_summary.json`
- `phase_workflow/evaluation/repeatability/phase4c_*/phase4c_summary.json`
- `phase_workflow/evaluation/repeatability/hermes_trials/phase4c2_*/phase4c2_summary.json`
- `phase_workflow/evaluation/fault_injection/phase4d5_reset_checker_*/corrected_checker_summary.json`
- `phase_workflow/evaluation/feedback_closure/phase4d7_*/PHASE4D7_RESEARCH_REPORT.md`
- `phase_workflow/phase_04_uart_novelty/research/PHASE4E_EVIDENCE_AUDIT.json`
