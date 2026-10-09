#!/usr/bin/env bash

# ============================================================
# DAY 25 - ALU STATIC TIMING ANALYSIS RUNNER
# Original ALU vs Optimized ALU
# ============================================================

set -euo pipefail

cd "$(dirname "$0")/../.."

LIB="extensions/technology/nangate45/NangateOpenCellLibrary_typical.lib"
OUT="extensions/results/day25/ppa"
SDC="extensions/scripts/alu_timing.sdc"
TCL="extensions/scripts/alu_sta.tcl"

mkdir -p "$OUT"

echo "=========================================="
echo "ALU OPENSTA VERIFICATION"
echo "=========================================="

# Check OpenSTA installation.

if ! command -v sta >/dev/null 2>&1; then
    echo "ERROR: OpenSTA is not installed."
    exit 1
fi

# Validate input files.

for file in "$LIB" "$SDC" "$TCL"; do
    if [ ! -s "$file" ]; then
        echo "ERROR: Missing or empty file: $file"
        exit 1
    fi
done

# Analyze original and optimized ALU.

for label in original optimized; do

    if [ "$label" = "original" ]; then
        TOP="alu"
    else
        TOP="alu_opt"
    fi

    NETLIST="$OUT/${label}_mapped.v"
    LOG="$OUT/${label}_timing.log"

    echo
    echo "========== ANALYZING $label ALU =========="

    if [ ! -s "$NETLIST" ]; then
        echo "ERROR: Missing mapped netlist: $NETLIST"
        exit 1
    fi

    # Pass configuration through environment variables.
    # Limit execution time to 120 seconds.
    # Redirect standard input to prevent interactive waiting.

    if ALU_STA_LIB="$LIB" \
       ALU_STA_NETLIST="$NETLIST" \
       ALU_STA_TOP="$TOP" \
       ALU_STA_SDC="$SDC" \
       timeout 120s sta -no_init -exit "$TCL" \
       </dev/null >"$LOG" 2>&1
    then
        echo "OpenSTA process exited successfully."
    else
        rc=$?
        echo "ERROR: OpenSTA failed for $label (exit code $rc)"
        cat "$LOG"
        exit "$rc"
    fi

    # Reject logs containing OpenSTA errors.

    if grep -Eiq '(^|[[:space:]])Error:|unknown command' "$LOG"; then
        echo "ERROR: OpenSTA reported errors for $label"
        cat "$LOG"
        exit 1
    fi

    # Verify completion marker.

    if ! grep -q "TIMING CHECK COMPLETE" "$LOG"; then
        echo "ERROR: Missing timing completion marker."
        cat "$LOG"
        exit 1
    fi

    echo "PASS: $label ALU timing commands completed."
    echo "Log: $LOG"

done

echo
echo "=========================================="
echo "OPENSTA EXECUTION COMPLETED"
echo "=========================================="
echo "Original and optimized analyses executed."
echo "Reports saved in: $OUT"
