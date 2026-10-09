`timescale 1ns/1ps
module tb_day30_fifo_equivalence #(
    parameter integer DATA_WIDTH = 8,
    parameter integer DEPTH = 4,
    parameter integer ADDR_WIDTH = 2,
    parameter integer RANDOM_CYCLES = 5000
);
    reg clk, rst, wr_en, rd_en;
    reg [DATA_WIDTH-1:0] data_in;
    wire [DATA_WIDTH-1:0] base_data, opt_data;
    wire base_full, base_empty, opt_full, opt_empty;

    fifo #(.DATA_WIDTH(DATA_WIDTH), .DEPTH(DEPTH), .ADDR_WIDTH(ADDR_WIDTH)) baseline (
        .clk(clk), .rst(rst), .wr_en(wr_en), .rd_en(rd_en), .data_in(data_in),
        .data_out(base_data), .full(base_full), .empty(base_empty)
    );
    fifo_opt #(.DATA_WIDTH(DATA_WIDTH), .DEPTH(DEPTH), .ADDR_WIDTH(ADDR_WIDTH)) optimized (
        .clk(clk), .rst(rst), .wr_en(wr_en), .rd_en(rd_en), .data_in(data_in),
        .data_out(opt_data), .full(opt_full), .empty(opt_empty)
    );

    reg [DATA_WIDTH-1:0] model_memory [0:DEPTH-1];
    reg [DATA_WIDTH-1:0] expected_data;
    integer model_count, model_wp, model_rp;
    integer cycles, passed, failed, accepted_writes, accepted_reads;
    integer resets, simultaneous_requests, blocked_writes, blocked_reads;
    integer k, j;
    reg wr_fire, rd_fire;
    reg [31:0] random_state;

    initial clk = 0;
    always #5 clk = ~clk;

    task verify_outputs;
        begin
            if (base_data === expected_data) passed = passed + 1;
            else begin failed = failed + 1; $display("[FAIL] cycle=%0d baseline data got=%h expected=%h", cycles, base_data, expected_data); end
            if (opt_data === expected_data) passed = passed + 1;
            else begin failed = failed + 1; $display("[FAIL] cycle=%0d optimized data got=%h expected=%h", cycles, opt_data, expected_data); end
            if (base_full === (model_count == DEPTH)) passed = passed + 1;
            else begin failed = failed + 1; $display("[FAIL] cycle=%0d baseline full=%b count=%0d", cycles, base_full, model_count); end
            if (opt_full === (model_count == DEPTH)) passed = passed + 1;
            else begin failed = failed + 1; $display("[FAIL] cycle=%0d optimized full=%b count=%0d", cycles, opt_full, model_count); end
            if (base_empty === (model_count == 0)) passed = passed + 1;
            else begin failed = failed + 1; $display("[FAIL] cycle=%0d baseline empty=%b count=%0d", cycles, base_empty, model_count); end
            if (opt_empty === (model_count == 0)) passed = passed + 1;
            else begin failed = failed + 1; $display("[FAIL] cycle=%0d optimized empty=%b count=%0d", cycles, opt_empty, model_count); end
            if (failed >= 20) $fatal(1, "Too many FIFO mismatches");
        end
    endtask

    task cycle;
        input reset_value, write_value, read_value;
        input [DATA_WIDTH-1:0] input_value;
        integer idx;
        begin
            @(negedge clk);
            rst = reset_value;
            wr_en = write_value;
            rd_en = read_value;
            data_in = input_value;

            @(posedge clk);
            // Independent sequential FIFO model. Read old storage contents
            // before writing, matching nonblocking Verilog memory semantics.
            if (rst) begin
                model_count = 0;
                model_wp = 0;
                model_rp = 0;
                expected_data = 0;
                resets = resets + 1;
                for (idx = 0; idx < DEPTH; idx = idx + 1)
                    model_memory[idx] = 0;
            end else begin
                wr_fire = wr_en && (model_count != DEPTH);
                rd_fire = rd_en && (model_count != 0);
                if (wr_en && rd_en) simultaneous_requests = simultaneous_requests + 1;
                if (wr_en && !wr_fire) blocked_writes = blocked_writes + 1;
                if (rd_en && !rd_fire) blocked_reads = blocked_reads + 1;
                if (rd_fire) begin
                    expected_data = model_memory[model_rp];
                    model_rp = (model_rp + 1) % DEPTH;
                    accepted_reads = accepted_reads + 1;
                end
                if (wr_fire) begin
                    model_memory[model_wp] = data_in;
                    model_wp = (model_wp + 1) % DEPTH;
                    accepted_writes = accepted_writes + 1;
                end
                if (wr_fire && !rd_fire) model_count = model_count + 1;
                else if (!wr_fire && rd_fire) model_count = model_count - 1;
            end
            #1;
            cycles = cycles + 1;
            verify_outputs();
        end
    endtask

    task next_random;
        begin
            random_state = random_state * 32'd1664525 + 32'd1013904223;
        end
    endtask

    initial begin
        passed=0; failed=0; cycles=0; model_count=0;
        model_wp=0; model_rp=0; expected_data=0;
        accepted_writes=0; accepted_reads=0; resets=0;
        simultaneous_requests=0; blocked_writes=0; blocked_reads=0;
        random_state=32'h5A17C0DE;
        rst=0; wr_en=0; rd_en=0; data_in=0;

        if (DEPTH < 2 || DEPTH != (1 << ADDR_WIDTH)) begin
            $display("[FAIL] This regression tests power-of-two DEPTH with matching ADDR_WIDTH");
            $fatal(1, "Unsupported FIFO parameterization for the baseline pointer scheme");
        end

        $display("========== DAY 30 FIFO EQUIVALENCE ==========");
        $display("DATA_WIDTH=%0d DEPTH=%0d ADDR_WIDTH=%0d RANDOM_CYCLES=%0d", DATA_WIDTH, DEPTH, ADDR_WIDTH, RANDOM_CYCLES);

        // Reset / read while empty.
        cycle(1,0,0,0);
        cycle(0,0,1,0);
        // Fill completely and reject an overflow write.
        for (j=0; j<DEPTH; j=j+1) cycle(0,1,0,j+1);
        cycle(0,1,0,'hFF);
        // Full + both requested: read only, per baseline contract.
        cycle(0,1,1,'hA1);
        // Nonfull + nonempty + both: perform both.
        cycle(0,1,1,'hB2);
        // Drain and underflow.
        for (j=0; j<DEPTH+2; j=j+1) cycle(0,0,1,0);
        // Empty + both requested: write only, per baseline contract.
        cycle(0,1,1,'hC3);
        cycle(0,1,1,'hD4);
        cycle(0,0,1,0);
        // Reset during nonempty state; old array words must not be observed.
        cycle(0,1,0,'h88);
        cycle(1,1,1,'h99);
        cycle(0,0,1,0);
        // Heavy pointer wraparound, including repeated empty-to-one transitions.
        for (j=0; j<DEPTH*8; j=j+1) begin
            cycle(0,1,0,j);
            cycle(0,0,1,0);
        end
        // Deterministic mixed traffic with periodic resets.
        for (j=0; j<RANDOM_CYCLES; j=j+1) begin
            next_random();
            if ((j % 487) == 0) begin
                cycle(1,0,0,0);
            end else begin
                // Extract bits from different states, not only low LCG bits.
                cycle(0,random_state[19],random_state[27],random_state[15:0]);
            end
        end
        // Final drain / empty boundary.
        for (j=0; j<DEPTH+2; j=j+1) cycle(0,0,1,0);

        $display("TOTAL CYCLES: %0d",cycles);
        $display("TOTAL CHECKS: %0d",passed+failed);
        $display("PASSED CHECKS: %0d",passed);
        $display("FAILED CHECKS: %0d",failed);
        $display("ACCEPTED WRITES: %0d",accepted_writes);
        $display("ACCEPTED READS: %0d",accepted_reads);
        $display("BLOCKED WRITES: %0d",blocked_writes);
        $display("BLOCKED READS: %0d",blocked_reads);
        $display("SIMULTANEOUS REQUESTS: %0d",simultaneous_requests);
        $display("RESET EVENTS: %0d",resets);

        if (failed == 0 && cycles > RANDOM_CYCLES &&
            accepted_writes > 0 && accepted_reads > 0 &&
            blocked_writes > 0 && blocked_reads > 0 &&
            simultaneous_requests > 0 && resets > 1) begin
            $display("DAY 30 FIFO EQUIVALENCE: PASS");
        end else begin
            $display("DAY 30 FIFO EQUIVALENCE: FAIL");
            $fatal(1, "Coverage criteria or equivalence failed");
        end
        $finish;
    end
endmodule
