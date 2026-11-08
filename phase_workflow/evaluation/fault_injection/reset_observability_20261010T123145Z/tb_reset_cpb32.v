
`timescale 1ns/1ps

module tb_reset_probe;

    localparam integer CPB = 32;

    reg clk = 0;
    always #5 clk = ~clk;

    reg rst = 1;
    reg start = 0;
    reg [7:0] data_in = 8'hA5;

    wire tx_ref, busy_ref, done_ref;
    wire tx_opt, busy_opt, done_opt;

    integer failures = 0;
    integer excited = 0;

    uart_tx #(.CLKS_PER_BIT(CPB)) reference_tx (
        .clk(clk),
        .rst(rst),
        .start(start),
        .data_in(data_in),
        .tx(tx_ref),
        .busy(busy_ref),
        .done(done_ref)
    );

    uart_tx_opt #(.CLKS_PER_BIT(CPB)) candidate_tx (
        .clk(clk),
        .rst(rst),
        .start(start),
        .data_in(data_in),
        .tx(tx_opt),
        .busy(busy_opt),
        .done(done_opt)
    );

    initial begin
        repeat (4) @(negedge clk);

        @(negedge clk);
        #1 rst = 0;

        @(negedge clk);
        #1 start = 1;

        @(posedge clk);
        #1;

        if (busy_ref === 1'b1 &&
            busy_opt === 1'b1) begin
            excited = 1;
        end else begin
            failures = failures + 1;
            $display("SETUP_FAILED: TX not busy");
        end

        @(negedge clk);
        #1;
        start = 0;
        rst = 1;

        @(posedge clk);
        #1;

        $display("CPB=%0d", CPB);
        $display("REFERENCE_TX=%b", tx_ref);
        $display("CANDIDATE_TX=%b", tx_opt);
        $display("REFERENCE_BUSY=%b", busy_ref);
        $display("CANDIDATE_BUSY=%b", busy_opt);
        $display("EXCITED=%0d", excited);

        if (tx_ref !== 1'b1 ||
            busy_ref !== 1'b0 ||
            done_ref !== 1'b0) begin
            failures = failures + 1;
            $display("ASSERT_FAIL: REFERENCE_RESET");
        end

        if ({tx_ref,busy_ref,done_ref} !==
            {tx_opt,busy_opt,done_opt}) begin
            failures = failures + 1;
            $display(
                "ASSERT_FAIL: RESET_CYCLE_MISMATCH"
            );
        end

        if (failures == 0)
            $display("VERDICT=PASS");
        else
            $display("VERDICT=FAIL");

        $finish;
    end

endmodule
