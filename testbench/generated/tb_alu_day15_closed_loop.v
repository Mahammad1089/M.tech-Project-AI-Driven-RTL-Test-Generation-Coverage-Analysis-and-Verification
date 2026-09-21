`timescale 1ns/1ps

module tb_alu_hermes_generated;

    reg  [3:0] a;
    reg  [3:0] b;
    reg  [2:0] sel;
    wire [3:0] y;

    integer pass_count;
    integer fail_count;

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
        input [3:0] expected_y;
        input integer test_number;
        begin
            a   = test_a;
            b   = test_b;
            sel = test_sel;
            #10;

            if (y === expected_y) begin
                pass_count = pass_count + 1;
                $display("PASS test=%0d a=%h b=%h sel=%b y=%h",
                         test_number, a, b, sel, y);
            end
            else begin
                fail_count = fail_count + 1;
                $display("FAIL test=%0d a=%h b=%h sel=%b expected=%h actual=%h",
                         test_number, a, b, sel, expected_y, y);
            end
        end
    endtask

    initial begin
        $dumpfile("results/alu/day11/alu_hermes_generated.vcd");
        $dumpvars(0, tb_alu_hermes_generated);

        pass_count = 0;
        fail_count = 0;

        a = 4'b0000;
        b = 4'b0000;
        sel = 3'b000;

        #5;

        // OBJ_ALU_001 | ADD
        run_test(4'h5, 4'h3, 3'h0, 4'h8, 1);

        // OBJ_ALU_002 | SUB
        run_test(4'hA, 4'h4, 3'h1, 4'h6, 2);

        // OBJ_ALU_003 | AND
        run_test(4'hC, 4'hA, 3'h2, 4'h8, 3);

        // OBJ_ALU_004 | OR
        run_test(4'h7, 4'h9, 3'h3, 4'hF, 4);

        // OBJ_ALU_005 | XOR
        run_test(4'h6, 4'h5, 3'h4, 4'h3, 5);

        // OBJ_ALU_006 | NOT
        run_test(4'h9, 4'h0, 3'h5, 4'h6, 6);

        // OBJ_ALU_007 | SHIFT_LEFT
        run_test(4'h3, 4'h0, 3'h6, 4'h6, 7);

        // OBJ_ALU_008 | SHIFT_RIGHT
        run_test(4'hC, 4'h0, 3'h7, 4'h6, 8);

        // OBJ_ALU_009 | ADD
        run_test(4'h0, 4'h0, 3'h0, 4'h0, 9);

        // OBJ_ALU_010 | ADD
        run_test(4'hF, 4'hF, 3'h0, 4'hE, 10);

        // OBJ_ALU_011 | ADD
        run_test(4'hA, 4'h9, 3'h0, 4'h3, 11);

        // OBJ_ALU_012 | SUB
        run_test(4'h7, 4'h7, 3'h1, 4'h0, 12);

        // OBJ_ALU_013 | SUB
        run_test(4'hC, 4'h0, 3'h1, 4'hC, 13);

        // OBJ_ALU_014 | SUB
        run_test(4'h2, 4'h5, 3'h1, 4'hD, 14);

        // OBJ_ALU_015 | AND
        run_test(4'h0, 4'h5, 3'h2, 4'h0, 15);

        // OBJ_ALU_016 | AND
        run_test(4'hF, 4'hC, 3'h2, 4'hC, 16);

        // OBJ_ALU_017 | AND
        run_test(4'hA, 4'h5, 3'h2, 4'h0, 17);

        // OBJ_ALU_018 | OR
        run_test(4'h0, 4'h8, 3'h3, 4'h8, 18);

        // OBJ_ALU_019 | OR
        run_test(4'hF, 4'hA, 3'h3, 4'hF, 19);

        // OBJ_ALU_020 | OR
        run_test(4'hA, 4'h5, 3'h3, 4'hF, 20);

        // OBJ_ALU_021 | XOR
        run_test(4'h8, 4'h8, 3'h4, 4'h0, 21);

        // OBJ_ALU_022 | XOR
        run_test(4'hF, 4'h0, 3'h4, 4'hF, 22);

        // OBJ_ALU_023 | NOT
        run_test(4'h0, 4'h0, 3'h5, 4'hF, 23);

        // OBJ_ALU_024 | NOT
        run_test(4'hF, 4'h0, 3'h5, 4'h0, 24);

        // OBJ_ALU_025 | NOT
        run_test(4'hA, 4'h0, 3'h5, 4'h5, 25);

        // OBJ_ALU_026 | SHIFT_LEFT
        run_test(4'h0, 4'h0, 3'h6, 4'h0, 26);

        // OBJ_ALU_027 | SHIFT_LEFT
        run_test(4'hC, 4'h0, 3'h6, 4'h8, 27);

        // OBJ_ALU_028 | SHIFT_RIGHT
        run_test(4'h0, 4'h0, 3'h7, 4'h0, 28);

        // OBJ_ALU_029 | SHIFT_RIGHT
        run_test(4'h5, 4'h0, 3'h7, 4'h2, 29);

        // OBJ_ALU_001 | ADD
        run_test(4'h5, 4'h3, 3'h0, 4'h8, 30);

        // OBJ_ALU_002 | SUB
        run_test(4'hA, 4'h4, 3'h1, 4'h6, 31);

        // OBJ_ALU_003 | AND
        run_test(4'hC, 4'hA, 3'h2, 4'h8, 32);

        // OBJ_ALU_004 | OR
        run_test(4'h7, 4'h9, 3'h3, 4'hF, 33);

        // OBJ_ALU_005 | XOR
        run_test(4'h6, 4'h5, 3'h4, 4'h3, 34);

        // OBJ_ALU_006 | NOT
        run_test(4'h9, 4'h0, 3'h5, 4'h6, 35);

        // OBJ_ALU_007 | SHIFT_LEFT
        run_test(4'h3, 4'h0, 3'h6, 4'h6, 36);

        // OBJ_ALU_008 | SHIFT_RIGHT
        run_test(4'hC, 4'h0, 3'h7, 4'h6, 37);

        // OBJ_ALU_009 | ADD
        run_test(4'h0, 4'h0, 3'h0, 4'h0, 38);

        // OBJ_ALU_010 | ADD
        run_test(4'hF, 4'hF, 3'h0, 4'hE, 39);

        // OBJ_ALU_011 | ADD
        run_test(4'hA, 4'h9, 3'h0, 4'h3, 40);

        // OBJ_ALU_012 | SUB
        run_test(4'h7, 4'h7, 3'h1, 4'h0, 41);

        // OBJ_ALU_013 | SUB
        run_test(4'hC, 4'h0, 3'h1, 4'hC, 42);

        // OBJ_ALU_014 | SUB
        run_test(4'h2, 4'h5, 3'h1, 4'hD, 43);

        // OBJ_ALU_015 | AND
        run_test(4'h0, 4'h5, 3'h2, 4'h0, 44);

        // OBJ_ALU_016 | AND
        run_test(4'hF, 4'hC, 3'h2, 4'hC, 45);

        // OBJ_ALU_017 | AND
        run_test(4'hA, 4'h5, 3'h2, 4'h0, 46);

        // OBJ_ALU_018 | OR
        run_test(4'h0, 4'h8, 3'h3, 4'h8, 47);

        // OBJ_ALU_019 | OR
        run_test(4'hF, 4'hA, 3'h3, 4'hF, 48);

        // OBJ_ALU_020 | OR
        run_test(4'hA, 4'h5, 3'h3, 4'hF, 49);

        // OBJ_ALU_021 | XOR
        run_test(4'h8, 4'h8, 3'h4, 4'h0, 50);

        // OBJ_ALU_022 | XOR
        run_test(4'hF, 4'h0, 3'h4, 4'hF, 51);

        // OBJ_ALU_023 | NOT
        run_test(4'h0, 4'h0, 3'h5, 4'hF, 52);

        // OBJ_ALU_024 | NOT
        run_test(4'hF, 4'h0, 3'h5, 4'h0, 53);

        // OBJ_ALU_025 | NOT
        run_test(4'hA, 4'h0, 3'h5, 4'h5, 54);

        // OBJ_ALU_026 | SHIFT_LEFT
        run_test(4'h0, 4'h0, 3'h6, 4'h0, 55);

        // OBJ_ALU_027 | SHIFT_LEFT
        run_test(4'hC, 4'h0, 3'h6, 4'h8, 56);

        // OBJ_ALU_028 | SHIFT_RIGHT
        run_test(4'h0, 4'h0, 3'h7, 4'h0, 57);

        // OBJ_ALU_029 | SHIFT_RIGHT
        run_test(4'h5, 4'h0, 3'h7, 4'h2, 58);

        $display("----------------------------------------");
        $display("Generated ALU verification summary");
        $display("PASS = %0d", pass_count);
        $display("FAIL = %0d", fail_count);
        $display("TOTAL = %0d", pass_count + fail_count);
        $display("----------------------------------------");

        if (fail_count == 0)
            $display("TESTBENCH RESULT: PASS");
        else
            $display("TESTBENCH RESULT: FAIL");

        $finish;
    end

endmodule
