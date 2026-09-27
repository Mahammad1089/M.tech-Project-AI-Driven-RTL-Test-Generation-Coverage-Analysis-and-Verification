import hashlib
import json
import sys

from pathlib import Path


OUTPUT = Path(
    "results/final/day24/"
    "final_artifact_manifest.json"
)


ARTIFACTS = [

    # RTL
    "rtl/alu.v",
    "rtl/fsm_1011.v",
    "rtl/fifo.v",

    # Integration
    "main.py",
    "run_day23.py",
    "integration_validator.py",
    "validate_project_results.py",
    "day23_summary.py",

    # Major milestone evidence
    "results/alu/day15/day15_summary.json",
    "results/fsm/day17/day17_summary.json",
    "results/fifo/day19/day19_summary.json",
    "results/fifo/day20/day20_summary.json",
    "results/fifo/day21/day21_summary.json",
    "results/fifo/day22/day22_summary.json",

    # Day 23
    "results/integration/day23/"
    "day23_execution_report.json",

    "results/integration/day23/"
    "day23_summary.json",

    # Day 24
    "results/final/day24/"
    "tool_versions.json",

    "results/final/day24/"
    "rtl_sha256.txt"
]


def sha256(path):

    digest = hashlib.sha256()

    with path.open("rb") as file:

        while True:

            block = file.read(
                65536
            )

            if not block:
                break

            digest.update(
                block
            )

    return digest.hexdigest()


def main():

    records = []

    missing = []

    for filename in ARTIFACTS:

        path = Path(
            filename
        )

        if path.exists():

            records.append({

                "path":
                    filename,

                "size_bytes":
                    path.stat().st_size,

                "sha256":
                    sha256(path)
            })

        else:

            missing.append(
                filename
            )

    report = {

        "day": 24,

        "project":
            "AI-Driven RTL Test Generation, "
            "Coverage Analysis and Verification",

        "artifact_count":
            len(records),

        "required_artifact_count":
            len(ARTIFACTS),

        "missing_artifacts":
            missing,

        "artifacts":
            records,

        "status":
            "PASS"
            if not missing
            else "FAIL"
    }

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT.write_text(
        json.dumps(
            report,
            indent=4
        )
    )

    if missing:

        print(
            "DAY 24 ARTIFACT MANIFEST: FAIL"
        )

        print(
            "Missing artifacts:"
        )

        for item in missing:

            print(
                " -",
                item
            )

        sys.exit(1)

    print(
        "DAY 24 ARTIFACT MANIFEST: PASS"
    )

    print(
        "Artifacts recorded:",
        len(records)
    )


if __name__ == "__main__":

    main()
