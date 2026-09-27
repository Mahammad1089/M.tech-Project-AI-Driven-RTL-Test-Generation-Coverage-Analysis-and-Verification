# AI-Driven RTL Test Generation, Coverage Analysis and Verification

## Project Overview

This M.Tech project implements a simulation-only RTL verification
framework using Verilog, Python, open-source EDA tools and Hermes-assisted
structured test reasoning.

The framework integrates RTL analysis, structured verification-objective
generation, AI-assisted test-scenario generation, deterministic scenario
validation, automatic Verilog testbench generation, simulation, functional
coverage analysis, coverage-gap identification and targeted coverage closure.

## Benchmarks

The framework is evaluated using:

1. 4-bit ALU
2. Overlapping 1011 sequence detector FSM
3. 4-entry x 8-bit synchronous FIFO

## Main Verification Flow

Verilog RTL
→ RTL structural analysis
→ RTL knowledge model
→ verification objectives
→ Hermes structured scenarios
→ deterministic validation
→ Verilog testbench generation
→ simulation
→ functional coverage
→ gap analysis
→ targeted verification
→ coverage closure

## Experimental Evaluation

The FIFO phase additionally compares:

- manual/directed verification
- deterministic random verification
- feedback-driven verification

Random verification is evaluated over multiple fixed seeds to study
run-to-run variation.

## Main Tools

- Verilog
- Python
- Icarus Verilog
- VVP
- Yosys
- Verilator
- GTKWave
- PyVerilog
- Hermes Agent
- Matplotlib

Exact environment versions are recorded in:

results/final/day24/tool_versions.json

## One-Command Integration Validation

Run:

python main.py

## Final Freeze Validation

Run:

python docs/final/run_day24.py

## Important Result Directories

- results/alu/
- results/fsm/
- results/fifo/
- results/integration/day23/
- results/final/day24/
- graphs/day22/

## Project Boundaries

The project is simulation-only.

No FPGA or physical hardware implementation is required.

Day 24 does not modify RTL, generate new tests, change the coverage
model or fabricate experimental measurements.

## Final Status

The final status must be taken from:

results/final/day24/final_project_summary.json

A project should be treated as successfully frozen only when
docs/final/validate_final_project.py reports PASS.
