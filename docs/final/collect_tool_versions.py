import json
import platform
import subprocess
import sys
from pathlib import Path


OUTPUT = Path(
    "results/final/day24/tool_versions.json"
)


COMMANDS = {
    "python": [sys.executable, "--version"],
    "git": ["git", "--version"],
    "iverilog": ["iverilog", "-V"],
    "vvp": ["vvp", "-V"],
    "yosys": ["yosys", "-V"],
    "verilator": ["verilator", "--version"]
}


def get_version(command):

    try:

        result = subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=30
        )

        text = (
            result.stdout.strip()
            or result.stderr.strip()
        )

        first_line = (
            text.splitlines()[0]
            if text
            else "NO VERSION OUTPUT"
        )

        return {
            "available":
                result.returncode == 0,

            "version":
                first_line,

            "return_code":
                result.returncode
        }

    except Exception as error:

        return {
            "available": False,
            "version": str(error),
            "return_code": None
        }


def main():

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    tools = {}

    for name, command in COMMANDS.items():

        tools[name] = get_version(
            command
        )

    report = {

        "day": 24,

        "platform":
            platform.platform(),

        "python_runtime":
            sys.version.splitlines()[0],

        "tools":
            tools,

        "status":
            "PASS"
    }

    OUTPUT.write_text(
        json.dumps(
            report,
            indent=4
        )
    )

    print(
        json.dumps(
            report,
            indent=4
        )
    )

    print()

    print(
        "DAY 24 TOOL VERSION COLLECTION: PASS"
    )


if __name__ == "__main__":

    main()
