`timescale 1ns/1ps

// ============================================================
// Day 17 - FSM Targeted Coverage Closure Testbench
//
// Project:
// AI-Driven RTL Test Generation,
// Coverage Analysis and Verification
//
// DUT:
// rtl/fsm_1011.v
//
// Baseline transition coverage:
// 6 / 8 = 75%
//
// Missing transitions:
// TR_005 : S2 --0--> S0
// TR_007 : S3 --0--> S2
//
// Targeted sequences:
// TR_005 -> 100
// TR_007 -> 1010
//
// Purpose:
// 1. Execute targeted sequences.
// 2. Exercise TR_005 and TR_007.
// 3. Verify source state, destination state and output.
// 4. Produce a trace file.
// 5. Produce a VCD waveform.
// 6. Report PASS / FAIL for coverage closure.
// ============================================================

module tb_fsm_day17_closure;

    // --------------------------------------------------------
    // DUT signals
    // --------------------------------------------------------
    reg clk;
    reg rst;
    reg din;

    wire detected;

    // --------------------------------------------------------
    // State encoding used by fsm_1011
    // --------------------------------------------------------
    localparam [1:0] S0 = 2'b00;
    localparam [1:0] S1 = 2'b01;
    localparam [1:0] S2 = 2'b10;
    localparam [1:0] S3 = 2'b11;

    // --------------------------------------------------------
    // Counters
    // --------------------------------------------------------
    integer total_target_checks;
    integer passed_target_checks;
    integer failed_target_checks;

    // --------------------------------------------------------
    // Trace file
    // --------------------------------------------------------
    integer trace_file;

    // --------------------------------------------------------
    // Temporary storage
    // --------------------------------------------------------
    reg [1:0] before_state;
    reg [1:0] after_state;
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

    // ========================================================
    // Clock generation
    // ========================================================
    initial begin
        clk = 1'b0;
    end

    always #5 clk = ~clk;


    // ========================================================
    // Reset task
    // ========================================================
    task reset_fsm;

        begin

            @(negedge clk);

            rst = 1'b1;
            din = 1'b0;

            @(posedge clk);
            #1;

            @(posedge clk);
            #1;

            @(negedge clk);

            rst = 1'b0;
            din = 1'b0;

            #1;

            $display("RESET_COMPLETE state=%b detected=%b",
                     dut.current_state,
                     detected);

        end

    endtask


    // ========================================================
    // Apply normal input bit
    //
    // Used for reaching the source state of a target
    // transition.
    // ========================================================
    task apply_bit;

        input input_bit;

        begin

            @(negedge clk);

            din = input_bit;

            #1;

            before_state = dut.current_state;
            observed_detect = detected;

            @(posedge clk);

            #1;

            after_state = dut.current_state;

            $display("TRACE from_state=%b input=%b to_state=%b detected=%b",
                     before_state,
                     input_bit,
                     after_state,
                     observed_detect);

            $fdisplay(trace_file,
                      "%b,%b,%b,%b,NORMAL",
                      before_state,
                      input_bit,
                      after_state,
                      observed_detect);

        end

    endtask


    // ========================================================
    // Apply and verify targeted transition
    // ========================================================
    task check_target_transition;

        input [31:0] target_number;
        input input_bit;
        input [1:0] expected_from_state;
        input [1:0] expected_to_state;
        input expected_detect;

        begin

            @(negedge clk);

            din = input_bit;

            #1;

            before_state = dut.current_state;
            observed_detect = detected;

            @(posedge clk);

            #1;

            after_state = dut.current_state;

            total_target_checks = total_target_checks + 1;

            if ((before_state === expected_from_state) &&
                (after_state === expected_to_state) &&
                (observed_detect === expected_detect)) begin

                passed_target_checks = passed_target_checks + 1;

                $display("TARGET_PASS target=%0d from=%b input=%b to=%b detected=%b",
                         target_number,
                         before_state,
                         input_bit,
                         after_state,
                         observed_detect);

                $fdisplay(trace_file,
                          "%b,%b,%b,%b,TARGET_PASS",
                          before_state,
                          input_bit,
                          after_state,
                          observed_detect);

            end
            else begin

                failed_target_checks = failed_target_checks + 1;

                $display("TARGET_FAIL target=%0d expected_from=%b actual_from=%b input=%b expected_to=%b actual_to=%b expected_detect=%b actual_detect=%b",
                         target_number,
                         expected_from_state,
                         before_state,
                         input_bit,
                         expected_to_state,
                         after_state,
                         expected_detect,
                         observed_detect);

                $fdisplay(trace_file,
                          "%b,%b,%b,%b,TARGET_FAIL",
                          before_state,
                          input_bit,
                          after_state,
                          observed_detect);

            end

        end

    endtask


    // ========================================================
    // Main targeted closure test
    // ========================================================
    initial begin

        // ----------------------------------------------------
        // Waveform file
        // ----------------------------------------------------
        $dumpfile("results/fsm/day17/fsm_targeted.vcd");

        $dumpvars(0, tb_fsm_day17_closure);

        // ----------------------------------------------------
        // Transition trace
        // ----------------------------------------------------
        trace_file = $fopen(
            "results/fsm/day17/fsm_targeted_trace.csv",
            "w"
        );

        if (trace_file == 0) begin

            $display("ERROR: Could not open targeted FSM trace file.");

            $fatal;

        end

        $fdisplay(trace_file,
                  "from_state,input,to_state,detected,result");

        // ----------------------------------------------------
        // Initialize
        // ----------------------------------------------------
        total_target_checks  = 0;
        passed_target_checks = 0;
        failed_target_checks = 0;

        rst = 1'b1;
        din = 1'b0;

        #2;


        // ====================================================
        // TARGET 1
        //
        // Missing transition:
        //
        // TR_005
        // S2 --0--> S0
        //
        // Shortest sequence from reset:
        //
        // 1 0 0
        //
        // S0 --1--> S1
        // S1 --0--> S2
        // S2 --0--> S0  <-- TR_005
        // ====================================================

        $display("");
        $display("==================================================");
        $display("TARGET 1: TR_005");
        $display("Required transition: S2 --0--> S0");
        $display("Target sequence: 100");
        $display("==================================================");

        reset_fsm();

        // S0 --1--> S1
        apply_bit(1'b1);

        // S1 --0--> S2
        apply_bit(1'b0);

        // S2 --0--> S0 = TR_005
        check_target_transition(
            32'd5,
            1'b0,
            S2,
            S0,
            1'b0
        );


        // ====================================================
        // TARGET 2
        //
        // Missing transition:
        //
        // TR_007
        // S3 --0--> S2
        //
        // Shortest sequence from reset:
        //
        // 1 0 1 0
        //
        // S0 --1--> S1
        // S1 --0--> S2
        // S2 --1--> S3
        // S3 --0--> S2  <-- TR_007
        // ====================================================

        $display("");
        $display("==================================================");
        $display("TARGET 2: TR_007");
        $display("Required transition: S3 --0--> S2");
        $display("Target sequence: 1010");
        $display("==================================================");

        reset_fsm();

        // S0 --1--> S1
        apply_bit(1'b1);

        // S1 --0--> S2
        apply_bit(1'b0);

        // S2 --1--> S3
        apply_bit(1'b1);

        // S3 --0--> S2 = TR_007
        check_target_transition(
            32'd7,
            1'b0,
            S3,
            S2,
            1'b0
        );


        // ====================================================
        // Final results
        // ====================================================

        $display("");
        $display("==================================================");
        $display("DAY 17 FSM TARGETED CLOSURE SUMMARY");
        $display("==================================================");

        $display("TOTAL_TARGET_CHECKS  = %0d",
                 total_target_checks);

        $display("PASSED_TARGET_CHECKS = %0d",
                 passed_target_checks);

        $display("FAILED_TARGET_CHECKS = %0d",
                 failed_target_checks);

        $display("--------------------------------------------------");

        if ((failed_target_checks == 0) &&
            (passed_target_checks == 2)) begin

            $display("TR_005_STATUS = COVERED");
            $display("TR_007_STATUS = COVERED");
            $display("FSM_DAY17_CLOSURE: PASS");

        end
        else begin

            if (passed_target_checks < 2) begin
                $display("WARNING: One or more target transitions were not covered.");
            end

            $display("FSM_DAY17_CLOSURE: FAIL");

        end

        $display("==================================================");
        $display("");

        // ----------------------------------------------------
        // Close output file
        // ----------------------------------------------------
        $fclose(trace_file);

        #10;

        $finish;

    end

endmodule
