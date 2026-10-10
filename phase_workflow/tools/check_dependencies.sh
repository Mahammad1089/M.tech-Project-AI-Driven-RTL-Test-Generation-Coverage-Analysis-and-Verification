#!/usr/bin/env bash
set -u
printf '\n=== PHASE WORKFLOW TOOL CHECK ===\n'
for tool in python3 iverilog vvp git hermes yosys sta; do
 if command -v "$tool" >/dev/null 2>&1; then
   printf '[FOUND] %s = %s\n' "$tool" "$(command -v "$tool")"
 else
   printf '[MISSING/OPTIONAL] %s\n' "$tool"
 fi
done
python3 - <<'PY'
try:
 import pyverilog
 print('[FOUND] PyVerilog',getattr(pyverilog,'__version__','version not advertised'))
except ImportError:
 print('[MISSING] PyVerilog: install in active WSL Python environment')
PY
printf '\nSimulation stages require Icarus Verilog; AI stage requires working Hermes.\n'
