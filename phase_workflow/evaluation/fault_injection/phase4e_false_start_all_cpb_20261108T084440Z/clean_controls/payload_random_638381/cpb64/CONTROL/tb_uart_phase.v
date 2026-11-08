`timescale 1ns/1ps
module tb_uart_phase;
    localparam integer CPB = 64;
    reg clk = 0;
    always #5 clk = ~clk;
    reg rst = 1, start = 0;
    reg [7:0] data_in = 0;
    reg inject = 0, serial_in = 1;
    wire tx_ref, busy_ref, done_ref, tx_opt, busy_tx_opt, done_tx_opt;
    wire [7:0] received_ref, received_opt;
    wire valid_ref, busy_rx_ref, error_ref;
    wire valid_opt, busy_rx_opt, error_opt;
    wire wire_rx = inject ? serial_in : tx_ref;
    integer checks = 0, failed = 0, cycles = 0;
    integer received_count = 0, sent_count = 0, framing_count = 0;
    reg [7:0] last_received = 0;
    integer covered [0:9];
    integer ci;
    integer before_rx, before_tx, before_error, waits, before_fail;
    integer k;
    integer pair_failed_prior;
    uart_tx #(.CLKS_PER_BIT(CPB)) tx_base(
        .clk(clk), .rst(rst), .start(start), .data_in(data_in),
        .tx(tx_ref), .busy(busy_ref), .done(done_ref));
    uart_tx_opt #(.CLKS_PER_BIT(CPB)) tx_candidate(
        .clk(clk), .rst(rst), .start(start), .data_in(data_in),
        .tx(tx_opt), .busy(busy_tx_opt), .done(done_tx_opt));
    uart_rx #(.CLKS_PER_BIT(CPB)) rx_base(
        .clk(clk), .rst(rst), .rx(wire_rx), .data_out(received_ref),
        .valid(valid_ref), .busy(busy_rx_ref), .framing_error(error_ref));
    uart_rx_opt #(.CLKS_PER_BIT(CPB)) rx_candidate(
        .clk(clk), .rst(rst), .rx(wire_rx), .data_out(received_opt),
        .valid(valid_opt), .busy(busy_rx_opt), .framing_error(error_opt));

    task assert_true;
        input condition;
        input [8*90-1:0] label;
        begin
            checks = checks + 1;
            if (condition !== 1'b1) begin
                failed = failed + 1;
                if (failed <= 20) $display("ASSERT_FAIL: %0s at %0t",label,$time);
            end
        end
    endtask
    task mark_bin;
        input integer number;
        begin
            if (number >= 0 && number < 10) covered[number] = 1;
        end
    endtask
    // Continuous cycle-level equivalence, independently of directed checks.
    always @(negedge clk) begin
        #1;
        cycles = cycles + 1;
        if (!rst) begin
            assert_true({tx_ref,busy_ref,done_ref} ===
                        {tx_opt,busy_tx_opt,done_tx_opt},"TX cycle equivalence");
            assert_true({received_ref,valid_ref,busy_rx_ref,error_ref} ===
                        {received_opt,valid_opt,busy_rx_opt,error_opt},"RX cycle equivalence");
            if (valid_ref) begin
                received_count = received_count + 1;
                last_received = received_ref;
            end
            if (done_ref) sent_count = sent_count + 1;
            if (error_ref) framing_count = framing_count + 1;
        end
    end
    task one_loopback;
        input [7:0] value;
        input integer bin_number;
        begin
            before_fail=failed; before_rx=received_count; before_tx=sent_count;
            @(negedge clk); #2; data_in=value; start=1;
            @(negedge clk); #2; start=0;
            waits=0;
            while ((received_count == before_rx || sent_count == before_tx)
                   && waits < CPB*15) begin
                @(negedge clk); #2; waits=waits+1;
            end
            assert_true(waits < CPB*15,"loopback timeout");
            assert_true(received_count == before_rx+1,"one RX valid frame");
            assert_true(sent_count == before_tx+1,"one TX completed frame");
            assert_true(last_received === value,"received payload matches expected");
            assert_true(!error_ref && !error_opt,"no framing error");
            repeat(CPB*2) @(negedge clk);
            if (failed == before_fail) mark_bin(bin_number);
        end
    endtask
    task serial_bit;
        input bit_value;
        begin
            serial_in = bit_value;
            for (k=0;k<CPB;k=k+1) @(negedge clk);
        end
    endtask
    task bad_stop;
        integer n;
        begin
            before_fail=failed; before_rx=received_count;
            before_error=framing_count;
            @(negedge clk); #2; inject=1; serial_in=1;
            repeat(CPB*3) @(negedge clk);
            serial_bit(0);
            for (n=0;n<8;n=n+1) serial_bit((8'hA6 >> n)&1);
            serial_bit(0);
            serial_bit(1);
            repeat(CPB*2) @(negedge clk);
            assert_true(framing_count == before_error+1,"bad stop reported");
            assert_true(received_count == before_rx,"invalid stop suppressed valid");
            @(negedge clk); #2; inject=0;
            repeat(CPB*3) @(negedge clk);
            if (failed==before_fail) mark_bin(6);
        end
    endtask
    task reset_mid;
        begin
            before_fail=failed;
            @(negedge clk); #2; data_in=8'hA5; start=1;
            @(negedge clk); #2; start=0;
            repeat(CPB*3) @(negedge clk);
            @(negedge clk); #2; rst=1;
            repeat(4) @(negedge clk);
            assert_true(tx_ref && !busy_ref && !done_ref,"reset aborts TX");
            assert_true(tx_opt && !busy_tx_opt && !done_tx_opt,"reset aborts opt TX");
            @(negedge clk); #2; rst=0;
            repeat(CPB*3) @(negedge clk);
            if (failed==before_fail) mark_bin(7);
            one_loopback(8'h3C,5);
        end
    endtask
    task start_while_busy;
        input [7:0] value;
        begin
            before_fail=failed; before_rx=received_count; before_tx=sent_count;
            @(negedge clk); #2; data_in=value; start=1;
            @(negedge clk); #2; start=0;
            repeat(CPB*2) @(negedge clk);
            @(negedge clk); #2; data_in=(value^8'hFF); start=1;
            @(negedge clk); #2; start=0;
            waits=0;
            while ((received_count == before_rx || sent_count == before_tx)
                  && waits < CPB*15) begin
                @(negedge clk); #2; waits=waits+1;
            end
            assert_true(waits < CPB*15,"busy-start timeout");
            assert_true(received_count==before_rx+1,"busy start does not cause second RX");
            assert_true(sent_count==before_tx+1,"busy start ignored by TX");
            assert_true(last_received===value,"busy-start first byte preserved");
            repeat(CPB*3) @(negedge clk);
            if (failed==before_fail) mark_bin(8);
        end
    endtask
    initial begin
        for (ci=0;ci<10;ci=ci+1) covered[ci]=0;
        $display("PHASE_UART_VERIFICATION_BEGIN CPB=%0d", CPB);
        if (CPB<8) $fatal(1,"CPB must be >= 8 for supported RX operation");
        repeat(6) @(negedge clk);
        assert_true(tx_ref === 1'b1 && tx_opt === 1'b1,"idle TX level after reset");
        @(negedge clk); #2; rst=0;
        one_loopback(8'd49,5);
        one_loopback(8'd88,5);
        one_loopback(8'd195,5);
        one_loopback(8'd199,5);
        one_loopback(8'd200,5);
        one_loopback(8'd177,5);
        one_loopback(8'd48,5);
        one_loopback(8'd36,5);
        one_loopback(8'd218,5);
        one_loopback(8'd19,5);
        repeat(CPB*4) @(negedge clk);
        $display("TOTAL_CHECKS=%0d",checks);
        $display("FAILED_CHECKS=%0d",failed);
        $display("CYCLES=%0d",cycles);
        $display("RX_FRAMES=%0d",received_count);
        $display("TX_FRAMES=%0d",sent_count);
        $display("FRAMING_ERRORS=%0d",framing_count);
        $display("COVERAGE=zero:%0d,all_ones:%0d,alternating_55:%0d,alternating_aa:%0d,edge_81:%0d,other_data:%0d,framing_error:%0d,reset_mid_tx:%0d,busy_start:%0d,paired_frames:%0d",
            covered[0],covered[1],covered[2],covered[3],covered[4],
            covered[5],covered[6],covered[7],covered[8],covered[9]);
        if (failed==0) $display("VERDICT=PASS");
        else $display("VERDICT=FAIL");
        $finish;
    end
endmodule
