`timescale 1ns/1ps

// ============================================================
// DAY 20 - FIFO MANUAL BASELINE TESTBENCH
//
// Project:
// AI-Driven RTL Test Generation,
// Coverage Analysis and Verification
//
// DUT:
// rtl/fifo.v
//
// FIFO configuration:
// DATA_WIDTH = 8
// DEPTH      = 4
// ADDR_WIDTH = 2
//
// Day 20 objective:
// Fixed hand-written/manual baseline for later comparison
// against random and AI-guided verification methods.
//
// Generated files:
// results/fifo/day20/manual_trace.csv
// results/fifo/day20/manual.vcd
// ============================================================

module tb_fifo_day20_manual;

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
    // FILE / COUNTERS
    // ========================================================

    integer trace_file;

    integer total_checks;
    integer passed_checks;
    integer failed_checks;


    // ========================================================
    // INTERNAL FIFO SNAPSHOTS
    // ========================================================

    reg [2:0] count_before;
    reg [1:0] write_ptr_before;
    reg [1:0] read_ptr_before;


    // ========================================================
    // DUT
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
    // CLOCK
    // ========================================================

    initial begin

        clk = 1'b0;

        forever begin
            #5 clk = ~clk;
        end

    end


    // ========================================================
    // TRACE LOGGER
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
    // CHECK SINGLE-BIT VALUE
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
    // CHECK FIFO COUNT
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
    // RESET FIFO
    // ========================================================

    task reset_fifo;

        begin

            @(negedge clk);

            count_before = dut.count;
            write_ptr_before = dut.write_ptr;
            read_ptr_before = dut.read_ptr;

            rst = 1'b1;
            wr_en = 1'b0;
            rd_en = 1'b0;
            data_in = 8'h00;

            @(posedge clk);

            #1;

            log_cycle(
                1'b1,
                1'b0,
                1'b0
            );

            @(negedge clk);

            rst = 1'b0;
            wr_en = 1'b0;
            rd_en = 1'b0;

        end

    endtask


    // ========================================================
    // IDLE FIFO
    // ========================================================

    task idle_fifo;

        begin

            @(negedge clk);

            count_before = dut.count;
            write_ptr_before = dut.write_ptr;
            read_ptr_before = dut.read_ptr;

            rst = 1'b0;
            wr_en = 1'b0;
            rd_en = 1'b0;

            @(posedge clk);

            #1;

            log_cycle(
                1'b0,
                1'b0,
                1'b0
            );

        end

    endtask


    // ========================================================
    // WRITE FIFO
    // ========================================================

    task write_fifo;

        input [7:0] value;

        begin

            @(negedge clk);

            count_before = dut.count;
            write_ptr_before = dut.write_ptr;
            read_ptr_before = dut.read_ptr;

            rst = 1'b0;
            wr_en = 1'b1;
            rd_en = 1'b0;
            data_in = value;

            @(posedge clk);

            #1;

            log_cycle(
                1'b0,
                1'b1,
                1'b0
            );

            @(negedge clk);

            wr_en = 1'b0;

        end

    endtask


    // ========================================================
    // READ FIFO AND CHECK DATA
    // ========================================================

    task read_fifo;

        input [7:0] expected;

        begin

            @(negedge clk);

            count_before = dut.count;
            write_ptr_before = dut.write_ptr;
            read_ptr_before = dut.read_ptr;

            rst = 1'b0;
            wr_en = 1'b0;
            rd_en = 1'b1;

            @(posedge clk);

            #1;

            total_checks = total_checks + 1;

            if (data_out === expected) begin

                passed_checks = passed_checks + 1;

                $display(
                    "CHECK_PASS : FIFO READ DATA actual=%02h expected=%02h",
                    data_out,
                    expected
                );

            end
            else begin

                failed_checks = failed_checks + 1;

                $display(
                    "CHECK_FAIL : FIFO READ DATA actual=%02h expected=%02h",
                    data_out,
                    expected
                );

            end

            log_cycle(
                1'b0,
                1'b0,
                1'b1
            );

            @(negedge clk);

            rd_en = 1'b0;

        end

    endtask


    // ========================================================
    // SIMULTANEOUS WRITE + READ
    // ========================================================

    task simultaneous_fifo;

        input [7:0] write_value;
        input [7:0] expected_read;

        begin

            @(negedge clk);

            count_before = dut.count;
            write_ptr_before = dut.write_ptr;
            read_ptr_before = dut.read_ptr;

            rst = 1'b0;
            wr_en = 1'b1;
            rd_en = 1'b1;
            data_in = write_value;

            @(posedge clk);

            #1;

            total_checks = total_checks + 1;

            if (data_out === expected_read) begin

                passed_checks = passed_checks + 1;

                $display(
                    "CHECK_PASS : SIMULTANEOUS READ actual=%02h expected=%02h",
                    data_out,
                    expected_read
                );

            end
            else begin

                failed_checks = failed_checks + 1;

                $display(
                    "CHECK_FAIL : SIMULTANEOUS READ actual=%02h expected=%02h",
                    data_out,
                    expected_read
                );

            end

            log_cycle(
                1'b0,
                1'b1,
                1'b1
            );

            @(negedge clk);

            wr_en = 1'b0;
            rd_en = 1'b0;

        end

    endtask


    // ========================================================
    // MAIN MANUAL BASELINE
    // ========================================================

    initial begin

        // ----------------------------------------------------
        // INITIAL VALUES
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
        // VCD
        // ----------------------------------------------------

        $dumpfile(
            "results/fifo/day20/manual.vcd"
        );

        $dumpvars(
            0,
            tb_fifo_day20_manual
        );


        // ----------------------------------------------------
        // TRACE FILE
        // ----------------------------------------------------

        trace_file = $fopen(
            "results/fifo/day20/manual_trace.csv",
            "w"
        );


        if (trace_file == 0) begin

            $fatal(
                1,
                "Unable to open manual trace."
            );

        end


        // ----------------------------------------------------
        // CSV HEADER
        //
        // ONE complete string fixes your old
        // line 245 syntax error.
        // ----------------------------------------------------

        $fdisplay(
            trace_file,
            "rst,wr_en,rd_en,count_before,count_after,write_ptr_before,write_ptr_after,read_ptr_before,read_ptr_after,full,empty"
        );


        // ----------------------------------------------------
        // ALLOW CLOCK TO START
        // ----------------------------------------------------

        repeat (2) begin
            @(posedge clk);
        end


        $display("");
        $display("================================================");
        $display("DAY 20 FIFO MANUAL BASELINE");
        $display("================================================");


        // ====================================================
        // TEST 1 - RESET
        // ====================================================

        reset_fifo();

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
        // TEST 2 - IDLE
        // ====================================================

        idle_fifo();

        check_count(
            "COUNT AFTER IDLE",
            dut.count,
            3'd0
        );


        // ====================================================
        // TEST 3 - SINGLE WRITE
        // ====================================================

        write_fifo(
            8'hA1
        );

        check_bit(
            "NOT EMPTY AFTER WRITE",
            empty,
            1'b0
        );

        check_count(
            "COUNT AFTER ONE WRITE",
            dut.count,
            3'd1
        );


        // ====================================================
        // TEST 4 - SECOND WRITE
        // ====================================================

        write_fifo(
            8'hB2
        );

        check_count(
            "COUNT AFTER TWO WRITES",
            dut.count,
            3'd2
        );


        // ====================================================
        // TEST 5 - READ FIRST ENTRY
        // ====================================================

        read_fifo(
            8'hA1
        );

        check_count(
            "COUNT AFTER FIRST READ",
            dut.count,
            3'd1
        );


        // ====================================================
        // TEST 6 - SIMULTANEOUS WRITE / READ
        //
        // Existing entry = B2
        // New entry      = C3
        // Read result    = B2
        // Count remains  = 1
        // ====================================================

        simultaneous_fifo(
            8'hC3,
            8'hB2
        );

        check_count(
            "COUNT AFTER SIMULTANEOUS OPERATION",
            dut.count,
            3'd1
        );


        // ====================================================
        // TEST 7 - READ C3
        // ====================================================

        read_fifo(
            8'hC3
        );

        check_bit(
            "EMPTY AFTER C3 READ",
            empty,
            1'b1
        );


        // ====================================================
        // TEST 8 - RESET BEFORE FULL / WRAP TEST
        // ====================================================

        reset_fifo();


        // ====================================================
        // TEST 9 - FILL FIFO
        //
        // Writing four elements also exercises write-pointer
        // wraparound in a depth-4 FIFO.
        // ====================================================

        write_fifo(
            8'h11
        );

        write_fifo(
            8'h22
        );

        write_fifo(
            8'h33
        );

        write_fifo(
            8'h44
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
        // TEST 10 - WRITE WHILE FULL
        // ====================================================

        write_fifo(
            8'h55
        );

        check_bit(
            "FULL REMAINS ASSERTED",
            full,
            1'b1
        );

        check_count(
            "COUNT UNCHANGED AFTER FULL WRITE",
            dut.count,
            3'd4
        );


        // ====================================================
        // TEST 11 - DRAIN FIFO
        //
        // Four reads also exercise read-pointer wraparound.
        // ====================================================

        read_fifo(
            8'h11
        );

        read_fifo(
            8'h22
        );

        read_fifo(
            8'h33
        );

        read_fifo(
            8'h44
        );


        check_bit(
            "EMPTY AFTER DRAIN",
            empty,
            1'b1
        );

        check_count(
            "COUNT AFTER DRAIN",
            dut.count,
            3'd0
        );


        // ====================================================
        // TEST 12 - READ WHILE EMPTY
        // ====================================================

        @(negedge clk);

        count_before = dut.count;
        write_ptr_before = dut.write_ptr;
        read_ptr_before = dut.read_ptr;

        rst = 1'b0;
        wr_en = 1'b0;
        rd_en = 1'b1;

        @(posedge clk);

        #1;

        log_cycle(
            1'b0,
            1'b0,
            1'b1
        );

        check_bit(
            "EMPTY REMAINS ASSERTED AFTER EMPTY READ",
            empty,
            1'b1
        );

        check_count(
            "COUNT UNCHANGED AFTER EMPTY READ",
            dut.count,
            3'd0
        );

        @(negedge clk);

        rd_en = 1'b0;


        // ====================================================
        // FINAL SUMMARY
        // ====================================================

        $display("");
        $display("================================================");
        $display("DAY 20 FIFO MANUAL BASELINE SUMMARY");
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
            "METHOD        = MANUAL_DIRECTED"
        );

        $display("------------------------------------------------");


        if (failed_checks == 0) begin

            $display(
                "DAY 20 FIFO MANUAL BASELINE: PASS"
            );

        end
        else begin

            $display(
                "DAY 20 FIFO MANUAL BASELINE: FAIL"
            );

        end


        $display("================================================");
        $display("");


        // ----------------------------------------------------
        // CLOSE TRACE
        // ----------------------------------------------------

        $fclose(
            trace_file
        );


        #10;

        $finish;

    end

endmodule
