`timescale 1ns/1ps

module tb_alu_equivalence;

    reg  [3:0] a;
    reg  [3:0] b;
    reg  [2:0] sel;

    wire [3:0] y_original;
    wire [3:0] y_optimized;

    integer ai;
    integer bi;
    integer si;

    integer total_checks;
    integer passed_checks;
    integer failed_checks;

    alu original_dut (
        .a(a),
        .b(b),
        .sel(sel),
        .y(y_original)
    );

    alu_opt optimized_dut (
        .a(a),
        .b(b),
        .sel(sel),
        .y(y_optimized)
    );

    initial begin
        a = 0;
        b = 0;
        sel = 0;

        total_checks  = 0;
        passed_checks = 0;
        failed_checks = 0;

        $display("======================================");
        $display("DAY 25 - ALU EXHAUSTIVE EQUIVALENCE");
        $display("======================================");

        for (si = 0; si < 8; si = si + 1) begin
            for (ai = 0; ai < 16; ai = ai + 1) begin
                for (bi = 0; bi < 16; bi = bi + 1) begin

                    sel = si;
                    a   = ai;
                    b   = bi;

                    #1;

                    total_checks = total_checks + 1;

                    if (y_original === y_optimized) begin
                        passed_checks = passed_checks + 1;
                    end
                    else begin
                        failed_checks = failed_checks + 1;

                        $display(
                            "FAIL sel=%b a=%h b=%h original=%h optimized=%h",
                            sel, a, b, y_original, y_optimized
                        );
                    end
                end
            end
        end

        $display("--------------------------------------");
        $display("TOTAL CHECKS  : %0d", total_checks);
        $display("PASSED CHECKS : %0d", passed_checks);
        $display("FAILED CHECKS : %0d", failed_checks);
        $display("--------------------------------------");

        if (total_checks != 2048) begin
            $display("DAY 25 ALU EQUIVALENCE: FAIL");
            $fatal(1, "Unexpected number of test cases");
        end
        else if (failed_checks == 0) begin
            $display("DAY 25 ALU EQUIVALENCE: PASS");
        end
        else begin
            $display("DAY 25 ALU EQUIVALENCE: FAIL");
            $fatal(1, "Original and optimized ALUs differ");
        end

        $finish;
    end

endmodule
