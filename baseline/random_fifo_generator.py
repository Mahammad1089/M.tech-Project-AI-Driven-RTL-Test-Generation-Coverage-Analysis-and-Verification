import json
import random
import sys

from pathlib import Path


DEFAULT_SEED = 20260926
DEFAULT_CYCLES = 20


def generate(
    seed,
    cycles
):

    rng = random.Random(
        seed
    )


    model = []

    transactions = []


    for cycle in range(
        1,
        cycles + 1
    ):

        wr_en = rng.randint(
            0,
            1
        )

        rd_en = rng.randint(
            0,
            1
        )

        data_in = rng.randint(
            0,
            255
        )


        count_before = len(
            model
        )


        expected_read = None


        # Match the FIFO RTL policy:
        # write accepted if not full
        # read accepted if not empty.

        write_accepted = (
            wr_en == 1
            and count_before < 4
        )

        read_accepted = (
            rd_en == 1
            and count_before > 0
        )


        if read_accepted:

            expected_read = model[
                0
            ]


        if read_accepted:

            model.pop(
                0
            )


        if write_accepted:

            model.append(
                data_in
            )


        transactions.append({

            "cycle":
                cycle,

            "wr_en":
                wr_en,

            "rd_en":
                rd_en,

            "data_in":
                data_in,

            "count_before":
                count_before,

            "write_accepted":
                write_accepted,

            "read_accepted":
                read_accepted,

            "expected_read":
                expected_read,

            "count_after":
                len(model),
        })


    return {

        "dut":
            "fifo",

        "strategy":
            "random",

        "seed":
            seed,

        "cycles":
            cycles,

        "transactions":
            transactions,
    }


def main():

    seed = DEFAULT_SEED

    cycles = DEFAULT_CYCLES


    if len(
        sys.argv
    ) >= 2:

        seed = int(
            sys.argv[1]
        )


    if len(
        sys.argv
    ) >= 3:

        cycles = int(
            sys.argv[2]
        )


    if cycles <= 0:

        print(
            "RANDOM FIFO GENERATION: FAIL"
        )

        print(
            "ERROR: cycles must be greater than zero."
        )

        sys.exit(1)


    report = generate(
        seed,
        cycles
    )


    output = Path(
        "results/fifo/day20/random_transactions.json"
    )


    output.write_text(

        json.dumps(
            report,
            indent=4
        )
    )


    print(
        "RANDOM FIFO GENERATION: PASS"
    )

    print(
        "Seed   :",
        seed
    )

    print(
        "Cycles :",
        cycles
    )

    print(
        "Output :",
        output
    )


if __name__ == "__main__":
    main()
