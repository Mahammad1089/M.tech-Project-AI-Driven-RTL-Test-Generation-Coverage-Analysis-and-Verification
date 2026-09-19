import json
import sys
from pathlib import Path


def parse_stream_file(
    stream_file
):

    path = Path(
        stream_file
    )


    if not path.exists():

        raise FileNotFoundError(
            f"Stream file not found: "
            f"{stream_file}"
        )


    events = []


    for line_number, line in enumerate(
        path.read_text().splitlines(),
        start=1
    ):

        line = line.strip()


        if not line:

            continue


        try:

            event = json.loads(
                line
            )

        except json.JSONDecodeError:

            raise ValueError(
                f"Invalid JSON on line "
                f"{line_number}"
            )


        events.append(
            event
        )


    return events


def extract_result(
    events
):

    result_events = [

        event

        for event in events

        if event.get(
            "type"
        ) == "result"
    ]


    if not result_events:

        return None


    return result_events[-1]


def main():

    if len(sys.argv) != 3:

        print(
            "Usage:"
        )

        print(
            "python hermes/"
            "response_parser.py "
            "<stream_jsonl> "
            "<output_json>"
        )

        sys.exit(1)


    stream_file = (
        sys.argv[1]
    )


    output_file = (
        sys.argv[2]
    )


    try:

        events = parse_stream_file(
            stream_file
        )

    except (
        FileNotFoundError,
        ValueError
    ) as error:

        print(
            f"ERROR: {error}"
        )

        sys.exit(1)


    result = extract_result(
        events
    )


    if result is None:

        print(
            "ERROR: Hermes result "
            "event not found."
        )

        sys.exit(1)


    parsed = {

        "event_count":
            len(
                events
            ),

        "session_id":
            result.get(
                "session_id"
            ),

        "exit_code":
            result.get(
                "exit_code"
            ),

        "response_text":
            result.get(
                "text"
            ),

        "tokens":
            result.get(
                "tokens"
            ),

        "duration_ms":
            result.get(
                "duration_ms"
            )
    }


    output_path = Path(
        output_file
    )


    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    output_path.write_text(

        json.dumps(
            parsed,
            indent=4
        )

    )


    print(
        "HERMES RESPONSE PARSE: PASS"
    )


    print(
        "Events:",
        parsed[
            "event_count"
        ]
    )


    print(
        "Exit code:",
        parsed[
            "exit_code"
        ]
    )


    print(
        f"Saved to: "
        f"{output_file}"
    )


if __name__ == "__main__":

    main()
