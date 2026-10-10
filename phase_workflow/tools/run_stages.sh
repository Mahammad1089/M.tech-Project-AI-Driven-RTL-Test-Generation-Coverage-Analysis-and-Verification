#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
echo 'PHASE 1: Safe copy of verified RTL/evidence'
python3 phase_workflow/tools/organize.py
python3 phase_workflow/phase_04_uart_novelty/build_architecture_report.py
python3 phase_workflow/evaluation/build_review_summary.py
echo 'DEPENDENCIES:'
bash phase_workflow/tools/check_dependencies.sh
echo 'STATIC UNIT TESTS:'
python3 -m unittest discover -s phase_workflow/tests -v
echo 'PHASE 2 + PHASE 3 PREPARATION (AST knowledge, scenarios, Hermes prompt):'
python3 phase_workflow/phase_03_ai_verification/uart_ai_pipeline.py --mode prepare
echo 'NEXT: simulate baselines with --mode baseline, then run real AI with --mode all'
