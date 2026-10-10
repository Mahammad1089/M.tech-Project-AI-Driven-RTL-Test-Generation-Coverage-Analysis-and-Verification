# Phase 4 — UART Novelty

**Objective:** demonstrate the UART-specific contribution using structured RTL knowledge, real AI-generated tests and measurable fault sensitivity alongside independent UART architecture comparisons.

**Evidence:** five fresh Hermes trials (98% mean coverage), stronger protocol-aware random and balanced-directed baselines, 14-mutant study with corrected reset oracle (100% AI and balanced-directed), targeted one-call `edge_81` feedback (90% to 100%, matched directed also 100%), plus archived baseline/optimized/hybrid pre-layout PPA.

**Main files:** `UART_INTEGRATED_RESEARCH_REPORT.md`, `UART_ARCHITECTURE_RESULTS.md`, `research/PHASE4E_EVIDENCE_TRACE.md`. Additional experiment outputs are in `../evaluation/`.

**Limits:** AI did not outperform the balanced-directed method at maximum measured coverage or mutation score. Pre-layout hardware area/power improvements cannot be attributed to Hermes.
