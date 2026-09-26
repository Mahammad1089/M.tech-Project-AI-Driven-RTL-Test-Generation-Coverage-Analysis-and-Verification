`timescale 1ns/1ps

// ============================================================
// DAY 20 - FIFO RANDOM BASELINE TESTBENCH
//
// Project:
// AI-Driven RTL Test Generation,
// Coverage Analysis and Verification
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
// 1. Deterministic random FIFO baseline.
// 2. Fixed seed for repeatability.
// 3. Independent FIFO reference model.
// 4. Check count, full, empty and read data.
// 5. Generate functional-coverage trace.
// 6. Generate VCD waveform.
// 7. Provide Random baseline for Manual vs Random vs AI.
//
// IMPORTANT:
// Random stimulus is generated ONLY after negedge clk.
// This prevents an unmodelled operation from occurring
// before the intended positive clock edge.
// ============================================================

module tb_fifo_day20_random;

    // ========================================================
    // PARAMETERS
    // ========================================================

    parameter DATA_WIDTH = 8;
    parameter DEPTH      = 4;
    parameter ADDR_WIDTH = 2;

    parameter RANDOM_CYCLES = 40;


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
    // RESULT COUNTERS
    // ========================================================

    integer total_checks;
    integer passed_checks;
    integer failed_checks;

    integer cycle_number;


    // ========================================================
    // RANDOM GENERATOR
    // ========================================================

    integer random_seed;
    integer initial_random_seed;

    integer random_control;
    integer random_data;


    // ========================================================
    // DUT STATE BEFORE EACH OPERATION
    // ========================================================

    reg [2:0] count_before;
    reg [1:0] write_ptr_before;
    reg [1:0] read_ptr_before;


    // ========================================================
    // REFERENCE FIFO MODEL
    // ========================================================

    reg [7:0] model_mem [0:DEPTH-1];

    integer model_count;
    integer model_write_ptr;
    integer model_read_ptr;

    reg write_allowed;
    reg read_allowed;

    reg [7:0] expected_read_data;

    reg expected_full;
    reg expected_empty;


    // ========================================================
    // DUT INSTANTIATION
    // ========================================================

    fifo #(
        .DATA_WIDTH(DATA_WIDTH),
        .DEPTH(DEPTH),
        .ADDR_WIDTH(ADDR_WIDTH)
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
    // CHECK BIT
    // ========================================================

    task check_bit;

        input [8*80-1:0] check_name;
        input actual;
        input expected;

        begin

            total_checks = total_checks + 1;

            if (actual === expected) begin

                passed_checks = passed_checks + 1;

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
    // CHECK COUNT
    // ========================================================

    task check_count;

        input [8*80-1:0] check_name;
        input [2:0] actual;
        input integer expected;

        begin

            total_checks = total_checks + 1;

            if (actual === expected[2:0]) begin

                passed_checks = passed_checks + 1;

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
    // CHECK DATA
    // ========================================================

    task check_data;

        input [7:0] actual;
        input [7:0] expected;

        begin

            total_checks = total_checks + 1;

            if (actual === expected) begin

                passed_checks = passed_checks + 1;

            end
            else begin

                failed_checks = failed_checks + 1;

                $display(
                    "CHECK_FAIL : RANDOM FIFO READ cycle=%0d actual=%02h expected=%02h",
                    cycle_number,
                    actual,
                    expected
                );

            end

        end

    endtask


    // ========================================================
    // RESET DUT + REFERENCE MODEL
    // ========================================================

    task reset_fifo;

        begin

            // ------------------------------------------------
            // Apply reset only on falling edge.
            // ------------------------------------------------

            @(negedge clk);

            count_before = dut.count;
            write_ptr_before = dut.write_ptr;
            read_ptr_before = dut.read_ptr;

            rst = 1'b1;
            wr_en = 1'b0;
            rd_en = 1'b0;
            data_in = 8'h00;


            // ------------------------------------------------
            // Reset DUT.
            // ------------------------------------------------

            @(posedge clk);

            #1;


            // ------------------------------------------------
            // Reset software reference model.
            // ------------------------------------------------

            model_count = 0;
            model_write_ptr = 0;
            model_read_ptr = 0;

            model_mem[0] = 8'h00;
            model_mem[1] = 8'h00;
            model_mem[2] = 8'h00;
            model_mem[3] = 8'h00;


            // ------------------------------------------------
            // Log reset.
            // ------------------------------------------------

            log_cycle(
                1'b1,
                1'b0,
                1'b0
            );


            // ------------------------------------------------
            // Check reset state.
            // ------------------------------------------------

            check_count(
                "FIFO COUNT AFTER RESET",
                dut.count,
                0
            );

            check_bit(
                "FIFO FULL AFTER RESET",
                full,
                1'b0
            );

            check_bit(
                "FIFO EMPTY AFTER RESET",
                empty,
                1'b1
            );


            // ------------------------------------------------
            // Release reset away from positive edge.
            // ------------------------------------------------

            @(negedge clk);

            rst = 1'b0;
            wr_en = 1'b0;
            rd_en = 1'b0;

        end

    endtask


    // ========================================================
    // EXECUTE ONE RANDOM CYCLE
    // ========================================================

    task execute_random_cycle;

        begin

            // =================================================
            // IMPORTANT FIX
            //
            // Wait for falling edge FIRST.
            //
            // The old version generated stimulus before this
            // event control, which allowed an unintended
            // positive-edge FIFO operation to occur.
            // =================================================

            @(negedge clk);


            // ------------------------------------------------
            // Generate exactly ONE random transaction.
            // ------------------------------------------------

            random_control =
                $random(random_seed);

            random_data =
                $random(random_seed);


            wr_en =
                random_control[0];

            rd_en =
                random_control[1];

            data_in =
                random_data[7:0];


            // ------------------------------------------------
            // Snapshot DUT state before clock operation.
            // ------------------------------------------------

            count_before =
                dut.count;

            write_ptr_before =
                dut.write_ptr;

            read_ptr_before =
                dut.read_ptr;


            // ------------------------------------------------
            // Determine whether DUT should accept WRITE.
            //
            // A write is accepted only if:
            //
            // wr_en = 1
            // FIFO not full before clock edge
            // ------------------------------------------------

            if (
                (wr_en === 1'b1)
                &&
                (model_count < DEPTH)
            ) begin

                write_allowed = 1'b1;

            end
            else begin

                write_allowed = 1'b0;

            end


            // ------------------------------------------------
            // Determine whether DUT should accept READ.
            //
            // A read is accepted only if:
            //
            // rd_en = 1
            // FIFO not empty before clock edge
            // ------------------------------------------------

            if (
                (rd_en === 1'b1)
                &&
                (model_count > 0)
            ) begin

                read_allowed = 1'b1;

                expected_read_data =
                    model_mem[
                        model_read_ptr
                    ];

            end
            else begin

                read_allowed = 1'b0;

                expected_read_data =
                    8'h00;

            end


            // ------------------------------------------------
            // DUT samples inputs here.
            // ------------------------------------------------

            @(posedge clk);

            #1;


            // ------------------------------------------------
            // Verify READ result BEFORE updating reference
            // memory/pointers.
            // ------------------------------------------------

            if (read_allowed) begin

                check_data(
                    data_out,
                    expected_read_data
                );

            end


            // ------------------------------------------------
            // Update software reference WRITE state.
            // ------------------------------------------------

            if (write_allowed) begin

                model_mem[
                    model_write_ptr
                ] = data_in;


                if (
                    model_write_ptr
                    == (DEPTH - 1)
                ) begin

                    model_write_ptr = 0;

                end
                else begin

                    model_write_ptr =
                        model_write_ptr + 1;

                end

            end


            // ------------------------------------------------
            // Update software reference READ pointer.
            // ------------------------------------------------

            if (read_allowed) begin

                if (
                    model_read_ptr
                    == (DEPTH - 1)
                ) begin

                    model_read_ptr = 0;

                end
                else begin

                    model_read_ptr =
                        model_read_ptr + 1;

                end

            end


            // ------------------------------------------------
            // Update reference FIFO count.
            //
            // WRITE only -> +1
            // READ only  -> -1
            // BOTH       -> unchanged
            // NEITHER    -> unchanged
            // ------------------------------------------------

            if (
                write_allowed
                &&
                !read_allowed
            ) begin

                model_count =
                    model_count + 1;

            end
            else if (
                !write_allowed
                &&
                read_allowed
            ) begin

                model_count =
                    model_count - 1;

            end


            // ------------------------------------------------
            // Calculate expected FULL.
            // ------------------------------------------------

            if (
                model_count == DEPTH
            ) begin

                expected_full = 1'b1;

            end
            else begin

                expected_full = 1'b0;

            end


            // ------------------------------------------------
            // Calculate expected EMPTY.
            // ------------------------------------------------

            if (
                model_count == 0
            ) begin

                expected_empty = 1'b1;

            end
            else begin

                expected_empty = 1'b0;

            end


            // ------------------------------------------------
            // Verify count.
            // ------------------------------------------------

            check_count(
                "RANDOM FIFO COUNT",
                dut.count,
                model_count
            );


            // ------------------------------------------------
            // Verify full.
            // ------------------------------------------------

            check_bit(
                "RANDOM FIFO FULL",
                full,
                expected_full
            );


            // ------------------------------------------------
            // Verify empty.
            // ------------------------------------------------

            check_bit(
                "RANDOM FIFO EMPTY",
                empty,
                expected_empty
            );


            // ------------------------------------------------
            // Save trace.
            // ------------------------------------------------

            log_cycle(
                1'b0,
                wr_en,
                rd_en
            );


            // ------------------------------------------------
            // Console record.
            // ------------------------------------------------

            $display(
                "RANDOM_CYCLE=%0d wr=%0d rd=%0d data=%02h count=%0d full=%0d empty=%0d",
                cycle_number,
                wr_en,
                rd_en,
                data_in,
                dut.count,
                full,
                empty
            );


            // ------------------------------------------------
            // Clear controls ONLY after operation has been
            // completed.
            // ------------------------------------------------

            @(negedge clk);

            wr_en = 1'b0;
            rd_en = 1'b0;
            data_in = 8'h00;

        end

    endtask


    // ========================================================
    // MAIN
    // ========================================================

    initial begin

        // ----------------------------------------------------
        // Signal initialization.
        // ----------------------------------------------------

        rst = 1'b1;
        wr_en = 1'b0;
        rd_en = 1'b0;
        data_in = 8'h00;


        // ----------------------------------------------------
        // Result counters.
        // ----------------------------------------------------

        total_checks = 0;
        passed_checks = 0;
        failed_checks = 0;

        cycle_number = 0;


        // ----------------------------------------------------
        // Model initialization.
        // ----------------------------------------------------

        model_count = 0;
        model_write_ptr = 0;
        model_read_ptr = 0;

        model_mem[0] = 8'h00;
        model_mem[1] = 8'h00;
        model_mem[2] = 8'h00;
        model_mem[3] = 8'h00;


        // ----------------------------------------------------
        // Fixed random seed.
        //
        // Every run should generate the same random sequence.
        // ----------------------------------------------------

        initial_random_seed =
            32'h13579BDF;

        random_seed =
            initial_random_seed;


        // ----------------------------------------------------
        // Initialization of temporary variables.
        // ----------------------------------------------------

        random_control = 0;
        random_data = 0;

        count_before = 3'd0;
        write_ptr_before = 2'd0;
        read_ptr_before = 2'd0;

        write_allowed = 1'b0;
        read_allowed = 1'b0;

        expected_read_data = 8'h00;

        expected_full = 1'b0;
        expected_empty = 1'b1;


        // ----------------------------------------------------
        // VCD.
        // ----------------------------------------------------

        $dumpfile(
            "results/fifo/day20/random.vcd"
        );

        $dumpvars(
            0,
            tb_fifo_day20_random
        );


        // ----------------------------------------------------
        // Open trace.
        // ----------------------------------------------------

        trace_file = $fopen(
            "results/fifo/day20/random_trace.csv",
            "w"
        );


        if (trace_file == 0) begin

            $fatal(
                1,
                "Unable to open random baseline trace."
            );

        end


        // ----------------------------------------------------
        // CSV header.
        // ----------------------------------------------------

        $fdisplay(
            trace_file,
            "rst,wr_en,rd_en,count_before,count_after,write_ptr_before,write_ptr_after,read_ptr_before,read_ptr_after,full,empty"
        );


        // ----------------------------------------------------
        // Allow clock to begin.
        // ----------------------------------------------------

        repeat (2) begin
            @(posedge clk);
        end


        // ====================================================
        // HEADER
        // ====================================================

        $display("");
        $display("================================================");
        $display("DAY 20 FIFO RANDOM BASELINE");
        $display("================================================");

        $display(
            "RANDOM_SEED_INITIAL = %0d",
            initial_random_seed
        );

        $display(
            "RANDOM_CYCLES       = %0d",
            RANDOM_CYCLES
        );

        $display("------------------------------------------------");


        // ====================================================
        // RESET
        // ====================================================

        reset_fifo();


        // ====================================================
        // RANDOM RUN
        // ====================================================

        for (
            cycle_number = 1;
            cycle_number <= RANDOM_CYCLES;
            cycle_number = cycle_number + 1
        ) begin

            execute_random_cycle();

        end


        // ====================================================
        // FINAL SUMMARY
        // ====================================================

        $display("");
        $display("================================================");
        $display("DAY 20 FIFO RANDOM BASELINE SUMMARY");
        $display("================================================");

        $display(
            "RANDOM_CYCLES = %0d",
            RANDOM_CYCLES
        );

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
            "METHOD        = RANDOM_DETERMINISTIC"
        );

        $display("------------------------------------------------");


        if (failed_checks == 0) begin

            $display(
                "DAY 20 FIFO RANDOM BASELINE: PASS"
            );

        end
        else begin

            $display(
                "DAY 20 FIFO RANDOM BASELINE: FAIL"
            );

        end


        $display("================================================");
        $display("");


        // ----------------------------------------------------
        // Close trace.
        // ----------------------------------------------------

        $fclose(
            trace_file
        );


        #10;

        $finish;

    end

endmodule
