DAY 30 FSM independent coverage suite.

Files:
- tb_day30_fsm_independent_coverage.v -> extensions/testbench/
- run_day30_fsm_independent_coverage.py -> extensions/scripts/

Execute from project root:
python3 extensions/scripts/run_day30_fsm_independent_coverage.py

The suite checks four variants per pattern, five patterns total.
For each bit, it checks Mealy before posedge and Moore after posedge.
The reference uses sliding stream history and a non-overlap end index.
No existing RTL, results, or logs are changed.
Note: Icarus Verilog execution must be performed on user's WSL machine.
