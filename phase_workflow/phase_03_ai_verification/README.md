# Phase 3 — AI/LLM-Driven UART Verification

Run `uart_ai_pipeline.py --mode prepare`, `--mode baseline`, then `--mode all`. Objective generation, Hermes response validation, deterministic testbench generation, Icarus simulation, TX/RX equivalence checks, functional bins, targeted feedback and comparisons are separated and auditable. AI prompts never become executable source code. All new results require actual simulations; the script never claims a PASS in their absence.
