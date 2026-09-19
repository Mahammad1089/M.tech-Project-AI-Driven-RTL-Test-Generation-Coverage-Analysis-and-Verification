import json
import subprocess
import sys
from pathlib import Path


def run_hermes(
    prompt_file,
    timeout_seconds=180
):
    """
    Run Hermes Agent using a prompt file.

    Hermes is executed in:
        --oneshot mode
        --format stream-json mode

    The function parses the JSONL output,
    finds the final 'result' event and
    returns a structured Python dictionary.
    """

    prompt_path = Path(prompt_file)

    # -------------------------------------------------
    # STEP 1: Validate the prompt file
    # -------------------------------------------------

    if not prompt_path.exists():

        return {
            "status": "FAIL",
            "stage": "input",
            "error": (
                "Prompt file not found: "
                f"{prompt_file}"
            )
        }


    if not prompt_path.is_file():

        return {
            "status": "FAIL",
            "stage": "input",
            "error": (
                "Prompt path is not a file: "
                f"{prompt_file}"
            )
        }


    if prompt_path.stat().st_size == 0:

        return {
            "status": "FAIL",
            "stage": "input",
            "error": (
                "Prompt file is empty: "
                f"{prompt_file}"
            )
        }


    # -------------------------------------------------
    # STEP 2: Build the Hermes command
    # -------------------------------------------------

    command = [
        "hermes",
        "chat",

        "--oneshot",

        "--query-file",
        str(prompt_path),

        "--format",
        "stream-json"
    ]


    # -------------------------------------------------
    # STEP 3: Execute Hermes
    # -------------------------------------------------

    try:

        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )

    except subprocess.TimeoutExpired:

        return {
            "status": "FAIL",
            "stage": "timeout",
            "error": (
                "Hermes execution timed out "
                f"after {timeout_seconds} seconds."
            )
        }

    except FileNotFoundError:

        return {
            "status": "FAIL",
            "stage": "startup",
            "error": (
                "Hermes executable was not found. "
                "Check whether Hermes is installed "
                "and available in PATH."
            )
        }

    except Exception as error:

        return {
            "status": "FAIL",
            "stage": "startup",
            "error": str(error)
        }


    # -------------------------------------------------
    # STEP 4: Parse Hermes JSONL output
    # -------------------------------------------------

    events = []

    invalid_lines = []

    for line_number, line in enumerate(
        process.stdout.splitlines(),
        start=1
    ):

        line = line.strip()

        if not line:
            continue

        try:

            event = json.loads(line)

            events.append(event)

        except json.JSONDecodeError:

            invalid_lines.append({
                "line_number": line_number,
                "content": line
            })


    # -------------------------------------------------
    # STEP 5: Find the final Hermes result event
    # -------------------------------------------------

    result_events = [
        event
        for event in events
        if event.get("type") == "result"
    ]


    if not result_events:

        return {
            "status": "FAIL",
            "stage": "response",
            "return_code": process.returncode,
            "event_count": len(events),
            "invalid_line_count": len(
                invalid_lines
            ),
            "stdout": process.stdout,
            "stderr": process.stderr,
            "error": (
                "No Hermes 'result' event "
                "was found in the stream-json output."
            )
        }


    # Use the final result event
    result = result_events[-1]


    # -------------------------------------------------
    # STEP 6: Extract useful information
    # -------------------------------------------------

    hermes_exit_code = result.get(
        "exit_code"
    )

    response_text = result.get(
        "text",
        ""
    )


    # -------------------------------------------------
    # STEP 7: Check for Hermes failure
    # -------------------------------------------------

    if (
        process.returncode != 0
        or hermes_exit_code != 0
    ):

        return {
            "status": "FAIL",
            "stage": "hermes",
            "return_code": process.returncode,
            "hermes_exit_code": (
                hermes_exit_code
            ),
            "event_count": len(events),
            "invalid_line_count": len(
                invalid_lines
            ),
            "response_text": response_text,
            "stderr": process.stderr,
            "error": (
                "Hermes returned a "
                "non-zero exit code."
            )
        }


    # -------------------------------------------------
    # STEP 8: Check that response text exists
    # -------------------------------------------------

    if not response_text.strip():

        return {
            "status": "FAIL",
            "stage": "response",
            "return_code": process.returncode,
            "hermes_exit_code": (
                hermes_exit_code
            ),
            "event_count": len(events),
            "invalid_line_count": len(
                invalid_lines
            ),
            "stderr": process.stderr,
            "error": (
                "Hermes completed but returned "
                "an empty response."
            )
        }


    # -------------------------------------------------
    # STEP 9: Return successful structured result
    # -------------------------------------------------

    return {
        "status": "PASS",
        "stage": "complete",

        "return_code":
            process.returncode,

        "hermes_exit_code":
            hermes_exit_code,

        "event_count":
            len(events),

        "invalid_line_count":
            len(invalid_lines),

        "session_id":
            result.get("session_id"),

        "response_text":
            response_text,

        "tokens":
            result.get("tokens"),

        "duration_ms":
            result.get("duration_ms"),

        "stderr":
            process.stderr
    }


def main():
    """
    Command-line interface.

    Usage:

    python hermes/hermes_interface.py \
        <prompt_file> \
        <output_json>
    """

    # -------------------------------------------------
    # STEP 10: Validate command-line arguments
    # -------------------------------------------------

    if len(sys.argv) != 3:

        print("Usage:")

        print(
            "python hermes/"
            "hermes_interface.py "
            "<prompt_file> "
            "<output_json>"
        )

        sys.exit(1)


    prompt_file = sys.argv[1]

    output_file = sys.argv[2]


    print(
        "================================"
    )

    print(
        "HERMES AGENT INTERFACE"
    )

    print(
        "================================"
    )

    print()

    print(
        f"Prompt file: {prompt_file}"
    )

    print(
        "Starting Hermes..."
    )

    print()


    # -------------------------------------------------
    # STEP 11: Run Hermes
    # -------------------------------------------------

    result = run_hermes(
        prompt_file
    )


    # -------------------------------------------------
    # STEP 12: Save structured result
    # -------------------------------------------------

    output_path = Path(
        output_file
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path.write_text(
        json.dumps(
            result,
            indent=4
        )
    )


    # -------------------------------------------------
    # STEP 13: Print execution summary
    # -------------------------------------------------

    print(
        "Hermes interface status:",
        result.get("status")
    )

    print(
        "Hermes interface stage:",
        result.get("stage")
    )


    if result.get("event_count") is not None:

        print(
            "Hermes event count:",
            result.get("event_count")
        )


    if (
        result.get(
            "hermes_exit_code"
        )
        is not None
    ):

        print(
            "Hermes exit code:",
            result.get(
                "hermes_exit_code"
            )
        )


    if result.get("session_id"):

        print(
            "Hermes session ID:",
            result.get(
                "session_id"
            )
        )


    print()

    print(
        f"Result saved to: "
        f"{output_file}"
    )


    # -------------------------------------------------
    # STEP 14: Exit according to result
    # -------------------------------------------------

    if result.get("status") == "PASS":

        print()

        print(
            "HERMES INTERFACE: PASS"
        )

        sys.exit(0)


    print()

    print(
        "HERMES INTERFACE: FAIL"
    )


    if result.get("error"):

        print(
            "Error:",
            result.get("error")
        )


    sys.exit(1)


if __name__ == "__main__":

    main()
