import json
import sys
from pathlib import Path


def load_json(path):

    file_path = Path(path)

    if not file_path.exists():

        raise FileNotFoundError(
            f"File not found: {path}"
        )

    return json.loads(
        file_path.read_text()
    )


def expected_detect(
    history
):

    if len(history) < 4:

        return 0


    return int(
        history[-4:]
        == [1, 0, 1, 1]
    )


def main():

    if len(sys.argv) != 3:

        print(
            "Usage: python "
            "test_generation/"
            "fsm_tb_generator.py "
            "<target_sequences_json> "
            "<output_verilog>"
        )

        sys.exit(1)


    try:

        data = load_json(
            sys.argv[1]
        )

        targets = data.get(
            "targets",
            []
        )


        if not isinstance(
            targets,
            list
        ):

            raise ValueError(
                "targets must be a list."
            )


        body = []


        for target in targets:

            sequence = target.get(
                "input_sequence"
            )


            if not isinstance(
                sequence,
                list
            ):

                raise ValueError(
                    "Invalid input sequence."
                )


            history = []


            body.append(
                "        reset_fsm();"
            )


            for bit in sequence:

                if bit not in (
                    0,
                    1
                ):

                    raise ValueError(
                        "FSM input must "
                        "be 0 or 1."
                    )


                history.append(
                    bit
                )


                detect = (
                    expected_detect(
                        history
                    )
                )


                body.append(
                    "        "
                    f"apply_bit(1'b{bit}, "
                    f"1'b{detect});"
                )


        if not targets:

            body.append(
                "        "
                "$display("
                "\"NO TARGETED GAPS TO EXECUTE\""
                ");"
            )


        body_text = "\n".join(
            body
        )


        verilog = f'''`timescale 1ns/1ps

module tb_fsm_day17_closure;

    reg clk;
    reg rst;
    reg din;

    wire detected;

    integer trace_file;
    integer total_checks;
    integer passed_checks;
    integer failed_checks;

    reg [1:0] previous_state;


    fsm_1011 dut (
        .clk(clk),
        .rst(rst),
        .din(din),
        .detected(detected)
    );


    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;
    end


    task reset_fsm;

        begin

            @(negedge clk);

            rst = 1'b1;
            din = 1'b0;

            @(posedge clk);

            #1;

            @(negedge clk);

            rst = 1'b0;

        end

    endtask


    task apply_bit;

        input input_bit;
        input expected_detect;

        begin

            @(negedge clk);

            din = input_bit;

            #1;

            previous_state =
                dut.current_state;

            total_checks =
                total_checks + 1;


            if (
                detected
                === expected_detect
            ) begin

                passed_checks =
                    passed_checks + 1;

            end
            else begin

                failed_checks =
                    failed_checks + 1;

                $display(
                    "CHECK_FAIL "
                    "din=%b "
                    "expected=%b "
                    "actual=%b",
                    input_bit,
                    expected_detect,
                    detected
                );

            end


            @(posedge clk);

            #1;


            $fdisplay(
                trace_file,
                "%b,%b,%b,%b",
                previous_state,
                input_bit,
                dut.current_state,
                expected_detect
            );

        end

    endtask


    initial begin

        $dumpfile(
            "results/fsm/day17/"
            "fsm_day17_closure.vcd"
        );

        $dumpvars(
            0,
            tb_fsm_day17_closure
        );


        trace_file = $fopen(
            "results/fsm/day17/"
            "fsm_targeted_trace.csv",
            "w"
        );


        if (
            trace_file == 0
        ) begin

            $fatal(
                1,
                "Unable to open trace."
            );

        end


        $fdisplay(
            trace_file,
            "from_state,input,"
            "to_state,detected"
        );


        total_checks  = 0;
        passed_checks = 0;
        failed_checks = 0;

        rst = 1'b1;
        din = 1'b0;

        repeat (2)
            @(posedge clk);

        @(negedge clk);

        rst = 1'b0;


{body_text}


        $fclose(
            trace_file
        );


        $display(
            "TOTAL CHECKS  = %0d",
            total_checks
        );

        $display(
            "PASSED CHECKS = %0d",
            passed_checks
        );

        $display(
            "FAILED CHECKS = %0d",
            failed_checks
        );


        if (
            failed_checks == 0
        ) begin

            $display(
                "DAY 17 TARGETED FSM PASS"
            );

        end
        else begin

            $display(
                "DAY 17 TARGETED FSM FAIL"
            );

            $fatal;

        end


        #10;

        $finish;

    end

endmodule
'''


    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError
    ) as error:

        print(
            "FSM TB GENERATION: FAIL"
        )

        print(
            f"ERROR: {error}"
        )

        sys.exit(1)


    output = Path(
        sys.argv[2]
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output.write_text(
        verilog
    )


    print(
        "FSM TB GENERATION: PASS"
    )

    print(
        "Target groups:",
        len(targets)
    )


if __name__ == "__main__":

    main()
