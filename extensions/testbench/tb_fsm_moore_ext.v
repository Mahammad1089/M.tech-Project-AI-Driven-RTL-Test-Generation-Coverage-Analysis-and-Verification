`timescale 1ns/1ps

module tb_fsm_moore_ext;

    parameter integer LENGTH = 4;
    parameter [LENGTH-1:0] PATTERN = 4'b1011;
    parameter integer OVERLAP = 1;

    reg clk;
    reg rst;
    reg din;

    wire detected;

    reg [LENGTH-1:0] reference_history;
    reg [LENGTH-1:0] suffix_mask;

    integer reference_count;
    integer total_checks;
    integer passed_checks;
    integer failed_checks;
    integer detection_count;

    integer i;
    integer j;
    integer random_seed;
    integer random_value;

    reg expected_detected;

    fsm_moore_ext #(
        .LENGTH(LENGTH),
        .PATTERN(PATTERN),
        .OVERLAP(OVERLAP)
    ) dut (
        .clk(clk),
        .rst(rst),
        .din(din),
        .detected(detected)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    // Independent streaming reference model.
    // This model does not use the DUT's FSM states.
    task apply_bit;
        input bit_value;
        begin
            @(negedge clk);
            din = bit_value;
            rst = 1'b0;

            @(posedge clk);
            #1;

            reference_history =
                (reference_history << 1) | bit_value;

            reference_count = reference_count + 1;

            expected_detected = 1'b0;

            if ((reference_count >= LENGTH) &&
                (reference_history == PATTERN)) begin
                expected_detected = 1'b1;
            end

            total_checks = total_checks + 1;

            if (detected === expected_detected) begin
                passed_checks = passed_checks + 1;
            end
            else begin
                failed_checks = failed_checks + 1;

                $display(
                    "FAIL pattern=%b overlap=%0d check=%0d input=%b expected=%b actual=%b",
                    PATTERN,
                    OVERLAP,
                    total_checks,
                    bit_value,
                    expected_detected,
                    detected
                );

                $fatal(1, "Moore FSM functional mismatch");
            end

            if (expected_detected) begin
                detection_count = detection_count + 1;

                if (OVERLAP == 0) begin
                    reference_history = {LENGTH{1'b0}};
                    reference_count = 0;
                end
                else begin
                    reference_history =
                        reference_history & suffix_mask;

                    reference_count = LENGTH - 1;
                end
            end
            else if (reference_count >= LENGTH) begin
                reference_history =
                    reference_history & suffix_mask;

                reference_count = LENGTH - 1;
            end
        end
    endtask

    task reset_dut;
        begin
            @(negedge clk);
            rst = 1'b1;
            din = 1'b0;

            @(posedge clk);
            #1;

            if (detected !== 1'b0)
                $fatal(1, "Moore reset output mismatch");

            reference_history = {LENGTH{1'b0}};
            reference_count = 0;

            @(negedge clk);
            rst = 1'b0;
        end
    endtask

    task send_pattern;
        integer p;
        begin
            for (p = LENGTH - 1; p >= 0; p = p - 1)
                apply_bit(PATTERN[p]);
        end
    endtask

    initial begin
        rst = 1'b1;
        din = 1'b0;

        reference_history = {LENGTH{1'b0}};
        reference_count = 0;

        total_checks = 0;
        passed_checks = 0;
        failed_checks = 0;
        detection_count = 0;

        random_seed = 32'h1234ABCD;
        random_value = 0;

        suffix_mask = {LENGTH{1'b1}} >> 1;

        if (LENGTH < 2)
            $fatal(1, "LENGTH must be at least 2");

        if ((OVERLAP != 0) && (OVERLAP != 1))
            $fatal(1, "OVERLAP must be 0 or 1");

        $display("============================================");
        $display("DAY 26 - MOORE FSM FUNCTIONAL VERIFICATION");
        $display(
            "PATTERN=%b LENGTH=%0d OVERLAP=%0d",
            PATTERN, LENGTH, OVERLAP
        );
        $display("============================================");

        reset_dut();

        // Directed full-pattern detections.
        for (i = 0; i < 20; i = i + 1) begin
            send_pattern();
            apply_bit(1'b0);
            apply_bit(1'b0);
        end

        // Continuous pattern repetitions.
        reset_dut();

        for (i = 0; i < 40; i = i + 1)
            send_pattern();

        // Exercise long runs of zeros and ones.
        reset_dut();

        for (i = 0; i < 100; i = i + 1)
            apply_bit(1'b0);

        for (i = 0; i < 100; i = i + 1)
            apply_bit(1'b1);

        // Randomized streaming inputs.
        reset_dut();

        for (i = 0; i < 8000; i = i + 1) begin
            random_value = $random(random_seed);
            apply_bit(random_value & 1);
        end

        $display("--------------------------------------------");
        $display("TOTAL CHECKS : %0d", total_checks);
        $display("PASSED CHECKS: %0d", passed_checks);
        $display("FAILED CHECKS: %0d", failed_checks);
        $display("DETECTIONS   : %0d", detection_count);
        $display("--------------------------------------------");

        if ((failed_checks == 0) &&
            (passed_checks == total_checks) &&
            (detection_count > 0)) begin

            $display("DAY 26 MOORE VERIFICATION: PASS");
        end
        else begin
            $fatal(1, "DAY 26 MOORE VERIFICATION: FAIL");
        end

        $finish;
    end

endmodule
