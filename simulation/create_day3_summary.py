import json
from pathlib import Path


log_path = Path(
    "results/alu/day3/"
    "python_simulation.log"
)

text = log_path.read_text()


status = (
    "PASS"
    if "FAILED TESTS = 0" in text
    else "FAIL"
)


result = {
    "day": 3,
    "dut": "alu",
    "rtl_language": "Verilog",
    "verification_type": "directed_self_checking",
    "status": status
}


output = Path(
    "results/alu/day3/"
    "day3_summary.json"
)


output.write_text(
    json.dumps(
        result,
        indent=4
    )
)


print(
    json.dumps(
        result,
        indent=4
    )
)
