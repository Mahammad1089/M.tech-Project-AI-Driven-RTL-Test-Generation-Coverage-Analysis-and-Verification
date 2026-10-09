# Day 30 RTL Verification and PPA Reproducibility Guide

## Project

AI-Driven RTL Test Generation, Coverage Analysis and Verification

This guide supplements README_DAY30_EXTENSION.md and describes
the archived Days 25-30 simulation-only verification and
technology-mapped PPA experiments.

## Technical Verification Status

The final Day 30 master audit reported 18/18 requirements PASS.

Primary evidence:
extensions/results/day30/master_audit_reconciled_v3/

This result records the original project's completed experiments.
It does not certify independent reproduction on a new computer.

## Environment

Original development environment:
- Ubuntu under Windows Subsystem for Linux
- Python and Verilog RTL
- Icarus Verilog and Verilator
- Yosys synthesis
- OpenSTA timing and estimated-power analysis
- Nangate45 typical standard-cell Liberty library

The repository's requirements.txt lists Python dependencies.
The historical Day 24 tool-version record is located at:
results/final/day24/tool_versions.json

EDA tool versions, environment configuration and library
availability should be checked before reproducing results.

## Technology Library

The PPA experiments use:

extensions/technology/nangate45/NangateOpenCellLibrary_typical.lib

The library is installed in the original local project but
is intentionally excluded from the Git commit.

A user reproducing the PPA analysis must obtain the library
through an authorized source and respect its license terms.

Do not redistribute the Liberty library without reviewing
the applicable redistribution permissions.

## Machine-Specific Absolute Paths

Some archived Tcl and Yosys scripts contain absolute paths
generated for the original WSL project installation.

Step 9C-10 found:
- 97 supplementary files inspected
- 38 files containing absolute-path references
- 136 classified path-reference lines
- 74 project-local path lines
- 0 external-machine path lines in that category

These scripts are preserved without modification as evidence
of the original experimental setup.

They are not guaranteed to execute unchanged on a different
computer or after moving the project directory.

## Relocating the Project

To reproduce an experiment on another computer:

1. Clone the Git repository into a chosen local directory.
2. Install the required Python and EDA tools.
3. Obtain an appropriately licensed Nangate45 Liberty library.
4. Verify the RTL, constraints, mapped netlists and testbench
   paths referenced by the selected experiment.
5. Regenerate the Yosys/OpenSTA scripts using their original
   generating scripts when supported; otherwise create
   working copies with paths adapted to the new environment.
6. Execute the corresponding verification or PPA flow.
7. Compare new reports against the archived baseline results.

Keep the original historical Tcl/Yosys scripts unchanged.
Avoid modifying reported measurements merely to make their
paths or values match a different environment.

## Archived Experimental Scripts

The supplementary repository files include:

- 80 Yosys/OpenSTA synthesis, timing and power scripts
- 15 verification/testbench source files
- 2 package instruction files

The archived Tcl and Yosys scripts are stored in:
extensions/results/day26/
extensions/results/day30/

Primary source code and orchestration scripts are stored in:
extensions/rtl/
extensions/testbench/
extensions/scripts/

Some experiment-specific packages are retained inside their
original results directories.

## Important Limitations

- No FPGA or fabricated hardware is involved.
- Results are based on simulation and technology mapping.
- PPA estimates are pre-layout, not post-route measurements.
- Power values depend on assumed switching activity.
- Timing values depend on clocks, I/O constraints and loads.
- Absolute paths limit out-of-the-box portability.
- The Git commit excludes selected simulation logs,
  temporary executables, backups and the Liberty library.
- Functional simulation evidence is not a formal proof.

## Submission Evidence

The full local project contains additional verification logs
and temporary simulation outputs which are excluded from Git.

Preserve relevant logs in a separate local evidence archive,
subject to licensing and data-sharing requirements.

The completed master technical audit is available under:
extensions/results/day30/master_audit_reconciled_v3/

The university-formatted thesis, literature references and
final submission archive require separate review.
