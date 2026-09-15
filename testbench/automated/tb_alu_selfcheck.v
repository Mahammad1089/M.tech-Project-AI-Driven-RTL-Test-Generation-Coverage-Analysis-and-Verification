`timescale 1ns/1ps

module tb_alu_selfcheck;

reg  [3:0] a;
reg  [3:0] b;
reg  [2:0] sel;

wire [3:0] y;

integer total_tests;
integer passed_tests;
integer failed_tests;

reg [3:0] expected;


alu dut (
    .a(a),
    .b(b),
    .sel(sel),
    .y(y)
);


task run_test;

    input [3:0] test_a;
    input [3:0] test_b;
    input [2:0] test_sel;
    input [3:0] test_expected;

    begin

        a = test_a;
        b = test_b;
        sel = test_sel;
        expected = test_expected;

        #10;

        total_tests = total_tests + 1;

        if (y === expected) begin

            passed_tests = passed_tests + 1;

            $display(
                "PASS | a=%b b=%b sel=%b expected=%b actual=%b",
                a,
                b,
                sel,
                expected,
                y
            );

        end

        else begin

            failed_tests = failed_tests + 1;

            $display(
                "FAIL | a=%b b=%b sel=%b expected=%b actual=%b",
                a,
                b,
                sel,
                expected,
                y
            );

        end

    end

endtask


initial begin

    $dumpfile(
        "results/alu/day3/alu_selfcheck.vcd"
    );

    $dumpvars(
        0,
        tb_alu_selfcheck
    );


    total_tests = 0;
    passed_tests = 0;
    failed_tests = 0;


    $display(
        "=============================================="
    );

    $display(
        "DAY 3 - SELF-CHECKING ALU VERIFICATION"
    );

    $display(
        "=============================================="
    );


    // Basic operation tests

    run_test(
        4'b0101,
        4'b0011,
        3'b000,
        4'b1000
    );

    run_test(
        4'b0101,
        4'b0011,
        3'b001,
        4'b0010
    );

    run_test(
        4'b0101,
        4'b0011,
        3'b010,
        4'b0001
    );

    run_test(
        4'b0101,
        4'b0011,
        3'b011,
        4'b0111
    );

    run_test(
        4'b0101,
        4'b0011,
        3'b100,
        4'b0110
    );

    run_test(
        4'b0101,
        4'b0000,
        3'b101,
        4'b1010
    );

    run_test(
        4'b0101,
        4'b0000,
        3'b110,
        4'b1010
    );

    run_test(
        4'b0101,
        4'b0000,
        3'b111,
        4'b0010
    );

$display("CORNER TESTING");

    run_test(
        4'b1111,
        4'b0001,
        3'b000,
        4'b0000
    );

    run_test(
    	4'b0000,
    	4'b0001,
    	3'b001,
    	4'b1111
    );

    run_test(
    	4'b0000,
    	4'b0000,
    	3'b000,
    	4'b0000
    );
    
    run_test(
    	4'b0000,
    	4'b0000,
    	3'b010,
    	4'b0000
    );

    run_test(
    	4'b0000,
    	4'b0000,
    	3'b011,
    	4'b0000
    );

    run_test(
    	4'b1111,
    	4'b1111,
    	3'b010,
    	4'b1111
    );

    run_test(
    	4'b1111,
    	4'b1111,
    	3'b100,
    	4'b0000
    );

    run_test(
    	4'b1010,
    	4'b0101,
    	3'b011,
    	4'b1111
    );

    run_test(
    	4'b1010,
    	4'b0101,
    	3'b010,
    	4'b0000
    );

    run_test(
    	4'b1000,
    	4'b0000,
    	3'b110,
    	4'b0000
    );
   
    run_test(
    	4'b0001,
    	4'b0000,
    	3'b111,
    	4'b0000
    );

    run_test(
    	4'b0000,
    	4'b0000,
    	3'b101,
    	4'b1111
);

    run_test(
    	4'b1111,
    	4'b0000,
    	3'b101,
    	4'b0000
);

    

    $display(
        "=============================================="
    );

    $display(
        "TOTAL TESTS  = %0d",
        total_tests
    );

    $display(
        "PASSED TESTS = %0d",
        passed_tests
    );

    $display(
        "FAILED TESTS = %0d",
        failed_tests
    );


    if (failed_tests == 0)

        $display(
            "DAY 3 BASIC ALU VERIFICATION: PASS"
        );

    else

        $display(
            "DAY 3 BASIC ALU VERIFICATION: FAIL"
        );


    $display(
        "=============================================="
    );

    $finish;

end

endmodule
