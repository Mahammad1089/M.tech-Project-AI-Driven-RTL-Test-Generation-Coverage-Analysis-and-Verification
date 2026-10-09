#!/usr/bin/env bash
set -Eeuo pipefail
cd "$HOME/Mtech_project/AI_RTL_Verification"
mkdir -p extensions/results/day30/fifo_equivalence
for CONFIG in '8 4 2' '8 8 3' '16 4 2' '8 16 4'; do
  read -r WIDTH DEPTH ADDR <<< "$CONFIG"
  LABEL="w${WIDTH}_d${DEPTH}"
  OUT="extensions/results/day30/fifo_equivalence/${LABEL}.out"
  LOG="extensions/results/day30/fifo_equivalence/${LABEL}.log"
  echo "========== FIFO EQUIVALENCE ${LABEL} =========="
  iverilog -g2012 -s tb_day30_fifo_equivalence \
    -P "tb_day30_fifo_equivalence.DATA_WIDTH=${WIDTH}" \
    -P "tb_day30_fifo_equivalence.DEPTH=${DEPTH}" \
    -P "tb_day30_fifo_equivalence.ADDR_WIDTH=${ADDR}" \
    -P "tb_day30_fifo_equivalence.RANDOM_CYCLES=5000" \
    -o "$OUT" \
    rtl/fifo.v extensions/rtl/optimized/fifo_opt.v \
    extensions/testbench/tb_day30_fifo_equivalence.v
  vvp "$OUT" | tee "$LOG"
  grep -q '^FAILED CHECKS: 0$' "$LOG"
  grep -q '^DAY 30 FIFO EQUIVALENCE: PASS$' "$LOG"
done
echo 'DAY 30 FIFO FOUR-CONFIGURATION EQUIVALENCE: PASS'
