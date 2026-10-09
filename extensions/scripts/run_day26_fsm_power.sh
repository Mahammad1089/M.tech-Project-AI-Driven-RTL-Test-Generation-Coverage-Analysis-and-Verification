#!/usr/bin/env bash
set -Eeuo pipefail

cd "$HOME/Mtech_project/AI_RTL_Verification"

PPA="extensions/results/day26/ppa"
LIB="extensions/technology/nangate45/NangateOpenCellLibrary_typical.lib"

mkdir -p "$PPA"

echo "=============================================="
echo " DAY 26 - FSM POWER ANALYSIS"
echo "=============================================="

if ! command -v sta >/dev/null 2>&1; then
    echo "[FAIL] OpenSTA not installed"
    exit 1
fi

if [ ! -s "$LIB" ]; then
    echo "[FAIL] Nangate45 Liberty library missing"
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

    name="$(basename "$netlist" _mapped.v)"

    case "$name" in
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
            echo "[FAIL] Unknown configuration: $name"
            FAIL=$((FAIL + 1))
            continue
            ;;
    esac

    tcl="$PPA/${name}_power.tcl"
    log="$PPA/${name}_power.log"

    cat > "$tcl" <<EOF
read_liberty $LIB
read_verilog $netlist
link_design $top

create_clock -name fsm_clk -period 10.0 [get_ports clk]

set_input_delay 0.2 -clock fsm_clk [get_ports din]
set_output_delay 0.2 -clock fsm_clk [get_ports detected]

set_false_path -from [get_ports rst]

puts "========== FSM POWER ANALYSIS =========="
puts "Configuration: $name"
puts "Top module: $top"
puts "Activity: 0.1 transitions/ns"
puts "Duty cycle: 0.5"

set_power_activity -global -activity 0.1 -duty 0.5

report_power

puts "========== POWER ANALYSIS COMPLETED =========="
EOF

    echo
    echo "Analyzing: $name"

    if sta -exit "$tcl" > "$log" 2>&1; then
        if grep -q "POWER ANALYSIS COMPLETED" "$log" \
           && grep -Eq '^[[:space:]]*Total[[:space:]]+' "$log" \
           && ! grep -Eq '^Error:' "$log"; then

            echo "[PASS] $name"
            PASS=$((PASS + 1))
        else
            echo "[FAIL] Invalid power report: $name"
            tail -n 20 "$log"
            FAIL=$((FAIL + 1))
        fi
    else
        echo "[FAIL] OpenSTA execution: $name"
        tail -n 20 "$log"
        FAIL=$((FAIL + 1))
    fi

done

echo
echo "=============================================="
echo " DAY 26 FSM POWER SUMMARY"
echo "=============================================="
echo "Total configurations : ${#NETLISTS[@]}"
echo "Passed configurations: $PASS"
echo "Failed configurations: $FAIL"

if [ "$PASS" -eq 13 ] && [ "$FAIL" -eq 0 ]; then
    echo "DAY 26 FSM POWER ANALYSIS: PASS"
else
    echo "DAY 26 FSM POWER ANALYSIS: FAIL"
    exit 1
fi
