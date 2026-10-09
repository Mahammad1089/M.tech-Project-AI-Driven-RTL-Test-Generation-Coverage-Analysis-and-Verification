#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")/../.."

OUT="extensions/results/day26"
RTL="extensions/rtl/fsm_variants/fsm_mealy_ext.v"
TB="extensions/testbench/tb_fsm_mealy_ext.v"

mkdir -p "$OUT"

for pattern in 1011 1101 10101; do

    length=${#pattern}

    for overlap in 0 1; do

        name="mealy_${pattern}_overlap_${overlap}"

        echo
        echo "=========================================="
        echo "Testing $name"
        echo "=========================================="

        iverilog -g2012 \
            -s tb_fsm_mealy_ext \
            -Ptb_fsm_mealy_ext.LENGTH="$length" \
            -Ptb_fsm_mealy_ext.PATTERN="${length}'b${pattern}" \
            -Ptb_fsm_mealy_ext.OVERLAP="$overlap" \
            -o "$OUT/${name}.out" \
            "$RTL" "$TB"

        vvp "$OUT/${name}.out" \
            | tee "$OUT/${name}.log"

        grep -q \
            "DAY 26 MEALY VERIFICATION: PASS" \
            "$OUT/${name}.log"

    done

done

echo
echo "=========================================="
echo "DAY 26 ALL MEALY CONFIGURATIONS: PASS"
echo "=========================================="
