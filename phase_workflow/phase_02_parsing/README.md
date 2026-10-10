# Phase 2 — RTL Parsing into Python-Readable Knowledge

Run `python3 phase_workflow/phase_02_parsing/extract_uart.py`. It uses the PyVerilog AST, validates four module names, ports, clocked state machines and UART parameter contracts, then writes a structured JSON knowledge model. No Verilog-to-Python executable translation or AI invocation happens in this phase.
