#!/usr/bin/env bash
set -Eeuo pipefail

cd "$HOME/Mtech_project/AI_RTL_Verification"

PPA="extensions/results/day26/ppa"
LIB="extensions/technology/nangate45/NangateOpenCellLibrary_typical.lib"
CLOCK_PERIOD="10.0"
INPUT_DELAY="0.2"
OUTPUT_DELAY="0.2"

mkdir -p "$PPA"

echo "=============================================="
echo " DAY 26 - FSM TECHNOLOGY-MAPPED TIMING ANALYSIS"
echo "=============================================="

if ! command -v sta >/dev/null 2>&1; then
    echo "[FAIL] OpenSTA command 'sta' not found"
    exit 1
fi

if [ ! -s "$LIB" ]; then
    echo "[FAIL] Nangate45 Liberty library missing: $LIB"
    exit 1
fi

shopt -s nullglob
NETLISTS=("$PPA"/*_mapped.v)

if [ "${#NETLISTS[@]}" -ne 13 ]; then
    echo "[FAIL] Expected 13 mapped FSM netlists"
    echo "Found: ${#NETLISTS[@]}"
    exit 1
fi

PASS=0
FAIL=0

for netlist in "${NETLISTS[@]}"; do

    case_name="$(basename "$netlist" _mapped.v)"

    case "$case_name" in
        fsm_original_1011)
            top="fsm_1011"
            ;;
        mealy_*)
            top="fsm_mealy_ext"
            ;;
        moore_*)
            top="fsm_moore_ext"
            ;;
        *)
            echo "[FAIL] Unknown FSM configuration: $case_name"
            FAIL=$((FAIL + 1))
            continue
            ;;
    esac

    tcl="$PPA/${case_name}_sta.tcl"
    log="$PPA/${case_name}_timing.log"

    cat > "$tcl" <<EOF
read_liberty $LIB
read_verilog $netlist
link_design $top

create_clock -name fsm_clk -period $CLOCK_PERIOD [get_ports clk]

set_input_delay $INPUT_DELAY -clock fsm_clk [get_ports din]
set_output_delay $OUTPUT_DELAY -clock fsm_clk [get_ports detected]

# Reset is excluded from ordinary synchronous data-path analysis.
set_false_path -from [get_ports rst]

puts "========== CASE: $case_name =========="
puts "========== MAXIMUM TIMING PATHS =========="
report_checks -path_delay max -group_count 10

puts "========== MINIMUM TIMING PATHS =========="
report_checks -path_delay min -group_count 10

puts "========== TIMING ANALYSIS COMPLETED =========="
EOF

    echo
    echo "Analyzing: $case_name"
    echo "Top module: $top"

    if sta -exit "$tcl" > "$log" 2>&1; then

        if grep -q "TIMING ANALYSIS COMPLETED" "$log" \
           && grep -q "Startpoint:" "$log" \
           && grep -q "Endpoint:" "$log" \
           && ! grep -Eiq '(^Error:|^STA Error:)' "$log"; then

            echo "[PASS] $case_name"
            PASS=$((PASS + 1))

        else
            echo "[FAIL] Incomplete timing report: $case_name"
            tail -n 20 "$log"
            FAIL=$((FAIL + 1))
        fi

    else
        echo "[FAIL] OpenSTA execution: $case_name"
        tail -n 20 "$log"
        FAIL=$((FAIL + 1))
    fi

done

echo
echo "=============================================="
echo " DAY 26 FSM TIMING SUMMARY"
echo "=============================================="
echo "Total configurations : ${#NETLISTS[@]}"
echo "Passed configurations: $PASS"
echo "Failed configurations: $FAIL"

if [ "$PASS" -eq 13 ] && [ "$FAIL" -eq 0 ]; then
    echo "DAY 26 FSM TIMING ANALYSIS: PASS"
else
    echo "DAY 26 FSM TIMING ANALYSIS: FAIL"
    exit 1
fi
