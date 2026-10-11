# Phase 4D — UART mutation-based fault-detection evaluation

## Experimental design

- Mutation testing is performed **only in generated copies of optimized UART TX/RX RTL**.
- Original baseline TX/RX are unchanged, serving as the differential reference.
- The same deterministic 10-scenario test suites are used against each mutant.
- Mutation kill requires successful compilation, normal simulation exit, and a self-checking assertion FAIL.
- Compile failures and simulator timeouts are INVALID mutants, **never** counted as kills.
- Each suite has a clean-RTL control that must pass before any mutation experiment runs.
- Results are fault sensitivity to the particular mutation operators and checker; not formal proof of functional correctness.
- Comparing scenario counts does not equalize simulation cycles, human effort or AI inference cost.
- The fixed testbench contains per-cycle baseline/candidate equivalence assertions; this is a strong oracle,
  so both manual and AI scenarios benefit from the **same** oracle. This must be disclosed in the thesis.
- Mutation score counts a mutant as fully killed only if detected at every selected CPB.

CPBs: [8, 16, 32, 64]; mutants: 14; suites: 27

## Mutation score by verification method

| Method | Trials | Mean mutation score | All-mutants-killed trials |
|---|---:|---:|---:|
| balanced_directed | 1 | 92.86% | 0/1 |
| hermes_ai | 5 | 92.86% | 0/5 |
| hermes_archived | 1 | 92.86% | 0/1 |
| payload_random | 10 | 50.71% | 0/10 |
| protocol_random | 10 | 77.14% | 0/10 |

## Interpretation and limitations

Mutation score is a controlled sensitivity metric for the specified artificial defects.
Undetected mutants may be functionally equivalent, outside the test stimulus, or missed by the oracle.
This study does not compare against untested commercial verification tools or establish AI superiority.
All per-mutant differential patches, testbench sources, compile logs and simulation logs are retained.

## Artifacts

- `mutation_matrix.csv`: every suite/CPB/mutant result
- `mutation_summary.json`: machine-readable result and provenance
- `mutants/<ID>/mutation.patch`: exact edit for each mutant
- `clean_controls/`: expected passing simulations
- `mutation_runs/`: independent mutant trials
