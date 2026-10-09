#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")/../.."

OUT="extensions/results/day26"
RTL="extensions/rtl/fsm_variants/fsm_moore_ext.v"
TB="extensions/testbench/tb_fsm_moore_ext.v"

mkdir -p "$OUT"

passed=0
failed=0

for config in \
    "1011 4 0" \
    "1011 4 1" \
    "10101 5 0" \
    "10101 5 1" \
    "1101 4 0" \
    "1101 4 1"
do
    read -r pattern length overlap <<< "$config"

    name="moore_${pattern}_overlap_${overlap}"

    echo
    echo "============================================"
    echo "Testing $name"
    echo "============================================"

    if iverilog -g2012 -Wall \
        -s tb_fsm_moore_ext \
        -Ptb_fsm_moore_ext.LENGTH="$length" \
        -Ptb_fsm_moore_ext.PATTERN="${length}'b${pattern}" \
        -Ptb_fsm_moore_ext.OVERLAP="$overlap" \
        -o "$OUT/${name}.out" \
        "$RTL" "$TB" \
        && vvp "$OUT/${name}.out" \
        > "$OUT/${name}.log" 2>&1 \
        && grep -q \
        "DAY 26 MOORE VERIFICATION: PASS" \
        "$OUT/${name}.log"
    then
        cat "$OUT/${name}.log"
        passed=$((passed + 1))
    else
        echo "FAIL: $name"

        if [ -f "$OUT/${name}.log" ]; then
            cat "$OUT/${name}.log"
        fi

        failed=$((failed + 1))
    fi
done

echo
echo "============================================"
echo "DAY 26 MOORE SUMMARY"
echo "============================================"
echo "PASSED CONFIGURATIONS: $passed"
echo "FAILED CONFIGURATIONS: $failed"

if [ "$passed" -eq 6 ] && [ "$failed" -eq 0 ]; then
    echo "DAY 26 ALL MOORE CONFIGURATIONS: PASS"
else
    echo "DAY 26 ALL MOORE CONFIGURATIONS: FAIL"
    exit 1
fi
