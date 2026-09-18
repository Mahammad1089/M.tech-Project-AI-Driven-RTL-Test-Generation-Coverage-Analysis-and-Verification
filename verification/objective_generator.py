import json
import sys
from pathlib import Path


SUPPORTED_OPERATIONS = {
    "ADD",
    "SUB",
    "AND",
    "OR",
    "XOR",
    "NOT",
    "SHIFT_LEFT",
    "SHIFT_RIGHT"
}


def load_knowledge(
    knowledge_file
):

    path = Path(
        knowledge_file
    )


    if not path.exists():

        print(
            f"ERROR: Knowledge file "
            f"not found: {knowledge_file}"
        )

        return None


    try:

        return json.loads(
            path.read_text()
        )


    except json.JSONDecodeError as error:

        print(
            "ERROR: Invalid JSON."
        )

        print(
            error
        )

        return None


def generate_functional_objectives(
    knowledge
):

    objectives = []


    modules = knowledge.get(
        "modules",
        []
    )


    objective_number = 1


    for module in modules:

        module_name = module.get(
            "module_name"
        )


        for case_info in module.get(
            "case_logic",
            []
        ):

            selector = case_info.get(
                "selector"
            )


            for branch in case_info.get(
                "branches",
                []
            ):

                operation = branch.get(
                    "operator"
                )


                case_value = branch.get(
                    "case_value"
                )


                if (
                    operation
                    not in
                    SUPPORTED_OPERATIONS
                ):

                    continue


                objective_id = (
                    f"OBJ_"
                    f"{module_name.upper()}_"
                    f"{objective_number:03d}"
                )


                objective = {

                    "objective_id":
                        objective_id,

                    "category":
                        "functional",

                    "operation":
                        operation,

                    "selector":
                        selector,

                    "case_value":
                        case_value,

                    "expression":
                        branch.get(
                            "expression"
                        ),

                    "description":
                        (
                            f"Verify "
                            f"{operation} "
                            f"operation"
                        ),

                    "priority":
                        "high",

                    "source":
                        "rtl_knowledge"
                }


                objectives.append(
                    objective
                )


                objective_number += 1


    return objectives


CORNER_CASE_RULES = {

    "ADD": [

        {
            "name":
                "zero_operands",

            "description":
                "Verify ADD with zero operands",

            "priority":
                "medium"
        },

        {
            "name":
                "maximum_operands",

            "description":
                "Verify ADD with maximum "
                "4-bit operands",

            "priority":
                "high"
        },

        {
            "name":
                "overflow_wraparound",

            "description":
                "Verify 4-bit ADD overflow "
                "and wraparound behavior",

            "priority":
                "high"
        }
    ],


    "SUB": [

        {
            "name":
                "equal_operands",

            "description":
                "Verify SUB with equal operands",

            "priority":
                "medium"
        },

        {
            "name":
                "zero_subtrahend",

            "description":
                "Verify SUB when b is zero",

            "priority":
                "medium"
        },

        {
            "name":
                "underflow_wraparound",

            "description":
                "Verify 4-bit SUB underflow "
                "and wraparound behavior",

            "priority":
                "high"
        }
    ],


    "AND": [

        {
            "name":
                "all_zero",

            "description":
                "Verify AND with all-zero input",

            "priority":
                "medium"
        },

        {
            "name":
                "all_one",

            "description":
                "Verify AND with all-one input",

            "priority":
                "medium"
        },

        {
            "name":
                "alternating_patterns",

            "description":
                "Verify AND with alternating "
                "bit patterns",

            "priority":
                "medium"
        }
    ],


    "OR": [

        {
            "name":
                "all_zero",

            "description":
                "Verify OR with all-zero input",

            "priority":
                "medium"
        },

        {
            "name":
                "all_one",

            "description":
                "Verify OR with all-one input",

            "priority":
                "medium"
        },

        {
            "name":
                "alternating_patterns",

            "description":
                "Verify OR with alternating "
                "bit patterns",

            "priority":
                "medium"
        }
    ],


    "XOR": [

        {
            "name":
                "equal_operands",

            "description":
                "Verify XOR with equal operands",

            "priority":
                "medium"
        },

        {
            "name":
                "complementary_patterns",

            "description":
                "Verify XOR with complementary "
                "bit patterns",

            "priority":
                "medium"
        }
    ],


    "NOT": [

        {
            "name":
                "all_zero",

            "description":
                "Verify NOT of all-zero input",

            "priority":
                "medium"
        },

        {
            "name":
                "all_one",

            "description":
                "Verify NOT of all-one input",

            "priority":
                "medium"
        },

        {
            "name":
                "alternating_pattern",

            "description":
                "Verify NOT of an alternating "
                "bit pattern",

            "priority":
                "medium"
        }
    ],


    "SHIFT_LEFT": [

        {
            "name":
                "zero_input",

            "description":
                "Verify left shift of zero",

            "priority":
                "medium"
        },

        {
            "name":
                "msb_discard",

            "description":
                "Verify left shift when MSB "
                "is discarded",

            "priority":
                "high"
        }
    ],


    "SHIFT_RIGHT": [

        {
            "name":
                "zero_input",

            "description":
                "Verify right shift of zero",

            "priority":
                "medium"
        },

        {
            "name":
                "lsb_discard",

            "description":
                "Verify right shift when LSB "
                "is discarded",

            "priority":
                "high"
        }
    ]
}


def generate_corner_objectives(
    functional_objectives
):

    corner_objectives = []


    next_number = (
        len(
            functional_objectives
        )
        + 1
    )


    for functional in (
        functional_objectives
    ):

        operation = functional.get(
            "operation"
        )


        rules = CORNER_CASE_RULES.get(
            operation,
            []
        )


        for rule in rules:

            module_prefix = (
                functional[
                    "objective_id"
                ].split(
                    "_"
                )[1]
            )


            objective_id = (
                f"OBJ_"
                f"{module_prefix}_"
                f"{next_number:03d}"
            )


            objective = {

                "objective_id":
                    objective_id,

                "category":
                    "corner_case",

                "operation":
                    operation,

                "selector":
                    functional.get(
                        "selector"
                    ),

                "case_value":
                    functional.get(
                        "case_value"
                    ),

                "corner_case":
                    rule[
                        "name"
                    ],

                "description":
                    rule[
                        "description"
                    ],

                "priority":
                    rule[
                        "priority"
                    ],

                "source":
                    "derived_rule",

                "parent_objective":
                    functional[
                        "objective_id"
                    ]
            }


            corner_objectives.append(
                objective
            )


            next_number += 1


    return corner_objectives

def build_objective_model(
    knowledge
):

    functional = (
        generate_functional_objectives(
            knowledge
        )
    )


    corner_cases = (
        generate_corner_objectives(
            functional
        )
    )


    all_objectives = (
        functional
        + corner_cases
    )


    module_names = [

        module.get(
            "module_name"
        )

        for module in knowledge.get(
            "modules",
            []
        )
    ]


    return {

        "rtl_language":
            knowledge.get(
                "rtl_language"
            ),

        "source_analysis":
            knowledge.get(
                "analysis_method"
            ),

        "modules":
            module_names,

        "functional_objective_count":
            len(
                functional
            ),

        "corner_case_objective_count":
            len(
                corner_cases
            ),

        "total_objective_count":
            len(
                all_objectives
            ),

        "objectives":
            all_objectives
    }


def main():

    if len(sys.argv) != 3:

        print(
            "Usage:"
        )

        print(
            "python "
            "verification/"
            "objective_generator.py "
            "<knowledge_json> "
            "<output_json>"
        )

        sys.exit(1)


    knowledge_file = (
        sys.argv[1]
    )


    output_file = (
        sys.argv[2]
    )


    knowledge = load_knowledge(
        knowledge_file
    )


    if knowledge is None:

        sys.exit(1)


    model = build_objective_model(
        knowledge
    )


    output_path = Path(
        output_file
    )


    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    output_path.write_text(

        json.dumps(
            model,
            indent=4
        )

    )


    print(
        "================================"
    )

    print(
        "VERIFICATION OBJECTIVE GENERATOR"
    )

    print(
        "================================"
    )


    print(
        "Functional objectives :",
        model[
            "functional_objective_count"
        ]
    )


    print(
        "Corner objectives     :",
        model[
            "corner_case_objective_count"
        ]
    )


    print(
        "Total objectives      :",
        model[
            "total_objective_count"
        ]
    )


    print()


    print(
        f"Saved to: "
        f"{output_file}"
    )


if __name__ == "__main__":

    main()
