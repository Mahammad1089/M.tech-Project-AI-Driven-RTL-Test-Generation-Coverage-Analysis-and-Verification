# Final Output Verification — Four-Phase Project

**Audit scope:** actual WSL evidence files, official four-phase presentation, selected outputs, committed source syntax and unit tests.

| Item | Outcome |
|---|---|
| `original_historical_audit_18_of_18` | PASS |
| `integrated_workflow_12_of_12` | PASS |
| `phase_1_four_uart_rtl` | PASS |
| `phase_2_ast_knowledge_available` | PASS |
| `phase_3_three_verification_suites` | PASS |
| `phase_4_architecture_report` | PASS |
| `phase_4_fresh_ai_repeatability_evidence` | PASS |
| `phase_4_corrected_mutation_evidence` | PASS |
| `phase_4_feedback_closure_evidence` | PASS |
| `phase_4_research_evidence_audit` | PASS |
| `thesis_docx_exists` | PASS |
| `review_slides_exist` | PASS |

## UART suite measurements (from local JSON)

| Suite | Simulator checks | Minimum defined-bin coverage | Simulation result |
|---|---:|---:|---|
| directed | 30116 | 60.0% | PASS |
| random | 30116 | 20.0% | PASS |
| ai_initial | 36408 | 100.0% | PASS |

## Further research evidence

- Repeatability: {'passed_trials': 5, 'statistics': {'full_coverage_trials': 4, 'mean': 98.0, 'median': 100.0, 'n': 5, 'range': [90.0, 100.0], 'std_dev_sample': 4.472}}
- Corrected mutation runs: {'clean_controls': 108, 'invalid': 0, 'mutant_simulations': 1512}
- Feedback closure: {'baseline_pct': 90.0, 'ai_pct': 100.0, 'directed_pct': 100.0}
- Reviewed Python syntax: 19 source files, 0 issues
- Python unit tests: PASS

## Source versus experiment reproducibility

- Historical 18/18 and phase 12/12 audits refer to local generated evidence. The clean source checkout previously reproduced parsing and directed/random simulation, but not paid Hermes requests or technology mapping.
- The full experiment files remain local, preserving original paths and hashes. This script does not rerun all raw logs or fabricate fresh results.
- The reviewer-facing phase tree contains no chronologically named files; the private mapping inside `.git/phase_final_review/` tracks historical names.

## Research limitations

- Full coverage is limited to ten explicitly defined UART bins and fourteen selected mutants.
- Balanced-directed methods match the AI maximum result; this is an integrated automation study, not a proof of universal AI superiority.
- External technology-library redistribution permission must be checked independently.


## Local output file inventory (including ignored generated files)

- Files inspected for metadata: 16606
- On-disk size: 345.21 MiB
- File types: {'.md': 9, '.json': 300, '.py': 1, '.log': 7996, '.csv': 14, '.out': 3997, '.v': 4219, '.patch': 56, '.txt': 7, '.png': 6, '.pyc': 1}
- Zero-length examples: []
- Invalid JSON examples (if any): []
- Inventory is not exhaustive behavioral re-simulation of each generated Verilog executable or log.
