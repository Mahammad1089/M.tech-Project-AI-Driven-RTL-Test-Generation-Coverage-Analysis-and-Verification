import json
from pathlib import Path


STRUCTURE_FILE = Path(
    "results/alu/day5/"
    "alu_structure.json"
)

OUTPUT_FILE = Path(
    "results/alu/day5/"
    "day5_summary.json"
)


def main():

    if not STRUCTURE_FILE.exists():

        print(
            "DAY 5 SUMMARY: FAIL"
        )

        print(
            "alu_structure.json not found."
        )

        raise SystemExit(1)


    structure = json.loads(
        STRUCTURE_FILE.read_text()
    )


    modules = structure.get(
        "modules",
        []
    )


    if not modules:

        print(
            "DAY 5 SUMMARY: FAIL"
        )

        print(
            "No modules extracted."
        )

        raise SystemExit(1)


    module = modules[0]


    summary = {

        "day":
            5,

        "dut":
            module.get(
                "name"
            ),

        "rtl_language":
            "Verilog",

        "analysis_method":
            "PyVerilog AST",

        "module_detected":
            True,

        "port_count":
            len(
                module.get(
                    "ports",
                    []
                )
            ),

        "case_statement_count":
            module.get(
                "case_statements",
                0
            ),

        "structure_json":
            str(
                STRUCTURE_FILE
            ),

        "status":
            "PASS"
    }


    OUTPUT_FILE.write_text(

        json.dumps(
            summary,
            indent=4
        )

    )


    print(
        json.dumps(
            summary,
            indent=4
        )
    )


if __name__ == "__main__":

    main()
