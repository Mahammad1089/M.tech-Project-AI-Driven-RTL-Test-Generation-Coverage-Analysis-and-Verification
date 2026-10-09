`timescale 1ns/1ps

module tb_fsm_mealy_ext;

    parameter integer LENGTH = 4;
    parameter [LENGTH-1:0] PATTERN = 4'b1011;
    parameter integer OVERLAP = 1;

    reg clk;
    reg rst;
    reg din;
    wire detected;

    integer checks;
    integer failures;
    integer detections;

    reg [LENGTH-1:0] history;
    integer valid_bits;
    integer bit_count;
    integer last_detection_end;

    integer stream_length;
    integer stream_value;
    integer bit_index;
    integer random_index;
    integer seed;

    reg expected;
    reg [LENGTH-1:0] next_history;

    fsm_mealy_ext #(
        .LENGTH(LENGTH),
        .PATTERN(PATTERN),
        .OVERLAP(OVERLAP)
    ) dut (
        .clk(clk),
        .rst(rst),
        .din(din),
        .detected(detected)
    );

    initial clk = 0;
    always #5 clk = ~clk;

    task reset_model;
    begin
        history = {LENGTH{1'b0}};
        valid_bits = 0;
        bit_count = 0;
        last_detection_end = -1;
    end
    endtask

    task reset_dut;
    begin
        @(negedge clk);
        rst = 1;
        din = 0;
        reset_model();

        @(posedge clk);
        #1;

        @(negedge clk);
        rst = 0;
    end
    endtask

    task apply_bit;
        input reg bit_value;
        integer allowed;
    begin
        din = bit_value;

        next_history = (history << 1) | bit_value;

        expected = 0;

        allowed = 1;

        if (OVERLAP == 0) begin
            if ((bit_count + 1 - LENGTH) <= last_detection_end)
                allowed = 0;
        end

        if ((valid_bits >= LENGTH - 1) &&
            (next_history == PATTERN) &&
            allowed)
            expected = 1;

        #1;

        checks = checks + 1;

        if (detected !== expected) begin
            failures = failures + 1;

            $display(
                "FAIL pattern=%b overlap=%0d bit=%0d input=%b expected=%b actual=%b",
                PATTERN, OVERLAP, bit_count,
                bit_value, expected, detected
            );

            $fatal(1, "FSM functional mismatch");
        end

        if (expected) begin
            detections = detections + 1;
            last_detection_end = bit_count;
        end

        history = next_history;

        if (valid_bits < LENGTH)
            valid_bits = valid_bits + 1;

        bit_count = bit_count + 1;

        @(posedge clk);
        #1;
        @(negedge clk);
    end
    endtask

    initial begin

        rst = 0;
        din = 0;
        checks = 0;
        failures = 0;
        detections = 0;
        seed = 32'h12345678;

        $display("==========================================");
        $display("DAY 26 - MEALY FSM FUNCTIONAL VERIFICATION");
        $display("PATTERN=%b LENGTH=%0d OVERLAP=%0d",
                 PATTERN, LENGTH, OVERLAP);
        $display("==========================================");

        for (stream_length = 1;
             stream_length <= 10;
             stream_length = stream_length + 1) begin

            for (stream_value = 0;
                 stream_value < (1 << stream_length);
                 stream_value = stream_value + 1) begin

                reset_dut();

                for (bit_index = stream_length - 1;
                     bit_index >= 0;
                     bit_index = bit_index - 1) begin

                    apply_bit(
                        (stream_value >> bit_index) & 1
                    );
                end
            end
        end

        reset_dut();

        for (random_index = 0;
             random_index < 500;
             random_index = random_index + 1) begin

            seed = (seed * 1664525) + 1013904223;

            apply_bit((seed >> 16) & 1);

            if ((random_index % 73) == 72)
                reset_dut();
        end

        $display("TOTAL CHECKS: %0d", checks);
        $display("PASSED CHECKS: %0d", checks - failures);
        $display("FAILED CHECKS: %0d", failures);
        $display("DETECTIONS: %0d", detections);

        if (failures == 0) begin
            $display("DAY 26 MEALY VERIFICATION: PASS");
        end else begin
            $display("DAY 26 MEALY VERIFICATION: FAIL");
            $fatal(1);
        end

        $finish;
    end

endmodule
