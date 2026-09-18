import json
import sys
from pathlib import Path

from pyverilog.vparser.parser import parse
from pyverilog.vparser.ast import ModuleDef
from pyverilog.vparser.ast import Input
from pyverilog.vparser.ast import Output
from pyverilog.vparser.ast import Inout
from pyverilog.vparser.ast import CaseStatement


def width_to_dict(width):

    if width is None:

        return {
            "msb": 0,
            "lsb": 0,
            "bits": 1
        }


    try:

        msb = int(
            width.msb.value
        )

        lsb = int(
            width.lsb.value
        )


        return {
            "msb": msb,
            "lsb": lsb,
            "bits": abs(msb - lsb) + 1
        }


    except Exception:

        return {
            "msb": None,
            "lsb": None,
            "bits": None
        }


def walk(node):

    yield node

    for child in node.children():

        yield from walk(child)


def extract_structure(ast):

    data = {
        "modules": []
    }


    for node in walk(ast):

        if isinstance(
            node,
            ModuleDef
        ):

            module_data = {

                "name":
                    node.name,

                "ports":
                    [],

                "case_statements":
                    0
            }


            for item in walk(node):

                if isinstance(
                    item,
                    Input
                ):

                    module_data[
                        "ports"
                    ].append({

                        "name":
                            item.name,

                        "direction":
                            "input",

                        "width":
                            width_to_dict(
                                item.width
                            )
                    })


                elif isinstance(
                    item,
                    Output
                ):

                    module_data[
                        "ports"
                    ].append({

                        "name":
                            item.name,

                        "direction":
                            "output",

                        "width":
                            width_to_dict(
                                item.width
                            )
                    })


                elif isinstance(
                    item,
                    Inout
                ):

                    module_data[
                        "ports"
                    ].append({

                        "name":
                            item.name,

                        "direction":
                            "inout",

                        "width":
                            width_to_dict(
                                item.width
                            )
                    })


                elif isinstance(
                    item,
                    CaseStatement
                ):

                    module_data[
                        "case_statements"
                    ] += 1


            data[
                "modules"
            ].append(
                module_data
            )


    return data


def main():

    if len(sys.argv) != 3:

        print(
            "Usage:"
        )

        print(
            "python parser/extract_structure.py "
            "<rtl_file> <output_json>"
        )

        sys.exit(1)


    rtl_file = sys.argv[1]

    output_json = sys.argv[2]


    if not Path(
        rtl_file
    ).exists():

        print(
            f"ERROR: RTL file not found: "
            f"{rtl_file}"
        )

        sys.exit(1)


    ast, directives = parse(
        [rtl_file]
    )


    structure = extract_structure(
        ast
    )


    output_path = Path(
        output_json
    )


    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    output_path.write_text(

        json.dumps(
            structure,
            indent=4
        )

    )


    print(
        json.dumps(
            structure,
            indent=4
        )
    )


    print()
    print(
        f"JSON saved to: "
        f"{output_json}"
    )


if __name__ == "__main__":

    main()
