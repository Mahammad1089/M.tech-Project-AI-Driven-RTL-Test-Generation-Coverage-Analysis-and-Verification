import json
import sys

from pathlib import Path


def main():

    if len(
        sys.argv
    ) != 3:

        print(
            "Usage: python "
            "baseline/random_fifo_tb_generator.py "
            "<transactions.json> "
            "<output.v>"
        )

        sys.exit(1)


    try:

        source = json.loads(

            Path(
                sys.argv[1]
            ).read_text()
        )


        lines = []


        for transaction in source[
            "transactions"
        ]:

            wr_en = transaction[
                "wr_en"
            ]

            rd_en = transaction[
                "rd_en"
            ]

            data_in = transaction[
                "data_in"
            ]

            read_accepted = transaction[
                "read_accepted"
            ]

            expected_read = transaction[
                "expected_read"
            ]


            if expected_read is None:

                expected_value = 0

            else:

                expected_value = (
                    expected_read
                )


            lines.append(

                "        apply_transaction("
                f"1'b{wr_en}, "
                f"1'b{rd_en}, "
                f"8'h{data_in:02X}, "
                f"1'b{1 if read_accepted else 0}, "
                f"8'h{expected_value:02X}"
                ");"
            )


        transaction_body = "\n".join(
            lines
        )


        template = r'''`timescale 1ns/1ps

module tb_fifo_day20_random;

reg clk;
reg rst;
reg wr_en;
reg rd_en;

reg [7:0] data_in;

wire [7:0] data_out;
wire full;
wire empty;

integer trace_file;

integer total_checks;
integer passed_checks;
integer failed_checks;

reg [2:0] count_before;
reg [1:0] write_ptr_before;
reg [1:0] read_ptr_before;


fifo #(
    .DATA_WIDTH(8),
    .DEPTH(4),
    .ADDR_WIDTH(2)
) dut (
    .clk(clk),
    .rst(rst),
    .wr_en(wr_en),
    .rd_en(rd_en),
    .data_in(data_in),
    .data_out(data_out),
    .full(full),
    .empty(empty)
);


initial begin

    clk = 1'b0;

    forever begin

        #5 clk = ~clk;

    end

end


task log_cycle;

input reset_value;
input write_value;
input read_value;

begin

$fdisplay(
    trace_file,
    "%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d",
    reset_value,
    write_value,
    read_value,
    count_before,
    dut.count,
    write_ptr_before,
    dut.write_ptr,
    read_ptr_before,
    dut.read_ptr,
    full,
    empty
);

end

endtask


task apply_transaction;

input write_value;
input read_value;
input [7:0] input_value;
input check_read;
input [7:0] expected_read;

begin

@(negedge clk);

rst = 1'b0;

wr_en = write_value;

rd_en = read_value;

data_in = input_value;


count_before =
    dut.count;

write_ptr_before =
    dut.write_ptr;

read_ptr_before =
    dut.read_ptr;


@(posedge clk);

#1;


if (
    check_read
) begin

    total_checks =
        total_checks + 1;


    if (
        data_out === expected_read
    ) begin

        passed_checks =
            passed_checks + 1;

    end
    else begin

        failed_checks =
            failed_checks + 1;

        $display(
            "RANDOM READ FAIL expected=%02h actual=%02h",
            expected_read,
            data_out
        );

    end

end


log_cycle(
    1'b0,
    write_value,
    read_value
);


@(negedge clk);

wr_en = 1'b0;

rd_en = 1'b0;

end

endtask


initial begin

$dumpfile(
    "results/fifo/day20/fifo_random.vcd"
);

$dumpvars(
    0,
    tb_fifo_day20_random
);


trace_file = $fopen(
    "results/fifo/day20/random_trace.csv",
    "w"
);


if (
    trace_file == 0
) begin

    $fatal(
        1,
        "Unable to open random trace."
    );

end


$fdisplay(
    trace_file,
    "rst,wr_en,rd_en,count_before,count_after,"
    "write_ptr_before,write_ptr_after,"
    "read_ptr_before,read_ptr_after,full,empty"
);


total_checks  = 0;

passed_checks = 0;

failed_checks = 0;


rst = 1'b1;

wr_en = 1'b0;

rd_en = 1'b0;

data_in = 8'h00;


repeat (2) begin

    @(negedge clk);

    count_before =
        dut.count;

    write_ptr_before =
        dut.write_ptr;

    read_ptr_before =
        dut.read_ptr;


    @(posedge clk);

    #1;


    log_cycle(
        1'b1,
        1'b0,
        1'b0
    );

end


@(negedge clk);

rst = 1'b0;


__TRANSACTIONS__


$fclose(
    trace_file
);


$display("");

$display(
    "========================================"
);

$display(
    "DAY 20 RANDOM BASELINE"
);

$display(
    "========================================"
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
        "DAY 20 RANDOM BASELINE PASS"
    );

end
else begin

    $display(
        "DAY 20 RANDOM BASELINE FAIL"
    );

    $fatal(
        1,
        "Random baseline failed."
    );

end


$display(
    "========================================"
);

#10;

$finish;

end

endmodule
'''


        output_text = template.replace(

            "__TRANSACTIONS__",
            transaction_body
        )


        Path(
            sys.argv[2]
        ).write_text(
            output_text
        )


    except Exception as error:

        print(
            "RANDOM FIFO TB GENERATION: FAIL"
        )

        print(
            "ERROR:",
            error
        )

        sys.exit(1)


    print(
        "RANDOM FIFO TB GENERATION: PASS"
    )

    print(
        "Transactions:",
        len(
            source[
                "transactions"
            ]
        )
    )


if __name__ == "__main__":
    main()
