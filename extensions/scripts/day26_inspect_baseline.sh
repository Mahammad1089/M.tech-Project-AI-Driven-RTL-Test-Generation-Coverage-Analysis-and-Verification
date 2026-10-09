#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")/../.."

OUT="extensions/results/day26"
REPORT="$OUT/day26_baseline_inspection.log"

mkdir -p "$OUT"

{
    echo "=========================================="
    echo " DAY 26 - FSM BASELINE INSPECTION"
    echo "=========================================="
    echo

    echo "========== TOOL VERSIONS =========="

    iverilog -V 2>&1 | head -n 3 || true
    yosys -V
    sta -version 2>&1 || true

    echo
    echo "========== ORIGINAL FSM RTL =========="

    if [[ -f rtl/fsm_1011.v ]]; then

        cp -n \
            rtl/fsm_1011.v \
            extensions/rtl/baseline/fsm_1011_original.v

        echo "Original FSM preserved."

        echo
        echo "Original SHA256:"
        sha256sum rtl/fsm_1011.v

        echo
        echo "Baseline SHA256:"
        sha256sum \
            extensions/rtl/baseline/fsm_1011_original.v

        echo
        echo "========== COMPLETE FSM RTL =========="
        cat rtl/fsm_1011.v

    else
        echo "ERROR: rtl/fsm_1011.v not found."
        exit 1
    fi

    echo
    echo "========== FSM-RELATED FILES =========="

    find rtl testbench coverage results/fsm \
        -maxdepth 4 \
        -type f \
        \( -iname "*fsm*" -o -iname "*day17*" \) \
        -print 2>/dev/null | sort | head -n 100

    echo
    echo "========== FSM MODULE DECLARATIONS =========="

    grep -nE \
        'module |input |output |parameter |localparam |always|case|endmodule' \
        rtl/fsm_1011.v || true

    echo
    echo "========== DAY 17 COVERAGE EVIDENCE =========="

    for file in \
        results/fsm/day17/day17_summary.json \
        results/fsm/day17/fsm_baseline_coverage.json \
        results/fsm/day17/fsm_targeted_sequences.json
    do
        if [[ -f "$file" ]]; then
            echo
            echo "FILE: $file"
            python3 -m json.tool "$file"
        else
            echo "NOT FOUND: $file"
        fi
    done

    echo
    echo "========== FSM RTL COMPILATION =========="

    iverilog -g2012 \
        -s fsm_1011 \
        -o "$OUT/fsm_baseline_compile.out" \
        rtl/fsm_1011.v

    echo "FSM baseline compilation: PASS"

    echo
    echo "========== FSM BASELINE SYNTHESIS =========="

    yosys -Q -T \
        -l "$OUT/fsm_baseline_synthesis.log" \
        -p "read_verilog rtl/fsm_1011.v; hierarchy -check -top fsm_1011; synth -top fsm_1011; check; stat" \
        > "$OUT/fsm_baseline_synthesis_console.log"

    echo "FSM baseline synthesis: PASS"

    echo
    echo "========== BASELINE INSPECTION COMPLETED =========="

} 2>&1 | tee "$REPORT"

echo
echo "Generated report: $REPORT"
