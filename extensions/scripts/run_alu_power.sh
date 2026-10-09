#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

LIB="extensions/technology/nangate45/NangateOpenCellLibrary_typical.lib"
OUT="extensions/results/day25/ppa"
SDC="extensions/scripts/alu_timing.sdc"
TCL="extensions/scripts/alu_power_sta.tcl"

mkdir -p "$OUT"

for file in "$LIB" "$SDC" "$TCL"; do
    if [ ! -s "$file" ]; then
        echo "ERROR: Missing file: $file"
        exit 1
    fi
done

for label in original optimized; do

    if [ "$label" = "original" ]; then
        TOP="alu"
    else
        TOP="alu_opt"
    fi

    NETLIST="$OUT/${label}_mapped.v"
    LOG="$OUT/${label}_power.log"

    if [ ! -s "$NETLIST" ]; then
        echo "ERROR: Missing netlist: $NETLIST"
        exit 1
    fi

    echo "========== POWER ANALYSIS: $label =========="

    if ALU_STA_LIB="$LIB" \
       ALU_STA_NETLIST="$NETLIST" \
       ALU_STA_TOP="$TOP" \
       ALU_STA_SDC="$SDC" \
       timeout 120s sta -no_init -exit "$TCL" \
       </dev/null >"$LOG" 2>&1
    then
        :
    else
        rc=$?
        echo "ERROR: OpenSTA exited with code $rc"
        cat "$LOG"
        exit "$rc"
    fi

    if grep -Eiq '(^|[[:space:]])Error:|unknown command' "$LOG"; then
        echo "ERROR: OpenSTA reported a problem."
        cat "$LOG"
        exit 1
    fi

    if ! grep -q "POWER ANALYSIS COMPLETED" "$LOG"; then
        echo "ERROR: Completion marker not found."
        cat "$LOG"
        exit 1
    fi

    if ! grep -Eq 'Internal|Switching|Leakage' "$LOG"; then
        echo "ERROR: Power results not found."
        cat "$LOG"
        exit 1
    fi

    echo "PASS: $label power analysis completed."
    echo "Report: $LOG"

done

echo "========== BOTH POWER ANALYSES COMPLETED =========="
