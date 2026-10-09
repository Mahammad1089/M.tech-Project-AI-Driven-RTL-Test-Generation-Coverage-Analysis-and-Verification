`timescale 1ns/1ps

module tb_day30_fifo_audit;

    reg clk;
    reg rst;
    reg wr_en;
    reg rd_en;
    reg [7:0] data_in;

    wire [7:0] data_out;
    wire full;
    wire empty;

    integer passed;
    integer failed;

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

    initial clk = 0;
    always #5 clk = ~clk;

    task check_flags;
        input expected_full;
        input expected_empty;
        begin
            if ((full === expected_full) &&
                (empty === expected_empty)) begin
                passed = passed + 1;
            end else begin
                failed = failed + 1;
                $display(
                    "[FAIL] Flags: full=%b empty=%b expected=%b,%b",
                    full, empty, expected_full, expected_empty
                );
            end
        end
    endtask

    task check_data;
        input [7:0] expected_data;
        begin
            if (data_out === expected_data) begin
                passed = passed + 1;
            end else begin
                failed = failed + 1;
                $display(
                    "[FAIL] Data: actual=%h expected=%h",
                    data_out, expected_data
                );
            end
        end
    endtask

    task cycle;
        input reset_value;
        input write_value;
        input read_value;
        input [7:0] input_value;
        begin
            @(negedge clk);
            rst = reset_value;
            wr_en = write_value;
            rd_en = read_value;
            data_in = input_value;

            @(posedge clk);
            #1;
        end
    endtask

    initial begin

        passed = 0;
        failed = 0;

        rst = 0;
        wr_en = 0;
        rd_en = 0;
        data_in = 0;

        $display("======================================");
        $display("DAY 30 FIFO FUNCTIONAL AUDIT");
        $display("======================================");

        // Test 1: Reset and empty condition
        cycle(1, 0, 0, 8'h00);
        check_flags(0, 1);
        check_data(8'h00);

        // Test 2: Read when empty
        cycle(0, 0, 1, 8'h00);
        check_flags(0, 1);
        check_data(8'h00);

        // Test 3: Write first element
        cycle(0, 1, 0, 8'h11);
        check_flags(0, 0);

        // Test 4: Fill FIFO
        cycle(0, 1, 0, 8'h22);
        cycle(0, 1, 0, 8'h33);
        cycle(0, 1, 0, 8'h44);
        check_flags(1, 0);

        // Test 5: Block write when full
        cycle(0, 1, 0, 8'hFF);
        check_flags(1, 0);

        // Test 6: Read in FIFO order
        cycle(0, 0, 1, 8'h00);
        check_data(8'h11);
        check_flags(0, 0);

        cycle(0, 0, 1, 8'h00);
        check_data(8'h22);

        cycle(0, 0, 1, 8'h00);
        check_data(8'h33);

        cycle(0, 0, 1, 8'h00);
        check_data(8'h44);
        check_flags(0, 1);

        // Test 7: Pointer wraparound
        cycle(0, 1, 0, 8'hA1);
        cycle(0, 1, 0, 8'hB2);
        cycle(0, 1, 0, 8'hC3);
        cycle(0, 1, 0, 8'hD4);
        check_flags(1, 0);

        cycle(0, 0, 1, 8'h00);
        check_data(8'hA1);

        cycle(0, 0, 1, 8'h00);
        check_data(8'hB2);

        cycle(0, 0, 1, 8'h00);
        check_data(8'hC3);

        cycle(0, 0, 1, 8'h00);
        check_data(8'hD4);
        check_flags(0, 1);

        // Test 8: Simultaneous write and read
        cycle(0, 1, 0, 8'h55);
        cycle(0, 1, 1, 8'h66);
        check_data(8'h55);
        check_flags(0, 0);

        cycle(0, 0, 1, 8'h00);
        check_data(8'h66);
        check_flags(0, 1);

        // Test 9: Reset while data exists
        cycle(0, 1, 0, 8'h77);
        cycle(1, 0, 0, 8'h00);
        check_flags(0, 1);
        check_data(8'h00);

        $display("======================================");
        $display("TOTAL CHECKS : %0d", passed + failed);
        $display("PASSED CHECKS: %0d", passed);
        $display("FAILED CHECKS: %0d", failed);

        if (failed == 0) begin
            $display("DAY 30 FIFO AUDIT: PASS");
        end else begin
            $display("DAY 30 FIFO AUDIT: FAIL");
            $fatal(1, "FIFO functional verification failed");
        end

        $finish;
    end

endmodule
