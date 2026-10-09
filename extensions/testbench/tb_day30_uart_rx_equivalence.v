`timescale 1ns/1ps
module tb_day30_uart_rx_equivalence;
    parameter integer CPB = 16;
    reg clk = 0;
    always #5 clk = ~clk;
    reg rst = 1;
    reg rx = 1;

    wire [7:0] ref_data, opt_data;
    wire ref_valid, opt_valid;
    wire ref_busy, opt_busy;
    wire ref_error, opt_error;

    uart_rx #(.CLKS_PER_BIT(CPB)) baseline (
        .clk(clk), .rst(rst), .rx(rx), .data_out(ref_data),
        .valid(ref_valid), .busy(ref_busy), .framing_error(ref_error)
    );
    uart_rx_opt #(.CLKS_PER_BIT(CPB)) optimized (
        .clk(clk), .rst(rst), .rx(rx), .data_out(opt_data),
        .valid(opt_valid), .busy(opt_busy), .framing_error(opt_error)
    );

    integer checks = 0;
    integer passed = 0;
    integer failed = 0;
    integer cycles = 0;
    integer frames_sent = 0;
    integer valid_frames = 0;
    integer framing_errors = 0;
    reg [7:0] last_byte = 0;

    task assert_true;
        input condition;
        input [255:0] label;
        begin
            checks = checks + 1;
            if (condition === 1'b1)
                passed = passed + 1;
            else begin
                failed = failed + 1;
                if (failed <= 25)
                    $display("[FAIL] %0s cycle=%0d CPB=%0d t=%0t ref=%02h/%b/%b/%b opt=%02h/%b/%b/%b",
                        label, cycles, CPB, $time,
                        ref_data, ref_valid, ref_busy, ref_error,
                        opt_data, opt_valid, opt_busy, opt_error);
            end
        end
    endtask

    // Sample after the nonblocking assignments at every active clock edge;
    // serial stimulus changes only on falling edges, avoiding simulator races.
    always @(posedge clk) begin
        #1;
        cycles = cycles + 1;
        assert_true(ref_data === opt_data, "data_out cycle equality");
        assert_true(ref_valid === opt_valid, "valid cycle equality");
        assert_true(ref_busy === opt_busy, "busy cycle equality");
        assert_true(ref_error === opt_error, "framing_error cycle equality");
        if (!rst) begin
            if (ref_valid) begin
                valid_frames = valid_frames + 1;
                last_byte = ref_data;
            end
            if (ref_error)
                framing_errors = framing_errors + 1;
        end
    end

    task send_bit;
        input value;
        integer c;
        begin
            rx = value;
            for (c = 0; c < CPB; c = c + 1)
                @(negedge clk);
        end
    endtask

    task send_byte;
        input [7:0] value;
        input good_stop;
        integer i;
        integer old_valid;
        integer old_error;
        begin
            old_valid = valid_frames;
            old_error = framing_errors;
            @(negedge clk);
            send_bit(0);
            for (i = 0; i < 8; i = i + 1)
                send_bit(value[i]);
            send_bit(good_stop);
            send_bit(1);
            send_bit(1);
            frames_sent = frames_sent + 1;
            if (good_stop) begin
                assert_true(valid_frames == old_valid + 1, "exactly one valid frame");
                assert_true(framing_errors == old_error, "no framing error for valid stop");
                assert_true(last_byte === value, "received byte equals independent stimulus");
            end else begin
                assert_true(valid_frames == old_valid, "bad stop rejects valid frame");
                assert_true(framing_errors == old_error + 1, "bad stop flags one framing error");
            end
            assert_true(ref_busy === 1'b0 && opt_busy === 1'b0,
                        "receivers idle after frame");
        end
    endtask

    integer i;
    integer prior_valid;
    integer prior_error;
    initial begin
        $display("DAY 30 STEP 4C - UART RX CYCLE-ACCURATE EQUIVALENCE");
        $display("CLKS_PER_BIT: %0d", CPB);
        if (CPB < 8)
            $fatal(1, "CPB must be >= 8 to match verified baseline assumptions");

        repeat (5) @(negedge clk);
        assert_true(ref_data === 8'h00 && opt_data === 8'h00,
                    "outputs cleared by reset");
        assert_true(!ref_busy && !opt_busy && !ref_valid && !opt_valid,
                    "receivers idle after reset");
        rst = 0;
        repeat (CPB * 3) @(negedge clk);

        // Exhaustively exercise all 256 possible UART data byte values.
        for (i = 0; i < 256; i = i + 1)
            send_byte(i[7:0], 1'b1);

        // Invalid stop bits exercised with varied payloads.
        send_byte(8'h00, 1'b0);
        send_byte(8'hA6, 1'b0);
        send_byte(8'hFF, 1'b0);

        // False start: assert line low briefly then recover to idle.
        prior_valid = valid_frames;
        prior_error = framing_errors;
        @(negedge clk);
        rx = 0;
        repeat (2) @(negedge clk);
        rx = 1;
        repeat (CPB * 3) @(negedge clk);
        assert_true(valid_frames == prior_valid, "false start causes no receive");
        assert_true(framing_errors == prior_error, "false start causes no framing error");
        assert_true(!ref_busy && !opt_busy, "false start recovers to idle");

        // Reset in the middle of a partial frame.
        @(negedge clk);
        send_bit(0);
        send_bit(1);
        send_bit(0);
        send_bit(1);
        rst = 1;
        rx = 1;
        repeat (5) @(negedge clk);
        assert_true(ref_data === 8'h00 && opt_data === 8'h00,
                    "midframe reset clears data_out");
        assert_true(!ref_valid && !opt_valid && !ref_busy && !opt_busy,
                    "midframe reset clears status");
        rst = 0;
        repeat (CPB * 3) @(negedge clk);
        send_byte(8'h3C, 1'b1);

        $display("========================================");
        $display("TOTAL CHECKS: %0d", checks);
        $display("PASSED CHECKS: %0d", passed);
        $display("FAILED CHECKS: %0d", failed);
        $display("CYCLES COMPARED: %0d", cycles);
        $display("FRAMES DRIVEN: %0d", frames_sent);
        $display("VALID FRAMES: %0d", valid_frames);
        $display("FRAMING ERRORS: %0d", framing_errors);
        if (failed == 0 && frames_sent == 260 && valid_frames == 257 && framing_errors == 3)
            $display("DAY 30 UART RX EQUIVALENCE: PASS");
        else begin
            $display("DAY 30 UART RX EQUIVALENCE: FAIL");
            $fatal(1, "Equivalence or independent stimulus assertions failed");
        end
        $finish;
    end

    initial begin
        #10000000;
        $fatal(1, "WATCHDOG: UART RX equivalence simulation timed out");
    end
endmodule
