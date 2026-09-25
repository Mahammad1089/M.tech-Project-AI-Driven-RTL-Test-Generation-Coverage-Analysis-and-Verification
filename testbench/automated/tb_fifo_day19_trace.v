`timescale 1ns/1ps

// ============================================================
// Day 19 - FIFO Baseline Trace Testbench
//
// DUT:
// rtl/fifo.v
//
// Configuration:
// DATA_WIDTH = 8
// DEPTH      = 4
// ADDR_WIDTH = 2
//
// Purpose:
// 1. Verify deterministic FIFO operation.
// 2. Generate a machine-readable execution trace.
// 3. Exercise reset, write, read, full, empty,
//    blocked operations, wrap-around and simultaneous R/W.
// 4. Produce a VCD waveform.
// 5. Produce a PASS/FAIL simulation log.
//
// Output files:
// results/fifo/day19/fifo_day19.vcd
// results/fifo/day19/fifo_baseline_trace.csv
// ============================================================

module tb_fifo_day19_trace;

    // ========================================================
    // DUT SIGNALS
    // ========================================================

    reg clk;
    reg rst;
    reg wr_en;
    reg rd_en;

    reg [7:0] data_in;

    wire [7:0] data_out;
    wire full;
    wire empty;


    // ========================================================
    // TRACE FILE
    // ========================================================

    integer trace_file;


    // ========================================================
    // CHECK COUNTERS
    // ========================================================

    integer total_checks;
    integer passed_checks;
    integer failed_checks;


    // ========================================================
    // INTERNAL DUT STATE SNAPSHOTS
    // ========================================================

    reg [2:0] count_before;

    reg [1:0] write_ptr_before;
    reg [1:0] read_ptr_before;


    // ========================================================
    // DUT INSTANTIATION
    // ========================================================

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


    // ========================================================
    // CLOCK GENERATION
    // ========================================================

    initial begin

        clk = 1'b0;

        forever begin
            #5 clk = ~clk;
        end

    end


    // ========================================================
    // TASK: WRITE ONE TRACE RECORD
    // ========================================================

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


    // ========================================================
    // TASK: APPLY ONE FIFO CLOCK CYCLE
    // ========================================================

    task apply_cycle;

        input reset_value;
        input write_value;
        input read_value;
        input [7:0] write_data;

        begin

            // Apply stimulus away from rising edge.
            @(negedge clk);

            count_before = dut.count;
            write_ptr_before = dut.write_ptr;
            read_ptr_before = dut.read_ptr;

            rst = reset_value;
            wr_en = write_value;
            rd_en = read_value;
            data_in = write_data;

            // FIFO updates here.
            @(posedge clk);

            // Allow nonblocking assignments to settle.
            #1;

            log_cycle(
                reset_value,
                write_value,
                read_value
            );

        end

    endtask


    // ========================================================
    // TASK: CHECK ONE-BIT VALUE
    // ========================================================

    task check_bit;

        input [8*80-1:0] check_name;
        input actual;
        input expected;

        begin

            total_checks = total_checks + 1;

            if (actual === expected) begin

                passed_checks = passed_checks + 1;

                $display(
                    "CHECK_PASS : %0s actual=%b expected=%b",
                    check_name,
                    actual,
                    expected
                );

            end
            else begin

                failed_checks = failed_checks + 1;

                $display(
                    "CHECK_FAIL : %0s actual=%b expected=%b",
                    check_name,
                    actual,
                    expected
                );

            end

        end

    endtask


    // ========================================================
    // TASK: CHECK 8-BIT DATA
    // ========================================================

    task check_data;

        input [8*80-1:0] check_name;
        input [7:0] actual;
        input [7:0] expected;

        begin

            total_checks = total_checks + 1;

            if (actual === expected) begin

                passed_checks = passed_checks + 1;

                $display(
                    "CHECK_PASS : %0s actual=%h expected=%h",
                    check_name,
                    actual,
                    expected
                );

            end
            else begin

                failed_checks = failed_checks + 1;

                $display(
                    "CHECK_FAIL : %0s actual=%h expected=%h",
                    check_name,
                    actual,
                    expected
                );

            end

        end

    endtask


    // ========================================================
    // TASK: CHECK FIFO COUNT
    // ========================================================

    task check_count;

        input [8*80-1:0] check_name;
        input [2:0] actual;
        input [2:0] expected;

        begin

            total_checks = total_checks + 1;

            if (actual === expected) begin

                passed_checks = passed_checks + 1;

                $display(
                    "CHECK_PASS : %0s actual=%0d expected=%0d",
                    check_name,
                    actual,
                    expected
                );

            end
            else begin

                failed_checks = failed_checks + 1;

                $display(
                    "CHECK_FAIL : %0s actual=%0d expected=%0d",
                    check_name,
                    actual,
                    expected
                );

            end

        end

    endtask


    // ========================================================
    // MAIN TEST
    // ========================================================

    initial begin

        // ----------------------------------------------------
        // Initial values
        // ----------------------------------------------------

        rst = 1'b1;
        wr_en = 1'b0;
        rd_en = 1'b0;
        data_in = 8'h00;

        total_checks = 0;
        passed_checks = 0;
        failed_checks = 0;

        count_before = 3'd0;
        write_ptr_before = 2'd0;
        read_ptr_before = 2'd0;


        // ----------------------------------------------------
        // Create VCD
        // ----------------------------------------------------

        $dumpfile(
            "results/fifo/day19/fifo_day19.vcd"
        );

        $dumpvars(
            0,
            tb_fifo_day19_trace
        );


        // ----------------------------------------------------
        // Create execution trace
        // ----------------------------------------------------

        trace_file = $fopen(
            "results/fifo/day19/fifo_baseline_trace.csv",
            "w"
        );

        if (trace_file == 0) begin

            $display(
                "ERROR: Unable to open FIFO trace."
            );

            $fatal;

        end


        // ----------------------------------------------------
        // IMPORTANT:
        // Use ONE complete Verilog string.
        // This corrects your line 315 syntax error.
        // ----------------------------------------------------

        $fdisplay(
            trace_file,
            "rst,wr_en,rd_en,count_before,count_after,write_ptr_before,write_ptr_after,read_ptr_before,read_ptr_after,full,empty"
        );


        // ====================================================
        // RESET
        // ====================================================

        // Establish a known reset state first.
        repeat (2) begin
            @(posedge clk);
            #1;
        end

        // Trace one deterministic reset cycle.
        apply_cycle(
            1'b1,
            1'b0,
            1'b0,
            8'h00
        );

        check_bit(
            "EMPTY AFTER RESET",
            empty,
            1'b1
        );

        check_bit(
            "NOT FULL AFTER RESET",
            full,
            1'b0
        );

        check_count(
            "COUNT AFTER RESET",
            dut.count,
            3'd0
        );


        // ====================================================
        // RELEASE RESET
        // ====================================================

        apply_cycle(
            1'b0,
            1'b0,
            1'b0,
            8'h00
        );


        // ====================================================
        // WRITE FIRST ENTRY
        // ====================================================

        apply_cycle(
            1'b0,
            1'b1,
            1'b0,
            8'hA1
        );

        check_bit(
            "NOT EMPTY AFTER FIRST WRITE",
            empty,
            1'b0
        );

        check_count(
            "COUNT AFTER FIRST WRITE",
            dut.count,
            3'd1
        );


        // ====================================================
        // ADD SECOND ENTRY
        // ====================================================

        apply_cycle(
            1'b0,
            1'b1,
            1'b0,
            8'hB2
        );

        check_count(
            "COUNT AFTER SECOND WRITE",
            dut.count,
            3'd2
        );


        // ====================================================
        // ADD THIRD ENTRY
        // ====================================================

        apply_cycle(
            1'b0,
            1'b1,
            1'b0,
            8'hC3
        );

        check_count(
            "COUNT AFTER THIRD WRITE",
            dut.count,
            3'd3
        );


        // ====================================================
        // ADD FOURTH ENTRY -> FIFO FULL
        // ====================================================

        apply_cycle(
            1'b0,
            1'b1,
            1'b0,
            8'hD4
        );

        check_bit(
            "FULL AFTER FOUR WRITES",
            full,
            1'b1
        );

        check_count(
            "COUNT WHEN FULL",
            dut.count,
            3'd4
        );


        // ====================================================
        // WRITE WHILE FULL
        //
        // This write should be blocked.
        // ====================================================

        apply_cycle(
            1'b0,
            1'b1,
            1'b0,
            8'hE5
        );

        check_bit(
            "FULL REMAINS ASSERTED",
            full,
            1'b1
        );

        check_count(
            "COUNT UNCHANGED WHEN WRITE BLOCKED",
            dut.count,
            3'd4
        );


        // ====================================================
        // READ ENTRY 1
        // ====================================================

        apply_cycle(
            1'b0,
            1'b0,
            1'b1,
            8'h00
        );

        check_data(
            "FIFO READ DATA A1",
            data_out,
            8'hA1
        );


        // ====================================================
        // READ ENTRY 2
        // ====================================================

        apply_cycle(
            1'b0,
            1'b0,
            1'b1,
            8'h00
        );

        check_data(
            "FIFO READ DATA B2",
            data_out,
            8'hB2
        );


        // ====================================================
        // READ ENTRY 3
        // ====================================================

        apply_cycle(
            1'b0,
            1'b0,
            1'b1,
            8'h00
        );

        check_data(
            "FIFO READ DATA C3",
            data_out,
            8'hC3
        );


        // ====================================================
        // READ ENTRY 4
        // ====================================================

        apply_cycle(
            1'b0,
            1'b0,
            1'b1,
            8'h00
        );

        check_data(
            "FIFO READ DATA D4",
            data_out,
            8'hD4
        );

        check_bit(
            "EMPTY AFTER ALL READS",
            empty,
            1'b1
        );

        check_count(
            "COUNT AFTER ALL READS",
            dut.count,
            3'd0
        );


        // ====================================================
        // READ WHILE EMPTY
        //
        // Read must be blocked.
        // ====================================================

        apply_cycle(
            1'b0,
            1'b0,
            1'b1,
            8'h00
        );

        check_bit(
            "EMPTY REMAINS ASSERTED",
            empty,
            1'b1
        );

        check_count(
            "COUNT UNCHANGED WHEN READ BLOCKED",
            dut.count,
            3'd0
        );


        // ====================================================
        // POINTER WRAP-AROUND EXERCISE
        // ====================================================

        apply_cycle(
            1'b0,
            1'b1,
            1'b0,
            8'h55
        );

        apply_cycle(
            1'b0,
            1'b1,
            1'b0,
            8'h66
        );

        apply_cycle(
            1'b0,
            1'b0,
            1'b1,
            8'h00
        );

        check_data(
            "WRAP TEST READ DATA 55",
            data_out,
            8'h55
        );


        // ====================================================
        // SIMULTANEOUS READ AND WRITE
        //
        // Existing FIFO entry = 66
        // New write = 77
        //
        // Expected:
        // read returns 66
        // count remains unchanged
        // ====================================================

        apply_cycle(
            1'b0,
            1'b1,
            1'b1,
            8'h77
        );

        check_data(
            "SIMULTANEOUS READ DATA",
            data_out,
            8'h66
        );

        check_count(
            "COUNT AFTER SIMULTANEOUS READ WRITE",
            dut.count,
            3'd1
        );


        // ====================================================
        // READ NEW ENTRY
        // ====================================================

        apply_cycle(
            1'b0,
            1'b0,
            1'b1,
            8'h00
        );

        check_data(
            "FIFO READ DATA 77",
            data_out,
            8'h77
        );

        check_bit(
            "EMPTY AFTER SIMULTANEOUS TEST",
            empty,
            1'b1
        );


        // ====================================================
        // FINAL SUMMARY
        // ====================================================

        $display("");
        $display("================================================");
        $display("DAY 19 FIFO BASELINE TRACE SUMMARY");
        $display("================================================");

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

        $display(
            "TRACE_FILE    = results/fifo/day19/fifo_baseline_trace.csv"
        );

        $display(
            "VCD_FILE      = results/fifo/day19/fifo_day19.vcd"
        );

        $display("------------------------------------------------");

        if (failed_checks == 0) begin

            $display(
                "DAY 19 FIFO BASELINE TRACE: PASS"
            );

        end
        else begin

            $display(
                "DAY 19 FIFO BASELINE TRACE: FAIL"
            );

        end

        $display("================================================");
        $display("");


        // ----------------------------------------------------
        // Close trace
        // ----------------------------------------------------

        $fclose(
            trace_file
        );

        #10;

        $finish;

    end

endmodule
