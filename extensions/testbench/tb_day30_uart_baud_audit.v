`timescale 1ns/1ps
module tb_day30_uart_baud_audit;
    parameter integer CPB=16;
    reg clk=0;
    always #5 clk=~clk;
    reg rst=1, start=0;
    reg [7:0] data_in=0;
    reg inject=0, serial_in=1;
    wire tx, tx_busy, tx_done;
    wire [7:0] data_out;
    wire rx_valid, rx_busy, frame_err;
    wire rx_line = inject ? serial_in : tx;
    integer checks=0, passed=0, failed=0, rx_count=0, tx_count=0, err_count=0;
    reg [7:0] last_rx=0;
    uart_tx #(.CLKS_PER_BIT(CPB)) dut_tx(
        .clk(clk),.rst(rst),.start(start),.data_in(data_in),
        .tx(tx),.busy(tx_busy),.done(tx_done));
    uart_rx #(.CLKS_PER_BIT(CPB)) dut_rx(
        .clk(clk),.rst(rst),.rx(rx_line),.data_out(data_out),
        .valid(rx_valid),.busy(rx_busy),.framing_error(frame_err));
    always @(negedge clk) begin
        if (!rst) begin
            if (rx_valid) begin rx_count=rx_count+1; last_rx=data_out; end
            if (tx_done) tx_count=tx_count+1;
            if (frame_err) err_count=err_count+1;
        end
    end
    task check;
        input condition;
        input [255:0] label;
        begin
            checks=checks+1;
            if (condition === 1'b1) passed=passed+1;
            else begin failed=failed+1; $display("[FAIL] %0s at %0t",label,$time); end
        end
    endtask
    task send_loopback;
        input [7:0] value;
        integer before_rx, before_tx, timeout;
        begin
            before_rx=rx_count; before_tx=tx_count;
            @(negedge clk); data_in=value; start=1;
            @(negedge clk); start=0;
            timeout=0;
            while ((rx_count==before_rx || tx_count==before_tx) && timeout<CPB*14) begin
                @(negedge clk); timeout=timeout+1;
            end
            check(timeout<CPB*14,"loopback timeout");
            check(rx_count==before_rx+1,"one received frame");
            check(tx_count==before_tx+1,"one transmitted frame");
            check(last_rx===value,"received byte matches transmitted byte");
            check(!frame_err,"no framing error");
            repeat (CPB*2) @(negedge clk);
        end
    endtask
    task drive_bit;
        input b;
        integer k;
        begin
            serial_in=b;
            for (k=0;k<CPB;k=k+1) @(negedge clk);
        end
    endtask
    integer i, old_err, old_rx;
    reg [7:0] val;
    initial begin
        $display("DAY 30 STEP 2 - UART BASELINE AUDIT");
        if (CPB<8) $fatal(1,"CPB must be at least 8");
        repeat (5) @(negedge clk);
        check(tx===1'b1,"TX idle after reset");
        check(!tx_busy && !rx_busy,"modules idle after reset");
        rst=0;
        send_loopback(8'h00);
        send_loopback(8'hFF);
        send_loopback(8'h55);
        send_loopback(8'hAA);
        send_loopback(8'h81);
        send_loopback(8'h7E);
        for (i=0;i<32;i=i+1) begin
            val=(i*73+19) & 8'hFF;
            send_loopback(val);
        end
        // Independent RX framing-error injection (bad stop bit).
        old_err=err_count; old_rx=rx_count;
        @(negedge clk); inject=1; serial_in=1;
        repeat (CPB*3) @(negedge clk);
        drive_bit(0);
        for (i=0;i<8;i=i+1) drive_bit((8'hA6 >> i)&1);
        drive_bit(0);
        drive_bit(1);
        repeat (CPB*2) @(negedge clk);
        check(err_count==old_err+1,"bad stop bit produces framing error");
        check(rx_count==old_rx,"bad stop bit does not produce valid byte");
        inject=0;
        repeat (CPB*3) @(negedge clk);
        $display("========================================");
        $display("TOTAL CHECKS: %0d",checks);
        $display("PASSED CHECKS: %0d",passed);
        $display("FAILED CHECKS: %0d",failed);
        $display("TX FRAMES: %0d",tx_count);
        $display("RX VALID FRAMES: %0d",rx_count);
        $display("RX FRAMING ERRORS: %0d",err_count);
        if (failed==0) $display("DAY 30 UART BASELINE: PASS");
        else $display("DAY 30 UART BASELINE: FAIL");
        $finish;
    end
endmodule
