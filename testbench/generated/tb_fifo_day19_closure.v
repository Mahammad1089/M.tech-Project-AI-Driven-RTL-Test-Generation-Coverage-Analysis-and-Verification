`timescale 1ns/1ps

// ============================================================
// DAY 19 - FIFO TARGETED / CLOSURE TESTBENCH
//
// DUT:
// rtl/fifo.v
//
// FIFO configuration:
// DATA_WIDTH = 8
// DEPTH      = 4
// ADDR_WIDTH = 2
//
// Purpose:
// 1. Verify FIFO reset behavior.
// 2. Verify writes and reads.
// 3. Verify full state.
// 4. Verify write-when-full blocking.
// 5. Verify empty state.
// 6. Verify read-when-empty blocking.
// 7. Verify simultaneous read/write.
// 8. Exercise pointer wrap-around.
// 9. Generate targeted trace CSV.
// 10. Generate VCD waveform.
// ============================================================

module tb_fifo_day19_closure;

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
    // INTERNAL STATE SNAPSHOTS
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
    // TRACE ONE FIFO CLOCK CYCLE
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

        end

    endtask


    // ========================================================
    // APPLY IDLE CYCLE
    // ========================================================

    task idle_cycle;

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
    // WRITE BYTE
    // ========================================================

    task write_byte;

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
    // READ AND CHECK BYTE
    // ========================================================

    task read_and_check;

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
                    "CHECK_PASS : FIFO READ actual=%02h expected=%02h",
                    data_out,
                    expected
                );

            end
            else begin

                failed_checks = failed_checks + 1;

                $display(
                    "CHECK_FAIL : FIFO READ actual=%02h expected=%02h",
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
    // SIMULTANEOUS WRITE / READ
    // ========================================================

    task simultaneous_write_read;

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
    // CHECK ONE BIT
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
    // MAIN TEST
    // ========================================================

    initial begin

        // ----------------------------------------------------
        // INITIALIZATION
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
            "results/fifo/day19/fifo_day19_targeted.vcd"
        );

        $dumpvars(
            0,
            tb_fifo_day19_closure
        );


        // ----------------------------------------------------
        // OPEN TARGETED TRACE
        // ----------------------------------------------------

        trace_file = $fopen(
            "results/fifo/day19/fifo_targeted_trace.csv",
            "w"
        );


        if (trace_file == 0) begin

            $fatal(
                1,
                "Unable to open targeted trace."
            );

        end


        // ----------------------------------------------------
        // CSV HEADER
        //
        // IMPORTANT:
        // This is ONE complete string.
        // It fixes the syntax error at old line 392.
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


        // ====================================================
        // TEST 1 - RESET
        // ====================================================

        $display("");
        $display("================================================");
        $display("DAY 19 FIFO TARGETED / CLOSURE TEST");
        $display("================================================");

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

        idle_cycle();

        check_count(
            "COUNT AFTER IDLE",
            dut.count,
            3'd0
        );


        // ====================================================
        // TEST 3 - FILL FIFO
        // ====================================================

        write_byte(
            8'h11
        );

        check_bit(
            "NOT EMPTY AFTER FIRST WRITE",
            empty,
            1'b0
        );


        write_byte(
            8'h22
        );

        write_byte(
            8'h33
        );

        write_byte(
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
        // TEST 4 - WRITE WHEN FULL
        // ====================================================

        write_byte(
            8'hAA
        );

        check_bit(
            "FULL REMAINS ASSERTED",
            full,
            1'b1
        );

        check_count(
            "COUNT UNCHANGED WHEN FULL WRITE ATTEMPTED",
            dut.count,
            3'd4
        );


        // ====================================================
        // TEST 5 - FIRST READ
        // ====================================================

        read_and_check(
            8'h11
        );

        check_bit(
            "NOT FULL AFTER READ",
            full,
            1'b0
        );


        // ====================================================
        // TEST 6 - SIMULTANEOUS WRITE / READ
        //
        // Queue before operation:
        //
        // 22, 33, 44
        //
        // Read result = 22
        // Write value = 55
        //
        // Queue afterwards:
        //
        // 33, 44, 55
        // ====================================================

        simultaneous_write_read(
            8'h55,
            8'h22
        );

        check_count(
            "COUNT AFTER SIMULTANEOUS WRITE READ",
            dut.count,
            3'd3
        );


        // ====================================================
        // TEST 7 - DRAIN FIFO
        // ====================================================

        read_and_check(
            8'h33
        );

        read_and_check(
            8'h44
        );

        read_and_check(
            8'h55
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
        // TEST 8 - READ WHEN EMPTY
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
        // TEST 9 - POINTER WRAPAROUND
        // ====================================================

        write_byte(
            8'h66
        );

        write_byte(
            8'h77
        );

        read_and_check(
            8'h66
        );

        read_and_check(
            8'h77
        );


        check_bit(
            "EMPTY AFTER WRAP TEST",
            empty,
            1'b1
        );


        // ====================================================
        // FINAL SUMMARY
        // ====================================================

        $display("");
        $display("================================================");
        $display("DAY 19 FIFO TARGETED CLOSURE SUMMARY");
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

        $display("------------------------------------------------");


        if (failed_checks == 0) begin

            $display(
                "DAY 19 FIFO TARGETED CLOSURE: PASS"
            );

        end
        else begin

            $display(
                "DAY 19 FIFO TARGETED CLOSURE: FAIL"
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
