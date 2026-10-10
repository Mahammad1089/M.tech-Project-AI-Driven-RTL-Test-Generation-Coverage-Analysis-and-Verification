# Research Evidence, Claimed Contribution and Remaining Work

## Completed and measured

The original project verified ALU, FIFO, FSM and UART design families; its historical master audit is **18/18 PASS**. The additional phase-based UART experiment is now **12/12 PASS** and includes genuine PyVerilog parsing, live Hermes scenario generation, deterministic scenario validation, Icarus testbenches, observed functional coverage, and an integrated report.

At an equal initial **ten scenarios per strategy**, coverage across the defined ten UART bins was **60% directed, 20% deterministic random, and 100% Hermes AI**. The initial AI suite passed **36,408 checks** across CLKS_PER_BIT 8/16/32/64 with no failed checks. The missing-bin set was empty, so additional AI feedback trials were **not required**.

Original archived hybrid UART pre-layout mapping reduced combined area from 450.604 to 425.600 µm² and assumed-activity estimated power from 370.282 to 366.547 µW. These are architecture results and **not caused by Hermes**.

## Remaining research and submission validation

- Re-run random tests with multiple independent seeds, preserving a clearly specified scenario budget, and report mean, dispersion, and worst/best coverage.
- Repeat Hermes scenario generation with documented model/provider and multiple independent requests if feasible; compare variation and runtime/cost.
- Analyze independent coverage strength and negative tests; ten scenario bins are not complete UART protocol proof.
- Verify precise novelty and distinctions through a dated IEEE/Springer/Elsevier related-work table.
- Complete thesis/review document revision, including figures, reproducibility instructions and limitations.
- Conduct a clean WSL reproduction and validate checksums of final evidence ZIP. Do not include licensed standard-cell library, credential files or old machine-specific private data.

## Reviewer-friendly organization

Only phase names are used in review-facing paths. Original experiment/source paths are retained separately for transparent provenance; no mass-renaming or deletion is applied to validated historical evidence.
