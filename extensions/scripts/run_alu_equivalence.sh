#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")/../.."

mkdir -p extensions/results/day25

echo "======================================"
echo "DAY 25 - ALU EQUIVALENCE"
echo "======================================"

iverilog -g2012 \
    -s tb_alu_equivalence \
    -o extensions/results/day25/alu_equivalence.out \
    rtl/alu.v \
    extensions/rtl/optimized/alu_opt.v \
    extensions/testbench/tb_alu_equivalence.v

vvp extensions/results/day25/alu_equivalence.out \
    | tee extensions/results/day25/alu_equivalence.log

grep -q \
    "DAY 25 ALU EQUIVALENCE: PASS" \
    extensions/results/day25/alu_equivalence.log

echo "Simulation and PASS marker verified."
