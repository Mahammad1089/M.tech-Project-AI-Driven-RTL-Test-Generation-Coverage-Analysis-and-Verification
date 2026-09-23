`timescale 1ns/1ps

// ============================================================
// Day 17 - FSM Baseline Trace Testbench
// Project:
// AI-Driven RTL Test Generation, Coverage Analysis
// and Verification
//
// DUT:
// rtl/fsm_1011.v
//
// Purpose:
// 1. Run baseline verification for the 1011 sequence detector
// 2. Check detection output automatically
// 3. Record FSM state transitions
// 4. Generate CSV execution trace
// 5. Generate VCD waveform
// 6. Produce PASS / FAIL summary
//
// Generated files:
// results/fsm/day17/fsm_day17_baseline.vcd
// results/fsm/day17/fsm_execution_trace.csv
// ============================================================

module tb_fsm_day17_trace;

    // --------------------------------------------------------
    // DUT signals
    // --------------------------------------------------------
    reg clk;
    reg rst;
    reg din;

    wire detected;

    // --------------------------------------------------------
    // Testbench counters
    // --------------------------------------------------------
    integer total_checks;
    integer passed_checks;
    integer failed_checks;

    // --------------------------------------------------------
    // Trace file
    // --------------------------------------------------------
    integer trace_file;

    // --------------------------------------------------------
    // Temporary variables
    // --------------------------------------------------------
    reg [1:0] previous_state;
    reg [1:0] next_state;
    reg observed_detect;

    // --------------------------------------------------------
    // DUT instantiation
    // --------------------------------------------------------
    fsm_1011 dut (
        .clk      (clk),
        .rst      (rst),
        .din      (din),
        .detected (detected)
    );

    // --------------------------------------------------------
    // Clock generation
    //
    // Clock period = 10 ns
    // --------------------------------------------------------
    initial begin
        clk = 1'b0;
    end

    always #5 clk = ~clk;

    // ========================================================
    // TASK: Apply one input bit and check detector output
    //
    // input_bit      = bit applied to FSM
    // expected_detect = expected detector output before the
    //                   FSM advances to the next state
    // ========================================================
    task apply_and_check;

        input input_bit;
        input expected_detect;

        begin

            // ------------------------------------------------
            // Change input away from the positive clock edge
            // ------------------------------------------------
            @(negedge clk);

            din = input_bit;

            // Allow combinational logic to settle
            #1;

            // Save current state before state advances
            previous_state = dut.current_state;

            // Save detector value corresponding to this input
            observed_detect = detected;

            // ------------------------------------------------
            // Functional output check
            // ------------------------------------------------
            total_checks = total_checks + 1;

            if (observed_detect === expected_detect) begin

                passed_checks = passed_checks + 1;

                $display(
                    "CHECK_PASS state=%b din=%b expected=%b detected=%b",
                    previous_state,
                    input_bit,
                    expected_detect,
                    observed_detect
                );

            end
            else begin

                failed_checks = failed_checks + 1;

                $display(
                    "CHECK_FAIL state=%b din=%b expected=%b actual=%b",
                    previous_state,
                    input_bit,
                    expected_detect,
                    observed_detect
                );

            end

            // ------------------------------------------------
            // State advances here
            // ------------------------------------------------
            @(posedge clk);

            // Allow nonblocking assignments inside DUT
            // to update current_state
            #1;

            next_state = dut.current_state;

            // ------------------------------------------------
            // Store state transition in CSV
            // ------------------------------------------------
            $fdisplay(
                trace_file,
                "%b,%b,%b,%b",
                previous_state,
                input_bit,
                next_state,
                observed_detect
            );

            $display(
                "TRACE from_state=%b input=%b to_state=%b detected=%b",
                previous_state,
                input_bit,
                next_state,
                observed_detect
            );

        end

    endtask


    // ========================================================
    // TASK: Reset FSM
    // ========================================================
    task reset_fsm;

        begin

            $display("");
            $display("--------------------------------------------------");
            $display("Applying FSM reset");
            $display("--------------------------------------------------");

            @(negedge clk);

            rst = 1'b1;
            din = 1'b0;

            // Keep reset active across two clock edges
            @(posedge clk);
            #1;

            @(posedge clk);
            #1;

            @(negedge clk);

            rst = 1'b0;
            din = 1'b0;

            #1;

            $display(
                "RESET_COMPLETE current_state=%b detected=%b",
                dut.current_state,
                detected
            );

            $display("");

        end

    endtask


    // ========================================================
    // Main test sequence
    // ========================================================
    initial begin

        // ----------------------------------------------------
        // VCD waveform
        // ----------------------------------------------------
        $dumpfile(
            "results/fsm/day17/fsm_day17_baseline.vcd"
        );

        $dumpvars(
            0,
            tb_fsm_day17_trace
        );

        // ----------------------------------------------------
        // Open FSM execution trace CSV
        // ----------------------------------------------------
        trace_file = $fopen(
            "results/fsm/day17/fsm_execution_trace.csv",
            "w"
        );

        if (trace_file == 0) begin

            $display(
                "ERROR: Could not open FSM trace file."
            );

            $fatal;

        end

        // CSV header
        $fdisplay(
            trace_file,
            "from_state,input,to_state,detected"
        );

        // ----------------------------------------------------
        // Initialize counters
        // ----------------------------------------------------
        total_checks  = 0;
        passed_checks = 0;
        failed_checks = 0;

        // ----------------------------------------------------
        // Initial signal values
        // ----------------------------------------------------
        rst = 1'b1;
        din = 1'b0;

        // Allow clock to start
        #2;

        // ====================================================
        // RESET TEST
        // ====================================================
        reset_fsm();


        // ====================================================
        // TEST 1
        //
        // Input sequence:
        // 1 0 1 1
        //
        // Expected sequence detection:
        // 0 0 0 1
        //
        // This is the primary 1011 detection test.
        // ====================================================

        $display("");
        $display("==================================================");
        $display("TEST 1: Basic 1011 sequence detection");
        $display("==================================================");

        apply_and_check(1'b1, 1'b0);
        apply_and_check(1'b0, 1'b0);
        apply_and_check(1'b1, 1'b0);
        apply_and_check(1'b1, 1'b1);


        // ====================================================
        // TEST 2
        //
        // Continue from previous detected sequence.
        //
        // Apply:
        // 0 1 1
        //
        // Because overlapping detection is supported,
        // the existing final '1' from 1011 can become the
        // beginning of another 1011.
        //
        // Effective stream:
        // 1 0 1 1 0 1 1
        //
        // Two occurrences of 1011 are present.
        // ====================================================

        $display("");
        $display("==================================================");
        $display("TEST 2: Overlapping 1011 detection");
        $display("==================================================");

        apply_and_check(1'b0, 1'b0);
        apply_and_check(1'b1, 1'b0);
        apply_and_check(1'b1, 1'b1);


        // ====================================================
        // TEST 3
        //
        // Reset before testing a non-detection sequence.
        // ====================================================

        reset_fsm();

        $display("");
        $display("==================================================");
        $display("TEST 3: Non-detection sequence 0000");
        $display("==================================================");

        apply_and_check(1'b0, 1'b0);
        apply_and_check(1'b0, 1'b0);
        apply_and_check(1'b0, 1'b0);
        apply_and_check(1'b0, 1'b0);


        // ====================================================
        // TEST 4
        //
        // Reset and test sequence containing leading noise.
        //
        // Input:
        // 1 1 0 1 1
        //
        // Last four bits contain:
        // 1 0 1 1
        //
        // Therefore detector must assert on final bit.
        // ====================================================

        reset_fsm();

        $display("");
        $display("==================================================");
        $display("TEST 4: Detection after leading input");
        $display("==================================================");

        apply_and_check(1'b1, 1'b0);
        apply_and_check(1'b1, 1'b0);
        apply_and_check(1'b0, 1'b0);
        apply_and_check(1'b1, 1'b0);
        apply_and_check(1'b1, 1'b1);


        // ====================================================
        // TEST 5
        //
        // Reset and exercise additional transitions.
        //
        // Input:
        // 0 1 0 1 1
        //
        // Final four useful bits:
        // 1 0 1 1
        // ====================================================

        reset_fsm();

        $display("");
        $display("==================================================");
        $display("TEST 5: 01011 sequence");
        $display("==================================================");

        apply_and_check(1'b0, 1'b0);
        apply_and_check(1'b1, 1'b0);
        apply_and_check(1'b0, 1'b0);
        apply_and_check(1'b1, 1'b0);
        apply_and_check(1'b1, 1'b1);


        // ====================================================
        // FINAL SUMMARY
        // ====================================================

        $display("");
        $display("==================================================");
        $display("DAY 17 FSM BASELINE SUMMARY");
        $display("==================================================");

        $display(
            "TOTAL_CHECKS  = %0d",
            total_checks
        );

        $display(
            "PASSED_CHECKS = %0d",
            passed_checks
        );

        $display(
            "FAILED_CHECKS = %0d",
            failed_checks
        );

        $display("--------------------------------------------------");

        if (failed_checks == 0) begin

            $display("FSM_DAY17_BASELINE: PASS");

        end
        else begin

            $display("FSM_DAY17_BASELINE: FAIL");

        end

        $display("==================================================");
        $display("");

        // ----------------------------------------------------
        // Close CSV file
        // ----------------------------------------------------
        $fclose(trace_file);

        // Give VCD a final timestamp
        #10;

        $finish;

    end

endmodule
