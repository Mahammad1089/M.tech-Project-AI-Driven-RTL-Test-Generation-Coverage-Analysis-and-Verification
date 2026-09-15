#!/bin/bash

echo
echo "======================================"
echo " DAY 1 PROJECT ENVIRONMENT CHECK"
echo "======================================"
echo


echo "[1] Python"
python3 --version


echo
echo "[2] Git"
git --version


echo
echo "[3] Icarus"
iverilog -V 2>&1 | head -n 2


echo
echo "[4] VVP"
vvp -V 2>&1 | head -n 2


echo
echo "[5] Yosys"
yosys -V


echo
echo "[6] Verilator"
verilator --version


echo
echo "[7] GTKWave"
gtkwave --version 2>&1 | head -n 2


echo
echo "[8] Python libraries"

python - <<'PY'

import pyverilog
import jinja2
import pandas
import matplotlib
import requests
import jsonschema

print(
    "Python libraries: PASS"
)

PY


echo
echo "[9] Hermes"

if command -v hermes >/dev/null 2>&1
then

    echo "Hermes: PASS"

else

    echo "Hermes: FAIL"

fi


echo
echo "======================================"
echo " DAY 1 CHECK COMPLETE"
echo "======================================"
