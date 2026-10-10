# M.Tech AI-Driven RTL Verification — Phase-Based Review

**Verified technical status: original historical audit 18/18 PASS; new UART AI workflow 12/12 PASS.**

| Phase | Purpose | Outcome |
|---|---|---|
| 1 — RTL | ALU, FIFO, sequence detector and UART baseline/optimized designs | Verified archived RTL and tests |
| 2 — Python knowledge | PyVerilog UART structural extraction | Four UART modules parsed |
| 3 — Hermes AI verification | AI scenario generation, whitelist, Verilog TB, Icarus and coverage | Ten scenarios; 100% of ten defined UART bins across four CPBs |
| 4 — UART research | Verification strategy comparison + historic pre-layout UART optimization | Integrated report PASS; distinct evidence streams |
| Evaluation | Automated acceptance and research/submission checks | 12/12 technical gates PASS; publication/submission tasks pending |

Start with `evaluation/PHASE_REVIEW_SUMMARY.md` and `docs/PHASE_EXECUTION_GUIDE.md`.

**Boundary:** This is simulation-only. AI-generated scenarios do not change the RTL. Historic evidence and path mappings are preserved. The review ZIP is for presentation; a separate evidence ZIP contains traceable new UART simulation artifacts. The original technology library is not redistributed.
