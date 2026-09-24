`timescale 1ns/1ps

module tb_fifo_day18;

    reg clk;
    reg rst;

    reg wr_en;
    reg rd_en;

    reg [7:0] data_in;

    wire [7:0] data_out;
    wire full;
    wire empty;

    integer total_checks;
    integer passed_checks;
    integer failed_checks;

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

    initial begin
        clk = 1'b0;

        forever begin
            #5 clk = ~clk;
        end
    end


    task check_flag;

        input actual_value;
        input expected_value;
        input [255:0] check_name;

        begin

            total_checks = total_checks + 1;

            if (actual_value === expected_value) begin

                passed_checks = passed_checks + 1;

                $display(
                    "CHECK_PASS : %0s actual=%b expected=%b",
                    check_name,
                    actual_value,
                    expected_value
                );

            end
            else begin

                failed_checks = failed_checks + 1;

                $display(
                    "CHECK_FAIL : %0s actual=%b expected=%b",
                    check_name,
                    actual_value,
                    expected_value
                );

            end

        end

    endtask


    task check_data;

        input [7:0] actual_value;
        input [7:0] expected_value;
        input [255:0] check_name;

        begin

            total_checks = total_checks + 1;

            if (actual_value === expected_value) begin

                passed_checks = passed_checks + 1;

                $display(
                    "CHECK_PASS : %0s actual=%02h expected=%02h",
                    check_name,
                    actual_value,
                    expected_value
                );

            end
            else begin

                failed_checks = failed_checks + 1;

                $display(
                    "CHECK_FAIL : %0s actual=%02h expected=%02h",
                    check_name,
                    actual_value,
                    expected_value
                );

            end

        end

    endtask


    task write_fifo;

        input [7:0] value;

        begin

            @(negedge clk);

            wr_en   = 1'b1;
            rd_en   = 1'b0;
            data_in = value;

            @(posedge clk);

            #1;

            @(negedge clk);

            wr_en = 1'b0;

        end

    endtask


    task read_fifo;

        input [7:0] expected_value;

        begin

            @(negedge clk);

            wr_en = 1'b0;
            rd_en = 1'b1;

            @(posedge clk);

            #1;

            check_data(
                data_out,
                expected_value,
                "FIFO READ DATA"
            );

            @(negedge clk);

            rd_en = 1'b0;

        end

    endtask


    task simultaneous_write_read;

        input [7:0] write_value;
        input [7:0] expected_read_value;

        begin

            @(negedge clk);

            wr_en   = 1'b1;
            rd_en   = 1'b1;
            data_in = write_value;

            @(posedge clk);

            #1;

            check_data(
                data_out,
                expected_read_value,
                "SIMULTANEOUS READ DATA"
            );

            @(negedge clk);

            wr_en = 1'b0;
            rd_en = 1'b0;

        end

    endtask


    initial begin

        $dumpfile(
            "results/fifo/day18/fifo_day18.vcd"
        );

        $dumpvars(
            0,
            tb_fifo_day18
        );

        total_checks  = 0;
        passed_checks = 0;
        failed_checks = 0;

        rst     = 1'b1;
        wr_en   = 1'b0;
        rd_en   = 1'b0;
        data_in = 8'h00;


        // -------------------------------------
        // TEST 1
        // Reset and empty condition
        // -------------------------------------

        repeat (2) @(posedge clk);

        #1;

        check_flag(
            empty,
            1'b1,
            "EMPTY AFTER RESET"
        );

        check_flag(
            full,
            1'b0,
            "NOT FULL AFTER RESET"
        );


        @(negedge clk);

        rst = 1'b0;


        // -------------------------------------
        // TEST 2
        // Single write
        // -------------------------------------

        write_fifo(8'h11);

        check_flag(
            empty,
            1'b0,
            "NOT EMPTY AFTER FIRST WRITE"
        );


        // -------------------------------------
        // TEST 3
        // Single read
        // -------------------------------------

        read_fifo(8'h11);

        check_flag(
            empty,
            1'b1,
            "EMPTY AFTER READING ONLY ENTRY"
        );


        // -------------------------------------
        // TEST 4
        // Fill FIFO
        // -------------------------------------

        write_fifo(8'hA1);
        write_fifo(8'hB2);
        write_fifo(8'hC3);
        write_fifo(8'hD4);

        check_flag(
            full,
            1'b1,
            "FULL AFTER FOUR WRITES"
        );

        check_flag(
            empty,
            1'b0,
            "NOT EMPTY WHEN FULL"
        );


        // -------------------------------------
        // TEST 5
        // Attempt write while full
        // This must NOT corrupt FIFO.
        // -------------------------------------

        write_fifo(8'hEE);

        check_flag(
            full,
            1'b1,
            "FULL REMAINS ASSERTED"
        );


        // -------------------------------------
        // TEST 6
        // Verify FIFO ordering
        // -------------------------------------

        read_fifo(8'hA1);
        read_fifo(8'hB2);
        read_fifo(8'hC3);
        read_fifo(8'hD4);

        check_flag(
            empty,
            1'b1,
            "EMPTY AFTER ALL READS"
        );


        // -------------------------------------
        // TEST 7
        // Attempt read while empty
        // -------------------------------------

        @(negedge clk);

        rd_en = 1'b1;
        wr_en = 1'b0;

        @(posedge clk);

        #1;

        check_flag(
            empty,
            1'b1,
            "EMPTY READ BLOCKED"
        );

        @(negedge clk);

        rd_en = 1'b0;


        // -------------------------------------
        // TEST 8
        // Simultaneous write and read
        // -------------------------------------

        write_fifo(8'h55);
        write_fifo(8'h66);

        simultaneous_write_read(
            8'h77,
            8'h55
        );

        read_fifo(8'h66);
        read_fifo(8'h77);

        check_flag(
            empty,
            1'b1,
            "EMPTY AFTER SIMULTANEOUS TEST"
        );


        // -------------------------------------
        // FINAL SUMMARY
        // -------------------------------------

        $display("");
        $display(
            "========================================"
        );

        $display(
            "DAY 18 FIFO VERIFICATION SUMMARY"
        );

        $display(
            "========================================"
        );

        $display(
            "TOTAL CHECKS  = %0d",
            total_checks
        );

        $display(
            "PASSED CHECKS = %0d",
            passed_checks
        );

        $display(
            "FAILED CHECKS = %0d",
            failed_checks
        );

        if (failed_checks == 0) begin

            $display(
                "DAY 18 FIFO VERIFICATION PASS"
            );

        end
        else begin

            $display(
                "DAY 18 FIFO VERIFICATION FAIL"
            );

            $fatal(
                1,
                "FIFO verification failed."
            );

        end

        $display(
            "========================================"
        );

        #10;

        $finish;

    end

endmodule
