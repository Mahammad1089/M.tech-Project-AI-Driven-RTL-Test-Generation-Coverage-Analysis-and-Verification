import json
import sys

from pathlib import Path


def load_json(
    path
):

    return json.loads(
        Path(
            path
        ).read_text()
    )


def action_to_verilog(
    action
):

    name = action[
        "action"
    ]


    if name == "RESET":

        return "        reset_fifo();"


    if name == "IDLE":

        return "        idle_fifo();"


    if name == "WRITE":

        value = action[
            "data"
        ]

        return (
            "        write_fifo("
            f"8'h{value:02X}"
            ");"
        )


    if name == "READ":

        expected = action[
            "expected"
        ]

        return (
            "        read_fifo("
            f"8'h{expected:02X}"
            ");"
        )


    if name == "READ_EMPTY":

        return (
            "        read_empty_fifo();"
        )


    if name == "WRITE_FULL":

        value = action[
            "data"
        ]

        return (
            "        write_full_fifo("
            f"8'h{value:02X}"
            ");"
        )


    if name == "SIMULTANEOUS":

        value = action[
            "data"
        ]

        expected = action[
            "expected"
        ]

        return (

            "        simultaneous_fifo("
            f"8'h{value:02X}, "
            f"8'h{expected:02X}"
            ");"
        )


    raise ValueError(
        f"Unknown FIFO action: {name}"
    )


def main():

    if len(
        sys.argv
    ) != 3:

        print(
            "Usage: python "
            "test_generation/fifo_tb_generator.py "
            "<targets.json> "
            "<output_tb.v>"
        )

        sys.exit(1)


    try:

        data = load_json(
            sys.argv[1]
        )


        body = []


        for target in data[
            "targets"
        ]:

            body.append(
                ""
            )

            body.append(
                "        // "
                + target[
                    "target_id"
                ]
                + " -> "
                + target[
                    "coverage_id"
                ]
            )


            for action in target[
                "actions"
            ]:

                body.append(
                    action_to_verilog(
                        action
                    )
                )


        if not body:

            body.append(
                '        $display('
                '"NO TARGETED FIFO GAPS TO EXECUTE");'
            )


        body_text = "\n".join(
            body
        )


        verilog = r'''`timescale 1ns/1ps

module tb_fifo_day19_closure;

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
    clk = 0;
    forever #5 clk = ~clk;
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


task reset_fifo;
begin

@(negedge clk);

rst = 1;
wr_en = 0;
rd_en = 0;

count_before = dut.count;
write_ptr_before = dut.write_ptr;
read_ptr_before = dut.read_ptr;

@(posedge clk);
#1;

log_cycle(
    1,
    0,
    0
);

@(negedge clk);

rst = 0;

end
endtask


task idle_fifo;
begin

@(negedge clk);

rst = 0;
wr_en = 0;
rd_en = 0;

count_before = dut.count;
write_ptr_before = dut.write_ptr;
read_ptr_before = dut.read_ptr;

@(posedge clk);
#1;

log_cycle(
    0,
    0,
    0
);

end
endtask


task write_fifo;

input [7:0] value;

begin

@(negedge clk);

rst = 0;
wr_en = 1;
rd_en = 0;
data_in = value;

count_before = dut.count;
write_ptr_before = dut.write_ptr;
read_ptr_before = dut.read_ptr;

@(posedge clk);
#1;

log_cycle(
    0,
    1,
    0
);

@(negedge clk);

wr_en = 0;

end
endtask


task read_fifo;

input [7:0] expected;

begin

@(negedge clk);

rst = 0;
wr_en = 0;
rd_en = 1;

count_before = dut.count;
write_ptr_before = dut.write_ptr;
read_ptr_before = dut.read_ptr;

@(posedge clk);
#1;

total_checks =
    total_checks + 1;

if (
    data_out === expected
)
    passed_checks =
        passed_checks + 1;
else begin

    failed_checks =
        failed_checks + 1;

    $display(
        "CHECK_FAIL READ expected=%02h actual=%02h",
        expected,
        data_out
    );

end

log_cycle(
    0,
    0,
    1
);

@(negedge clk);

rd_en = 0;

end
endtask


task read_empty_fifo;
begin

@(negedge clk);

rst = 0;
wr_en = 0;
rd_en = 1;

count_before = dut.count;
write_ptr_before = dut.write_ptr;
read_ptr_before = dut.read_ptr;

@(posedge clk);
#1;

total_checks =
    total_checks + 1;

if (
    empty === 1'b1
)
    passed_checks =
        passed_checks + 1;
else
    failed_checks =
        failed_checks + 1;

log_cycle(
    0,
    0,
    1
);

@(negedge clk);

rd_en = 0;

end
endtask


task write_full_fifo;

input [7:0] value;

begin

@(negedge clk);

rst = 0;
wr_en = 1;
rd_en = 0;
data_in = value;

count_before = dut.count;
write_ptr_before = dut.write_ptr;
read_ptr_before = dut.read_ptr;

@(posedge clk);
#1;

total_checks =
    total_checks + 1;

if (
    full === 1'b1
)
    passed_checks =
        passed_checks + 1;
else
    failed_checks =
        failed_checks + 1;

log_cycle(
    0,
    1,
    0
);

@(negedge clk);

wr_en = 0;

end
endtask


task simultaneous_fifo;

input [7:0] value;
input [7:0] expected;

begin

@(negedge clk);

rst = 0;
wr_en = 1;
rd_en = 1;
data_in = value;

count_before = dut.count;
write_ptr_before = dut.write_ptr;
read_ptr_before = dut.read_ptr;

@(posedge clk);
#1;

total_checks =
    total_checks + 1;

if (
    data_out === expected
)
    passed_checks =
        passed_checks + 1;
else begin

    failed_checks =
        failed_checks + 1;

    $display(
        "CHECK_FAIL SIM expected=%02h actual=%02h",
        expected,
        data_out
    );

end

log_cycle(
    0,
    1,
    1
);

@(negedge clk);

wr_en = 0;
rd_en = 0;

end
endtask


initial begin

$dumpfile(
    "results/fifo/day19/fifo_day19_targeted.vcd"
);

$dumpvars(
    0,
    tb_fifo_day19_closure
);


trace_file = $fopen(
    "results/fifo/day19/fifo_targeted_trace.csv",
    "w"
);


if (
    trace_file == 0
)
    $fatal(
        1,
        "Unable to open targeted trace."
    );


$fdisplay(
    trace_file,
    "rst,wr_en,rd_en,count_before,count_after,"
    "write_ptr_before,write_ptr_after,"
    "read_ptr_before,read_ptr_after,full,empty"
);


total_checks = 0;
passed_checks = 0;
failed_checks = 0;

rst = 1;
wr_en = 0;
rd_en = 0;
data_in = 0;

repeat (2)
    @(posedge clk);

@(negedge clk);

rst = 0;

__TARGET_BODY__


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
)
    $display(
        "DAY 19 TARGETED FIFO PASS"
    );
else begin

    $display(
        "DAY 19 TARGETED FIFO FAIL"
    );

    $fatal(
        1,
        "Targeted FIFO verification failed."
    );

end


#10;

$finish;

end

endmodule
'''


        verilog = verilog.replace(

            "__TARGET_BODY__",
            body_text
        )


        Path(
            sys.argv[2]
        ).write_text(
            verilog
        )


    except Exception as error:

        print(
            "FIFO TB GENERATION: FAIL"
        )

        print(
            "ERROR:",
            error
        )

        sys.exit(1)


    print(
        "FIFO TB GENERATION: PASS"
    )

    print(
        "Target groups:",
        data[
            "target_count"
        ]
    )


if __name__ == "__main__":
    main()
