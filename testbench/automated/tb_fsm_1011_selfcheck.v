`timescale 1ns/1ps

module tb_fsm_1011_selfcheck;

    reg clk;
    reg rst;
    reg din;

    wire detected;

    integer total_tests;
    integer passed_tests;
    integer failed_tests;

    // ---------------------------------------------------------
    // DUT
    // ---------------------------------------------------------
    fsm_1011 dut (
        .clk(clk),
        .rst(rst),
        .din(din),
        .detected(detected)
    );

    // ---------------------------------------------------------
    // Clock generation
    // 10 ns clock period
    // ---------------------------------------------------------
    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;
    end


    // ---------------------------------------------------------
    // Reset task
    //
    // fsm_1011 uses synchronous active-high reset.
    // ---------------------------------------------------------
    task reset_dut;
        begin
            @(negedge clk);

            rst = 1'b1;
            din = 1'b0;

            // Reset is sampled at rising edge.
            @(posedge clk);
            #1;

            @(negedge clk);

            rst = 1'b0;
            din = 1'b0;

            #1;
        end
    endtask


    // ---------------------------------------------------------
    // Apply one input bit and check Mealy output.
    //
    // Input is applied at negative edge.
    // detected is checked BEFORE the next positive edge.
    //
    // This is important because fsm_1011 is a Mealy FSM.
    // ---------------------------------------------------------
    task check_bit;

        input input_bit;
        input expected_detected;
        input [8*80-1:0] test_name;

        begin

            @(negedge clk);

            din = input_bit;

            // Allow combinational Mealy output to settle.
            #1;

            total_tests = total_tests + 1;

            if (detected === expected_detected) begin

                passed_tests = passed_tests + 1;

                $display(
                    "PASS | TEST=%0d | %0s | din=%b | expected=%b | actual=%b",
                    total_tests,
                    test_name,
                    din,
                    expected_detected,
                    detected
                );

            end
            else begin

                failed_tests = failed_tests + 1;

                $display(
                    "FAIL | TEST=%0d | %0s | din=%b | expected=%b | actual=%b",
                    total_tests,
                    test_name,
                    din,
                    expected_detected,
                    detected
                );

            end

            // Allow FSM to update its state.
            @(posedge clk);
            #1;

        end

    endtask


    // ---------------------------------------------------------
    // Main verification
    // ---------------------------------------------------------
    initial begin

        rst = 1'b0;
        din = 1'b0;

        total_tests  = 0;
        passed_tests = 0;
        failed_tests = 0;

        // Waveform
        $dumpfile("results/fsm/day16/fsm_1011_selfcheck.vcd");
        $dumpvars(0, tb_fsm_1011_selfcheck);


        // =====================================================
        // TEST GROUP 1
        // Basic 1011 detection
        // =====================================================

        $display("");
        $display("==============================================");
        $display("TEST GROUP 1 : BASIC 1011 SEQUENCE");
        $display("==============================================");

        reset_dut();

        // Sequence = 1 0 1 1
        //
        // Expected detected:
        // 1 -> 0
        // 0 -> 0
        // 1 -> 0
        // 1 -> 1

        check_bit(
            1'b1,
            1'b0,
            "Basic 1011 - bit 1"
        );

        check_bit(
            1'b0,
            1'b0,
            "Basic 1011 - bit 2"
        );

        check_bit(
            1'b1,
            1'b0,
            "Basic 1011 - bit 3"
        );

        check_bit(
            1'b1,
            1'b1,
            "Basic 1011 - sequence detected"
        );


        // =====================================================
        // TEST GROUP 2
        // Non-matching sequence
        // =====================================================

        $display("");
        $display("==============================================");
        $display("TEST GROUP 2 : NON-MATCHING SEQUENCE 1000");
        $display("==============================================");

        reset_dut();

        // Sequence = 1 0 0 0
        // No detection should occur.

        check_bit(
            1'b1,
            1'b0,
            "Non-match 1000 - bit 1"
        );

        check_bit(
            1'b0,
            1'b0,
            "Non-match 1000 - bit 2"
        );

        check_bit(
            1'b0,
            1'b0,
            "Non-match 1000 - bit 3"
        );

        check_bit(
            1'b0,
            1'b0,
            "Non-match 1000 - bit 4"
        );


        // =====================================================
        // TEST GROUP 3
        // Overlapping sequence verification
        //
        // Sequence:
        // 1 0 1 1 0 1 1
        //
        // First  1011 = bits 1-4
        // Second 1011 = bits 4-7
        // =====================================================

        $display("");
        $display("==============================================");
        $display("TEST GROUP 3 : OVERLAPPING 1011011");
        $display("==============================================");

        reset_dut();

        check_bit(
            1'b1,
            1'b0,
            "Overlap 1011011 - bit 1"
        );

        check_bit(
            1'b0,
            1'b0,
            "Overlap 1011011 - bit 2"
        );

        check_bit(
            1'b1,
            1'b0,
            "Overlap 1011011 - bit 3"
        );

        // First 1011 detected.
        check_bit(
            1'b1,
            1'b1,
            "Overlap 1011011 - first detection"
        );

        check_bit(
            1'b0,
            1'b0,
            "Overlap 1011011 - bit 5"
        );

        check_bit(
            1'b1,
            1'b0,
            "Overlap 1011011 - bit 6"
        );

        // Second overlapping 1011 detected.
        check_bit(
            1'b1,
            1'b1,
            "Overlap 1011011 - second detection"
        );


        // -----------------------------------------------------
        // FINAL SUMMARY
        // -----------------------------------------------------

        $display("");
        $display("==============================================");
        $display("FSM 1011 SELF-CHECKING VERIFICATION SUMMARY");
        $display("==============================================");

        // Standard machine-readable fields used by Python.
        $display("TOTAL TESTS: %0d", total_tests);
        $display("PASSED TESTS: %0d", passed_tests);
        $display("FAILED TESTS: %0d", failed_tests);

        // Backward-compatible CHECK fields.
        $display("TOTAL CHECKS = %0d", total_tests);
        $display("PASSED CHECKS = %0d", passed_tests);
        $display("FAILED CHECKS = %0d", failed_tests);

        if (failed_tests == 0) begin

            $display("VERIFICATION STATUS: PASS");
            $display("DAY 16 FSM VERIFICATION PASS");

        end
        else begin

            $display("VERIFICATION STATUS: FAIL");
            $display("DAY 16 FSM VERIFICATION FAIL");

        end

        $display("==============================================");
        $display("");

        #10;

        $finish;

    end

endmodule
