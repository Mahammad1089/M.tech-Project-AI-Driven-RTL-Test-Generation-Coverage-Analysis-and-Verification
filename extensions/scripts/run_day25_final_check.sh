#!/usr/bin/env bash
set -uo pipefail

cd "$(dirname "$0")/../.."

OUT="extensions/results/day25"
PPA="$OUT/ppa"
LOG="$OUT/day25_final_verification.log"

mkdir -p "$OUT"

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

pass() {
    echo "[PASS] $1"
    PASS_COUNT=$((PASS_COUNT + 1))
}

fail() {
    echo "[FAIL] $1"
    FAIL_COUNT=$((FAIL_COUNT + 1))
}

warn() {
    echo "[WARN] $1"
    WARN_COUNT=$((WARN_COUNT + 1))
}

check_file() {
    if [[ -s "$1" ]]; then
        pass "File exists: $1"
    else
        fail "Missing or empty file: $1"
    fi
}

run_checks() {

echo "===================================================="
echo " DAY 25 - COMPLETE ALU OPTIMIZATION VERIFICATION"
echo "===================================================="
echo "Date: $(date)"
echo

echo "========== 1. TOOL AVAILABILITY =========="

for tool in python3 iverilog vvp yosys sta; do
    if command -v "$tool" >/dev/null 2>&1; then
        pass "$tool available"
    else
        fail "$tool unavailable"
    fi
done

echo
echo "========== 2. RTL INTEGRITY =========="

check_file "rtl/alu.v"
check_file "extensions/rtl/baseline/alu_original.v"
check_file "extensions/rtl/optimized/alu_opt.v"

if [[ -s rtl/alu.v && -s extensions/rtl/baseline/alu_original.v ]]; then
    if cmp -s \
        rtl/alu.v \
        extensions/rtl/baseline/alu_original.v; then
        pass "Original RTL matches baseline snapshot"
    else
        fail "Original RTL differs from baseline snapshot"
    fi
fi

echo
echo "========== 3. FUNCTIONAL EQUIVALENCE =========="

if [[ -f extensions/scripts/run_alu_equivalence.sh ]]; then

    if bash extensions/scripts/run_alu_equivalence.sh; then
        pass "Equivalence simulation command completed"
    else
        fail "Equivalence simulation command failed"
    fi

else
    fail "Equivalence runner missing"
fi

if [[ -s "$OUT/alu_equivalence.log" ]]; then

    if grep -Eq 'TOTAL CHECKS[[:space:]]*:[[:space:]]*2048' \
        "$OUT/alu_equivalence.log" \
        && grep -Eq 'PASSED CHECKS[[:space:]]*:[[:space:]]*2048' \
        "$OUT/alu_equivalence.log" \
        && grep -Eq 'FAILED CHECKS[[:space:]]*:[[:space:]]*0([[:space:]]|$)' \
        "$OUT/alu_equivalence.log" \
        && grep -Fq 'DAY 25 ALU EQUIVALENCE: PASS' \
        "$OUT/alu_equivalence.log"; then

        pass "2048/2048 functional checks passed"

    else
        fail "Functional equivalence results not valid"
    fi

else
    fail "Equivalence log missing"
fi

echo
echo "========== 4. SYNTHESIS RESULTS =========="

check_file "$OUT/alu_original_synthesis.log"
check_file "$OUT/alu_optimized_synthesis.log"

for name in original optimized; do
    file="$OUT/alu_${name}_synthesis.log"

    if [[ -s "$file" ]]; then
        if grep -q "Number of cells:" "$file"; then
            pass "$name synthesis statistics available"
        else
            fail "$name synthesis statistics missing"
        fi
    fi
done

echo
echo "========== 5. TECHNOLOGY MAPPING =========="

check_file "$PPA/original_mapping.log"
check_file "$PPA/optimized_mapping.log"

check_file "$PPA/original_mapped.v"
check_file "$PPA/optimized_mapped.v"

for name in original optimized; do

    file="$PPA/${name}_mapping.log"

    if [[ -s "$file" ]]; then
        if grep -q "Chip area for module" "$file"; then
            pass "$name standard-cell area available"
        else
            fail "$name standard-cell area missing"
        fi
    fi

done

echo
echo "========== 6. STATIC TIMING ANALYSIS =========="

for name in original optimized; do

    file="$PPA/${name}_timing.log"

    check_file "$file"

    if [[ -s "$file" ]]; then

        if grep -q "Path Type: max" "$file" \
            && grep -q "data arrival time" "$file" \
            && grep -q "slack (" "$file"; then

            pass "$name critical-path timing available"

        else
            fail "$name critical-path timing incomplete"
        fi

    fi

done

echo
echo "========== 7. POWER ANALYSIS =========="

for name in original optimized; do

    file="$PPA/${name}_power.log"

    check_file "$file"

    if [[ -s "$file" ]]; then

        if grep -Eq \
            '^[[:space:]]*Total[[:space:]]+[0-9.eE+-]+' \
            "$file"; then

            pass "$name estimated power report available"

        else
            fail "$name estimated power values missing"
        fi

    fi

done

echo
echo "========== 8. COMPLETE DIAGNOSIS =========="

DIAG="extensions/scripts/generate_day25_diagnosis.py"

if [[ -s "$DIAG" ]]; then

    if python3 -m py_compile "$DIAG"; then
        pass "Diagnosis Python syntax"
    else
        fail "Diagnosis Python syntax"
    fi

    if python3 "$DIAG"; then
        pass "Complete diagnosis generated"
    else
        fail "Complete diagnosis execution"
    fi

else
    fail "Diagnosis script missing"
fi

echo
echo "========== 9. FINAL REPORT VALIDATION =========="

TXT="$OUT/day25_complete_diagnosis.txt"
JSON="$OUT/day25_complete_diagnosis.json"

check_file "$TXT"
check_file "$JSON"

if [[ -s "$JSON" ]]; then

    if python3 -m json.tool "$JSON" >/dev/null 2>&1; then
        pass "JSON report is valid"
    else
        fail "JSON report is invalid"
    fi

    if python3 - "$JSON" <<'PY'
import json
import sys

with open(sys.argv[1]) as f:
    data = json.load(f)

assert data["functional_equivalence"]["status"] == "PASS"
assert data["final_verdict"].startswith("PASS")
assert data["original"]["area_um2"] > data["optimized"]["area_um2"]
assert (
    data["original"]["timing"]["cell_path_delay_ns"]
    >
    data["optimized"]["timing"]["cell_path_delay_ns"]
)
assert (
    data["original"]["power"]["total_w"]
    >
    data["optimized"]["power"]["total_w"]
)
assert data["original"]["timing"]["slack_ns"] >= 0
assert data["optimized"]["timing"]["slack_ns"] >= 0

print("All consolidated PPA assertions passed.")
PY
    then
        pass "Functional, area, timing and power assertions"
    else
        fail "Consolidated PPA assertions"
    fi

fi

echo
echo "========== 10. FINAL PARAMETER SUMMARY =========="

if [[ -s "$TXT" ]]; then

    cat "$TXT"

else
    warn "Diagnosis summary unavailable"
fi

echo
echo "===================================================="
echo " FINAL DAY 25 VERIFICATION STATUS"
echo "===================================================="

echo "Passed checks : $PASS_COUNT"
echo "Failed checks : $FAIL_COUNT"
echo "Warnings      : $WARN_COUNT"

if [[ "$FAIL_COUNT" -eq 0 ]]; then
    echo "FINAL RESULT: PASS"
    return 0
else
    echo "FINAL RESULT: FAIL - REVIEW REQUIRED"
    return 1
fi
}

run_checks 2>&1 | tee "$LOG"
exit "${PIPESTATUS[0]}"
