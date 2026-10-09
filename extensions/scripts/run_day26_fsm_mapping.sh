#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

OUT="extensions/results/day26/ppa"
LIB="extensions/technology/nangate45/NangateOpenCellLibrary_typical.lib"

BASE="rtl/fsm_1011.v"
MEALY="extensions/rtl/fsm_variants/fsm_mealy_ext.v"
MOORE="extensions/rtl/fsm_variants/fsm_moore_ext.v"

mkdir -p "$OUT"

if ! command -v yosys >/dev/null 2>&1; then
    echo "ERROR: Yosys is unavailable."
    exit 1
fi

for file in "$LIB" "$BASE" "$MEALY" "$MOORE"; do
    if [ ! -s "$file" ]; then
        echo "ERROR: Missing or empty file: $file"
        exit 1
    fi
done

run_mapping() {
    local name="$1"
    local rtl="$2"
    local top="$3"
    local pattern="${4:-}"
    local length="${5:-}"
    local overlap="${6:-}"

    local log="$OUT/${name}_mapping.log"
    local netlist="$OUT/${name}_mapped.v"
    local params=""
    local pattern_decimal

    if [ -n "$pattern" ]; then
        pattern_decimal=$((2#$pattern))

        params="chparam -set LENGTH $length \
-set PATTERN $pattern_decimal \
-set OVERLAP $overlap $top;"
    fi

    echo
    echo "============================================"
    echo "Mapping: $name"
    echo "============================================"

    if yosys -Q -T -l "$log" -p "
        read_verilog -sv $rtl;
        $params
        hierarchy -check -top $top;
        synth -top $top -noabc;
        dfflibmap -liberty $LIB;
        abc -liberty $LIB;
        clean;
        check;
        stat -liberty $LIB;
        write_verilog -noattr -noexpr $netlist;
    " > "$OUT/${name}_console.log" 2>&1; then

        echo "MAPPING: PASS"

        grep -E \
          "Chip area for module|Number of cells:" \
          "$log" | tail -n 6 || true

        echo "Netlist: $netlist"
    else
        echo "MAPPING: FAIL"
        tail -n 35 "$OUT/${name}_console.log"
        return 1
    fi
}

passed=0
failed=0

if run_mapping \
    "fsm_original_1011" \
    "$BASE" \
    "fsm_1011"; then
    passed=$((passed + 1))
else
    failed=$((failed + 1))
fi

for architecture in mealy moore; do

    if [ "$architecture" = "mealy" ]; then
        rtl="$MEALY"
        top="fsm_mealy_ext"
    else
        rtl="$MOORE"
        top="fsm_moore_ext"
    fi

    for config in \
        "1011 4 0" \
        "1011 4 1" \
        "10101 5 0" \
        "10101 5 1" \
        "1101 4 0" \
        "1101 4 1"
    do
        read -r pattern length overlap <<< "$config"

        name="${architecture}_${pattern}_overlap_${overlap}"

        if run_mapping \
            "$name" \
            "$rtl" \
            "$top" \
            "$pattern" \
            "$length" \
            "$overlap"; then

            passed=$((passed + 1))
        else
            failed=$((failed + 1))
        fi
    done
done

echo
echo "============================================"
echo "DAY 26 FSM TECHNOLOGY MAPPING SUMMARY"
echo "============================================"

echo "PASSED CASES: $passed"
echo "FAILED CASES: $failed"

if [ "$passed" -eq 13 ] && [ "$failed" -eq 0 ]; then
    echo "DAY 26 FSM MAPPING: PASS"
else
    echo "DAY 26 FSM MAPPING: FAIL"
    exit 1
fi
