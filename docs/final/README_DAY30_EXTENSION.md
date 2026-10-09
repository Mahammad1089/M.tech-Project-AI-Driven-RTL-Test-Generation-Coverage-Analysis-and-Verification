# AI-Driven RTL Test Generation, Coverage Analysis and Verification

## M.Tech Major Project — Day 30 Extension Documentation

### 1. Project Overview

This project develops a simulation-only RTL verification
framework using Verilog, Python, open-source EDA tools,
and Hermes-assisted structured verification.

The framework integrates:

- RTL knowledge extraction
- Verification objective generation
- AI-assisted test scenario generation
- Deterministic scenario validation
- Automated testbench generation
- RTL simulation
- Functional coverage analysis
- Coverage-gap identification
- Feedback-driven coverage closure

The Day 25–30 extension adds optimized RTL architectures,
functional equivalence verification, parameterized
verification, technology-mapped PPA comparison and
architectural trade-off analysis.

No FPGA or physical hardware implementation is required.

### 2. Project Development Phases

#### Phase 1: Days 1–24

Baseline verification framework development covering:

- 4-bit ALU
- 1011 overlapping sequence detector FSM
- 8-bit, 4-entry synchronous FIFO

The original final documentation is preserved in:

docs/final/README_FINAL.md

#### Phase 2: Days 25–30

Extended verification and architectural analysis covering:

- Optimized 4-bit ALU
- Optimized synchronous FIFO
- Parameterized Mealy and Moore FSMs
- UART transmitter and receiver
- Technology-mapped area, timing and power evaluation
- Independent coverage verification
- Final integrated master requirements audit

### 3. Verified Design Under Tests

#### 3.1 Arithmetic Logic Unit

The ALU performs eight operations:

1. Addition
2. Subtraction
3. Bitwise AND
4. Bitwise OR
5. Bitwise XOR
6. Bitwise NOT
7. Left shift
8. Right shift

The optimized implementation shares arithmetic hardware
between addition and subtraction.

Functional equivalence:
2048 / 2048 comparisons passed.

Nangate45 PPA at 5 fF output loading:

Original:
- Mapped area: 68.096 um^2
- Setup slack: 9.270 ns
- Estimated power: 7.240 uW

Optimized:
- Mapped area: 59.052 um^2
- Setup slack: 9.320 ns
- Estimated power: 6.170 uW

Measured improvements under this model:
- Cell area reduction: 13.28%
- Estimated power reduction: 14.78%
- Setup slack improvement: 50 ps

These are pre-layout technology-mapped estimates.

#### 3.2 Synchronous FIFO

The baseline FIFO is an 8-bit, 4-entry synchronous FIFO.

The optimized implementation removes reset operations
from the storage array while preserving the externally
observable reset and FIFO behavior.

Evaluated configurations:

- 8-bit width, depth 4
- 8-bit width, depth 8
- 16-bit width, depth 4
- 8-bit width, depth 16

Functional equivalence:
124008 / 124008 checks passed.

The optimized FIFO reduced mapped cell area across all
four evaluated configurations.

Estimated power improvements varied by configuration;
an improvement is not claimed universally.

#### 3.3 Finite State Machines

The FSM extension covers five binary patterns:

- 1011
- 1101
- 1001
- 10101
- 1110

Each pattern supports:

- Mealy overlapping
- Mealy non-overlapping
- Moore overlapping
- Moore non-overlapping

Total functional configurations:
20 / 20 passed.

Independent functional verification:
147844 / 147844 checks passed.

Functional coverage includes positive sequence detections,
non-detection behavior, reset handling, and overlapping
versus non-overlapping behavior.

Technology-mapped PPA:
20 / 20 configurations completed.

Matched Mealy/Moore architectural comparisons:
10 / 10 pairs.

Pareto analysis:
- 20 evaluated configurations
- 2 exploratory global Pareto variants
- 14 controlled Pareto variants

Global Pareto results compare different functional
requirements and are exploratory only.

#### 3.4 UART Transmitter and Receiver

The UART extension includes:

- Baseline UART transmitter
- Baseline UART receiver
- Optimized UART transmitter
- Optimized UART receiver

Protocol:
8 data bits, no parity, one stop bit.

Evaluated clock-per-bit configurations:
8, 16, 32 and 64.

Verification includes:

- Baseline TX/RX loopback
- Optimized TX/RX equivalence
- Optimized TX/RX loopback
- Hybrid baseline TX plus optimized RX loopback

The hybrid architecture provided the best combined
mapped area and estimated-power results among the
three evaluated architectures at CPB=16.

This conclusion applies to the specified pre-layout
mapping and activity assumptions.

### 4. Main Verification Architecture

RTL Design
    |
    v
RTL Structural Analysis
    |
    v
Knowledge Extraction
    |
    v
Verification Objective Generation
    |
    v
Hermes-Assisted Scenario Generation
    |
    v
Deterministic Validation
    |
    v
Verilog Testbench Generation
    |
    v
Icarus Verilog / Verilator Simulation
    |
    v
Functional Coverage Analysis
    |
    v
Coverage-Gap Identification
    |
    v
Targeted Test Generation
    |
    v
Coverage Closure
    |
    v
Functional Equivalence Verification
    |
    v
Yosys Technology Mapping
    |
    v
OpenSTA Timing and Power Evaluation
    |
    v
Architectural Comparison and Reporting

The baseline and extension stages were developed
incrementally; not every stage was executed identically
for every DUT.

### 5. Tools and Technologies

- Verilog HDL
- Python
- Hermes Agent
- PyVerilog
- Icarus Verilog
- VVP
- Verilator
- Yosys
- OpenSTA
- Nangate45 typical Liberty library
- Matplotlib
- Pandas
- GTKWave
- Ubuntu / WSL

### 6. Verification and PPA Methodology

Functional verification uses directed, randomized,
parameterized and reference-model-based approaches,
as appropriate to each DUT.

PPA results are based on Nangate45 technology-mapped
netlists.

Timing uses specified virtual or real clock constraints
depending on the circuit architecture.

Power results use assumed switching activity.

No placed-and-routed timing, extracted parasitics,
fabricated silicon or physical power measurements
are claimed.

### 7. Final Evidence Locations

ALU:
extensions/results/day30/alu_final_report/
extensions/results/day30/alu_5ff_sensitivity/

FIFO:
extensions/results/day30/fifo_final_report/

FSM functional verification:
extensions/results/day30/fsm_20_matrix/
extensions/results/day30/fsm_independent_coverage/

FSM PPA:
extensions/results/day30/fsm_ppa_extension/

FSM architectural comparison:
extensions/results/day30/fsm_comparison_extended/

UART:
extensions/results/day30/uart/final_report/

Final integrated master audit:
extensions/results/day30/master_audit_reconciled_v3/

### 8. Final Technical Audit

The Day 30 master audit evaluated 18 technical
requirements covering ALU, FIFO, FSM, UART,
verification and PPA reporting.

Final result:

PASS_18_OF_18_REQUIREMENTS

All 18 requirements received PASS status.

No unresolved technical requirement was reported
by the final master audit.

### 9. Research Contributions

The implemented extension demonstrates:

- AI-assisted RTL verification workflow integration
- Coverage-guided targeted verification
- Exhaustive functional equivalence for the 4-bit ALU
- Multi-configuration FIFO equivalence analysis
- Twenty-configuration parameterized FSM verification
- Independent FSM functional coverage verification
- Matched Mealy/Moore architecture comparisons
- Pareto-based PPA trade-off analysis
- UART architecture optimization comparisons

These are implemented project contributions;
publication novelty requires a separate literature review.

### 10. Important Limitations

- Simulation-only project
- No FPGA implementation
- No fabricated hardware
- No post-route physical implementation
- Power based on assumed activity
- Timing depends on specified constraints
- Functional simulation is not formal proof
- Cross-pattern Pareto comparisons are exploratory

### 11. Reproducibility

Historical Day 24 workflow:

python main.py
python docs/final/run_day24.py

Day 30 verification and reporting scripts are
located in:

extensions/scripts/

Technical audit source:

extensions/scripts/reconcile_day30_master_audit_v3.py

Existing reports must be checked against their
referenced files and logs before claiming that
a new installation reproduces the results.

### 12. Submission Status

Technical master requirements:
18 / 18 PASS.

Thesis document:
Requires separate preparation and institutional review.

Repository:
Requires final source-control and evidence-archive review.

Research publications:
References and related work require verification.

### 13. Conclusion

The project demonstrates a simulation-only
AI-assisted RTL verification framework extended
with functional equivalence verification and
technology-mapped architectural analysis.

The evaluated ALU, FIFO, FSM and UART configurations
passed their reported verification requirements.

The final technical master audit passed all
18 specified requirements.

Thesis submission readiness remains subject
to documentation, references, reproducibility
and institutional formatting review.

### Nangate45 Library Reproducibility

Technology-mapped PPA experiments use the Nangate45
typical Liberty library.

Expected local path:

extensions/technology/nangate45/NangateOpenCellLibrary_typical.lib

This library is installed in the original WSL
development environment but is not included in
the Git repository.

Users reproducing the PPA experiments must obtain
an appropriately licensed copy and configure
the path expected by the PPA scripts.

Redistribution permissions must be verified before
including third-party technology libraries in
public repositories or submission archives.

Reported area, timing and power results are
pre-layout technology-mapped estimates.

Results depend on tool versions, technology libraries,
timing constraints, output loads and assumed
switching activity.

Simulation logs and temporary executables may be
excluded from Git and should be preserved separately
as verification evidence.
