# Phase 3 — AI/LLM Verification

**Code:** `hermes_bridge.py`, `uart_ai_pipeline.py`, `testbench_generator.py`.

**Explain:** objectives → actual Hermes response → scenario whitelist → generated self-checking RTL benches → Icarus → ten-bin coverage → gap identification and feedback.

**Measured initial suites:** directed 60% (30,116 checks), random 20% (30,116 checks), Hermes 100% (36,408 checks), with 0 failed checks. CPB 8/16/32/64.

**Local output:** `results/evaluation_summary.json`; retain Hermes response separately rather than publishing raw provider logs.
