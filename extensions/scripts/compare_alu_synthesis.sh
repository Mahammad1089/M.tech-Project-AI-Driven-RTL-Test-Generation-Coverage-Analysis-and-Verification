#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")/../.."

OUT="extensions/results/day25"

mkdir -p "$OUT"

echo "======================================"
echo "DAY 25 - ALU SYNTHESIS COMPARISON"
echo "======================================"

echo "Synthesizing original ALU..."

yosys -Q -T -l "$OUT/alu_original_synthesis.log" \
    -p "read_verilog rtl/alu.v; hierarchy -check -top alu; synth -top alu; stat" \
    > "$OUT/alu_original_console.log"

echo "Synthesizing optimized ALU..."

yosys -Q -T -l "$OUT/alu_optimized_synthesis.log" \
    -p "read_verilog extensions/rtl/optimized/alu_opt.v; hierarchy -check -top alu_opt; synth -top alu_opt; stat" \
    > "$OUT/alu_optimized_console.log"

echo
echo "========== ORIGINAL ALU =========="
tail -n 45 "$OUT/alu_original_synthesis.log"

echo
echo "========== OPTIMIZED ALU =========="
tail -n 45 "$OUT/alu_optimized_synthesis.log"

echo
echo "Synthesis completed."
echo "Reports saved in $OUT"
