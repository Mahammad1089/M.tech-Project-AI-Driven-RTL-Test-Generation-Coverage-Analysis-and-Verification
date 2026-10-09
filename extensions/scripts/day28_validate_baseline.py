#!/usr/bin/env python3

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("extensions/results")
DAY26 = ROOT / "day26"
DAY27 = ROOT / "day27"
DAY28 = ROOT / "day28"

DAY28.mkdir(parents=True, exist_ok=True)

checks = []
artifacts = {}

def record(label, success, details=""):
    result = {
        "check": label,
        "passed": bool(success),
        "details": details,
    }
    checks.append(result)

    status = "PASS" if success else "FAIL"
    print(f"[{status}] {label}")

    if details:
        print(f"       {details}")

def sha256(path):
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)

    return digest.hexdigest()

def validate_file(path):
    exists = path.is_file() and path.stat().st_size > 0

    record(f"Required file: {path}", exists)

    if exists:
        artifacts[str(path)] = {
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
        }

    return exists

print("=" * 70)
print("DAY 28 - STEP 1: BASELINE VALIDATION")
print("=" * 70)

day26_csv = DAY26 / "day26_fsm_ppa_comparison.csv"

# Locate the actual Day 26 consolidated CSV rather than
# assuming its filename.
day26_candidates = sorted(DAY26.glob("*.csv"))

record(
    "Day 26 CSV evidence available",
    bool(day26_candidates),
    f"Found {len(day26_candidates)} CSV file(s)",
)

day27_files = [
    DAY27 / "day27_mealy_moore_comparison.csv",
    DAY27 / "day27_mealy_moore_comparison.json",
    DAY27 / "day27_efficiency_metrics.csv",
    DAY27 / "day27_efficiency_metrics.json",
    DAY27 / "day27_pareto_analysis.csv",
    DAY27 / "day27_pareto_analysis.json",
    DAY27 / "day27_graph_summary.json",
]

for path in day27_files:
    validate_file(path)

efficiency_path = DAY27 / "day27_efficiency_metrics.csv"
efficiency_rows = []

if efficiency_path.is_file():
    try:
        with efficiency_path.open(
            newline="", encoding="utf-8"
        ) as handle:
            reader = csv.DictReader(handle)
            efficiency_rows = list(reader)
            columns = reader.fieldnames or []

        record(
            "13 FSM efficiency records",
            len(efficiency_rows) == 13,
            f"Actual records: {len(efficiency_rows)}",
        )

        record(
            "Configuration column available",
            "configuration" in columns,
        )

        if "configuration" in columns:
            names = [
                row["configuration"]
                for row in efficiency_rows
            ]

            record(
                "Configuration names are unique",
                len(names) == len(set(names)),
            )

    except (OSError, csv.Error, UnicodeError) as exc:
        record("Efficiency CSV readable", False, str(exc))

graph_dir = DAY27 / "graphs"
graphs = sorted(graph_dir.glob("*.png"))

record(
    "Six Day 27 graphs available",
    len(graphs) == 6,
    f"Actual graphs: {len(graphs)}",
)

for graph in graphs:
    validate_file(graph)

for path in day27_files:
    if path.suffix != ".json" or not path.is_file():
        continue

    try:
        with path.open(encoding="utf-8") as handle:
            json.load(handle)

        record(f"Valid JSON: {path.name}", True)

    except (OSError, ValueError) as exc:
        record(f"Valid JSON: {path.name}", False, str(exc))

passed = sum(item["passed"] for item in checks)
failed = len(checks) - passed

report = {
    "day": 28,
    "step": 1,
    "timestamp_utc": datetime.now(
        timezone.utc
    ).isoformat(),
    "source_day": [26, 27],
    "configuration_count": len(efficiency_rows),
    "checks_passed": passed,
    "checks_failed": failed,
    "status": "PASS" if failed == 0 else "FAIL",
    "checks": checks,
    "artifacts": artifacts,
}

output = DAY28 / "day28_baseline_validation.json"

output.write_text(
    json.dumps(report, indent=2) + "\n",
    encoding="utf-8",
)

print()
print("=" * 70)
print("DAY 28 - STEP 1 SUMMARY")
print("=" * 70)
print(f"Passed checks : {passed}")
print(f"Failed checks : {failed}")
print(f"Configurations: {len(efficiency_rows)}")
print(f"Report        : {output}")
print(f"FINAL STATUS  : {report['status']}")

sys.exit(0 if failed == 0 else 1)
