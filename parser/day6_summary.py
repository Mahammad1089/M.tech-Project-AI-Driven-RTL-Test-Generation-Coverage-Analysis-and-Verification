import json
from pathlib import Path


KNOWLEDGE_FILE = Path(
    "results/alu/day6/"
    "alu_knowledge.json"
)


SUMMARY_FILE = Path(
    "results/alu/day6/"
    "day6_summary.json"
)


def main():

    if not KNOWLEDGE_FILE.exists():

        print(
            "DAY 6 SUMMARY: FAIL"
        )

        raise SystemExit(1)


    data = json.loads(
        KNOWLEDGE_FILE.read_text()
    )


    modules = data.get(
        "modules",
        []
    )


    if not modules:

        print(
            "DAY 6 SUMMARY: FAIL"
        )

        raise SystemExit(1)


    module = modules[0]


    case_logic = module.get(
        "case_logic",
        []
    )


    branch_count = 0


    for case_info in case_logic:

        branch_count += len(
            case_info.get(
                "branches",
                []
            )
        )


    summary = {

        "day":
            6,

        "dut":
            module.get(
                "module_name"
            ),

        "rtl_language":
            data.get(
                "rtl_language"
            ),

        "analysis_method":
            data.get(
                "analysis_method"
            ),

        "port_count":
            len(
                module.get(
                    "ports",
                    []
                )
            ),

        "case_statement_count":
            len(
                case_logic
            ),

        "case_branch_count":
            branch_count,

        "knowledge_model":
            str(
                KNOWLEDGE_FILE
            ),

        "status":
            "PASS"
    }


    SUMMARY_FILE.write_text(

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
