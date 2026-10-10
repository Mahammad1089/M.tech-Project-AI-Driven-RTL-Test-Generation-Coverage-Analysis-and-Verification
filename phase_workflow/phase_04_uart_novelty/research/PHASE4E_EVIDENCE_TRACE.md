# Phase 4E: Verified evidence trace

Evidence status: **PASS**.
This document references existing WSL outputs; it does not rerun verification.

## Source provenance

| Dataset | Project-relative file |
|---|---|
| technical_audit | `evaluation/workflow_status.json` |
| phase3 | `phase_03_ai_verification/results/evaluation_summary.json` |
| phase4c1 | `evaluation/repeatability/phase4c_20261010T102153Z/phase4c_summary.json` |
| phase4c2 | `evaluation/repeatability/hermes_trials/phase4c2_20261010T103303Z/phase4c2_summary.json` |
| phase4d6 | `evaluation/fault_injection/phase4d5_reset_checker_20261010T130112Z/corrected_checker_summary.json` |
| phase4d7 | `evaluation/feedback_closure/phase4d7_20261010T132212Z/experiment_status.json` |

## Validated quantitative findings

- **phase3_initial_AI_coverage_pct:** 100.0
- **phase3_initial_scenarios:** 10
- **phase4c1_payload_random_mean_pct:** 13.0
- **phase4c1_protocol_random_mean_pct:** 69.0
- **phase4c1_balanced_directed_pct:** 100.0
- **phase4c2_fresh_ai_trials:** 5
- **phase4c2_fresh_ai_mean_coverage_pct:** 98.0
- **phase4c2_full_coverage_trials:** 4
- **phase4d6_clean_controls:** 108
- **phase4d6_mutant_simulations:** 1512
- **phase4d6_corrected_mutation_scores:** {'balanced_directed': 100.0, 'hermes_ai': 100.0, 'hermes_archived': 100.0, 'payload_random': 50.71, 'protocol_random': 81.43}
- **phase4d7_initial_coverage_pct:** 90.0
- **phase4d7_feedback_coverage_pct:** 100.0
- **phase4d7_matched_directed_coverage_pct:** 100.0
- **phase4d7_incremental_AI_calls:** 1

## Scientific boundaries

- This audit validates existing project evidence; it does not prove publication novelty.
- A 10-bin functional coverage model is not exhaustive verification.
- 100% mutation score means all 14 selected mutants were killed, not all faults.
- AI and balanced-directed equal 100% on corrected mutation experiment.
- Targeted feedback prompt disclosed the exact bin and loopback(129) remedy.
- UART architecture PPA is an independent pre-layout synthesis result.

## Literature positioning

Literature references and method comparison are in the separately authored
`Phase_4E_Literature_and_Novelty_Report.docx` / `.md`. The literature is not verified by this offline data audit.
