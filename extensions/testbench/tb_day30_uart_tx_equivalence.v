`timescale 1ns/1ps
module tb_day30_uart_tx_equivalence;
    parameter integer CPB=16;
    reg clk=0;
    always #5 clk=~clk;
    reg rst=1, start=0;
    reg [7:0] data_in=0;
    wire tx_ref,busy_ref,done_ref,tx_opt,busy_opt,done_opt;
    integer checks=0,passed=0,failed=0,frames=0,cycles=0;
    integer i,j;
    reg [31:0] rng=32'h5A17C0DE;
    uart_tx #(.CLKS_PER_BIT(CPB)) reference_tx(
        .clk(clk),.rst(rst),.start(start),.data_in(data_in),
        .tx(tx_ref),.busy(busy_ref),.done(done_ref));
    uart_tx_opt #(.CLKS_PER_BIT(CPB)) optimized_tx(
        .clk(clk),.rst(rst),.start(start),.data_in(data_in),
        .tx(tx_opt),.busy(busy_opt),.done(done_opt));
    always @(negedge clk) begin
        #1;
        cycles=cycles+1;
        checks=checks+1;
        if ({tx_ref,busy_ref,done_ref} === {tx_opt,busy_opt,done_opt}) passed=passed+1;
        else begin
            failed=failed+1;
            if (failed<=15) $display("[FAIL] cycle=%0d rst=%b start=%b data=%h REF=%b%b%b OPT=%b%b%b",cycles,rst,start,data_in,tx_ref,busy_ref,done_ref,tx_opt,busy_opt,done_opt);
        end
    end
    task send_byte;
        input [7:0] value;
        integer timeout;
        begin
            @(posedge clk); #2;
            if (busy_ref || busy_opt) begin
                $display("[FAIL] send_byte called while busy");
                failed=failed+1;
            end
            @(negedge clk); #2; data_in=value; start=1;
            @(negedge clk); #2; start=0;
            timeout=0;
            while ((busy_ref || busy_opt) && timeout < CPB*13+10) begin
                @(negedge clk); #2;
                timeout=timeout+1;
            end
            if (timeout >= CPB*13+10) begin
                $display("[FAIL] timeout for byte %h",value);
                failed=failed+1;
            end
            frames=frames+1;
            repeat(2) @(posedge clk);
        end
    endtask
    initial begin
        $display("DAY 30 STEP 4B - UART TX CYCLE EQUIVALENCE CPB=%0d",CPB);
        if (CPB<2) $fatal(1,"CPB must be >=2");
        repeat(5) @(posedge clk);
        @(negedge clk); #2; rst=0;
        for(i=0;i<256;i=i+1) send_byte(i[7:0]);
        for(i=0;i<16;i=i+1) begin
            rng=(rng<<13)^rng;
            rng=(rng>>17)^rng;
            rng=(rng<<5)^rng;
            send_byte(rng[7:0]);
        end
        // Reset during a frame, then confirm recovery.
        @(negedge clk); #2; data_in=8'hA5; start=1;
        @(negedge clk); #2; start=0;
        repeat(CPB*3) @(posedge clk);
        @(negedge clk); #2; rst=1;
        repeat(3) @(posedge clk);
        @(negedge clk); #2; rst=0;
        send_byte(8'h5A);
        repeat(4) @(posedge clk);
        $display("TOTAL CHECKS: %0d",checks);
        $display("PASSED CHECKS: %0d",passed);
        $display("FAILED CHECKS: %0d",failed);
        $display("COMPLETE FRAMES: %0d",frames);
        $display("CYCLES OBSERVED: %0d",cycles);
        if (failed==0 && frames==273) $display("DAY 30 UART TX EQUIVALENCE: PASS");
        else $display("DAY 30 UART TX EQUIVALENCE: FAIL");
        $finish;
    end
endmodule
