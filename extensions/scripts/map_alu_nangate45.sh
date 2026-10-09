#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

LIB="extensions/technology/nangate45/NangateOpenCellLibrary_typical.lib"
OUT="extensions/results/day25/ppa"

mkdir -p "$OUT"

if [ ! -s "$LIB" ]; then
    echo "ERROR: Nangate45 Liberty library missing."
    exit 1
fi

map_design() {
    local label="$1"
    local source="$2"
    local top="$3"

    echo "Mapping $label ALU..."

    yosys -Q -T -l "$OUT/${label}_mapping.log" -p "
        read_liberty -lib $LIB
        read_verilog $source
        hierarchy -check -top $top
        synth -top $top -noabc
        dfflibmap -liberty $LIB
        abc -liberty $LIB
        clean
        check
        stat -liberty $LIB
        write_verilog -noattr -noexpr $OUT/${label}_mapped.v
    " > "$OUT/${label}_console.log"

    test -s "$OUT/${label}_mapped.v"
    echo "$label mapping completed."
}

map_design \
    original \
    rtl/alu.v \
    alu

map_design \
    optimized \
    extensions/rtl/optimized/alu_opt.v \
    alu_opt

echo
echo "========== MAPPING COMPLETE =========="
echo "Mapped netlists and synthesis logs saved in $OUT"
