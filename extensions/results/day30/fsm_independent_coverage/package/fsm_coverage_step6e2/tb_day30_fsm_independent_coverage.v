`timescale 1ns/1ps

// Independent, four-variant verification for one selected sequence pattern.
// Compares two Mealy outputs before the sampling edge and two Moore outputs
// after the sampling edge against one stream-oriented reference model.
module tb_day30_fsm_independent_coverage;
    parameter integer LENGTH = 4;
    parameter [LENGTH-1:0] PATTERN = 4'b1011;
    parameter integer RANDOM_CYCLES = 3000;

    reg clk = 1'b0;
    reg rst = 1'b1;
    reg din = 1'b0;
    wire mealy_overlap;
    wire mealy_nonoverlap;
    wire moore_overlap;
    wire moore_nonoverlap;

    fsm_mealy_ext #(.LENGTH(LENGTH), .PATTERN(PATTERN), .OVERLAP(1)) m_ov (
        .clk(clk), .rst(rst), .din(din), .detected(mealy_overlap)
    );
    fsm_mealy_ext #(.LENGTH(LENGTH), .PATTERN(PATTERN), .OVERLAP(0)) m_no (
        .clk(clk), .rst(rst), .din(din), .detected(mealy_nonoverlap)
    );
    fsm_moore_ext #(.LENGTH(LENGTH), .PATTERN(PATTERN), .OVERLAP(1)) r_ov (
        .clk(clk), .rst(rst), .din(din), .detected(moore_overlap)
    );
    fsm_moore_ext #(.LENGTH(LENGTH), .PATTERN(PATTERN), .OVERLAP(0)) r_no (
        .clk(clk), .rst(rst), .din(din), .detected(moore_nonoverlap)
    );

    always #5 clk = ~clk;

    reg [LENGTH-1:0] history;
    reg [LENGTH-1:0] new_history;
    reg expected_overlap;
    reg expected_nonoverlap;
    integer valid_bits;
    integer bit_index;
    integer last_nonoverlap_end;
    integer total_checks;
    integer failures;
    integer cycles;
    integer reset_events;
    integer positive_overlap;
    integer positive_nonoverlap;
    integer negative_overlap;
    integer negative_nonoverlap;
    integer suppressed_opportunities;
    integer proper_border;
    integer b;
    integer j;
    integer equal_border;
    integer i;
    integer n;
    integer val;
    integer p;
    reg [31:0] random_state;

    task automatic compare;
        input [127:0] signal_name;
        input actual;
        input expected;
        begin
            total_checks = total_checks + 1;
            if (actual !== expected) begin
                failures = failures + 1;
                $display("[FAIL] %0s cycle=%0d rst=%b din=%b expected=%b actual=%b", signal_name, cycles, rst, din, expected, actual);
                $fatal(1, "Independent FSM reference mismatch");
            end
        end
    endtask

    task automatic reset_dut;
        begin
            @(negedge clk);
            rst = 1'b1;
            din = 1'b0;
            @(posedge clk);
            #1;
            compare("mealy_overlap", mealy_overlap, 1'b0);
            compare("mealy_nonoverlap", mealy_nonoverlap, 1'b0);
            compare("moore_overlap", moore_overlap, 1'b0);
            compare("moore_nonoverlap", moore_nonoverlap, 1'b0);
            history = {LENGTH{1'b0}};
            valid_bits = 0;
            bit_index = 0;
            last_nonoverlap_end = -1;
            reset_events = reset_events + 1;
        end
    endtask

    task automatic apply_bit;
        input bit_value;
        begin
            @(negedge clk);
            rst = 1'b0;
            din = bit_value;

            // Independent sliding-window specification. A non-overlapping
            // detection is accepted only if it begins after the last
            // accepted non-overlapping match has ended.
            new_history = (history << 1) | bit_value;
            expected_overlap = (valid_bits >= LENGTH-1) &&
                               (new_history == PATTERN);
            expected_nonoverlap = expected_overlap &&
                ((bit_index - LENGTH + 1) > last_nonoverlap_end);

            if (expected_overlap) positive_overlap = positive_overlap + 1;
            else negative_overlap = negative_overlap + 1;
            if (expected_nonoverlap) positive_nonoverlap = positive_nonoverlap + 1;
            else negative_nonoverlap = negative_nonoverlap + 1;
            if (expected_overlap && !expected_nonoverlap)
                suppressed_opportunities = suppressed_opportunities + 1;

            // Mealy output is combinational on current input and old state.
            #1;
            compare("mealy_overlap", mealy_overlap, expected_overlap);
            compare("mealy_nonoverlap", mealy_nonoverlap, expected_nonoverlap);

            // Moore output reflects the newly registered state after clock.
            @(posedge clk);
            #1;
            compare("moore_overlap", moore_overlap, expected_overlap);
            compare("moore_nonoverlap", moore_nonoverlap, expected_nonoverlap);

            history = new_history;
            if (valid_bits < LENGTH) valid_bits = valid_bits + 1;
            if (expected_nonoverlap) last_nonoverlap_end = bit_index;
            bit_index = bit_index + 1;
            cycles = cycles + 1;
        end
    endtask

    task automatic send_pattern;
        integer q;
        begin
            for (q=LENGTH-1; q>=0; q=q-1)
                apply_bit(PATTERN[q]);
        end
    endtask

    initial begin
        history = {LENGTH{1'b0}};
        new_history = {LENGTH{1'b0}};
        expected_overlap = 0;
        expected_nonoverlap = 0;
        valid_bits = 0;
        bit_index = 0;
        last_nonoverlap_end = -1;
        total_checks = 0;
        failures = 0;
        cycles = 0;
        reset_events = 0;
        positive_overlap = 0;
        positive_nonoverlap = 0;
        negative_overlap = 0;
        negative_nonoverlap = 0;
        suppressed_opportunities = 0;
        proper_border = 0;
        random_state = 32'h419a2cde;

        if (LENGTH < 2 || LENGTH > 16)
            $fatal(1, "Unsupported LENGTH: %0d", LENGTH);

        // Find the maximum proper prefix/suffix border of the pattern.
        for (b=1; b<LENGTH; b=b+1) begin
            equal_border = 1;
            for (j=0; j<b; j=j+1) begin
                if (PATTERN[LENGTH-1-j] !== PATTERN[b-1-j])
                    equal_border = 0;
            end
            if (equal_border) proper_border = b;
        end

        $display("========== DAY 30 FSM INDEPENDENT COVERAGE ==========");
        $display("PATTERN=%b LENGTH=%0d PROPER_BORDER=%0d", PATTERN, LENGTH, proper_border);

        // First isolated match.
        reset_dut();
        send_pattern();

        // Deliberate overlapping match: P + P[border ... LENGTH-1].
        // For an unbordered pattern, back-to-back full patterns are used.
        reset_dut();
        send_pattern();
        for (p=LENGTH-1-proper_border; p>=0; p=p-1)
            apply_bit(PATTERN[p]);

        // Repeated patterns, long runs, and an interrupted partial match.
        reset_dut();
        for (i=0; i<12; i=i+1) send_pattern();
        reset_dut();
        for (i=0; i<100; i=i+1) apply_bit(1'b0);
        for (i=0; i<100; i=i+1) apply_bit(1'b1);
        reset_dut();
        for (i=LENGTH-1; i>=LENGTH/2; i=i-1)
            apply_bit(PATTERN[i]);
        reset_dut();
        send_pattern();

        // Exhaustive binary streams through eight bits, separated by reset.
        for (n=1; n<=8; n=n+1) begin
            for (val=0; val<(1<<n); val=val+1) begin
                reset_dut();
                for (i=n-1; i>=0; i=i-1)
                    apply_bit((val >> i) & 1);
            end
        end

        reset_dut();
        for (i=0; i<RANDOM_CYCLES; i=i+1) begin
            // Fixed deterministic LCG, independent of the DUT internals.
            random_state = random_state * 32'd1664525 + 32'd1013904223;
            apply_bit(random_state[22]);
            if ((i % 137) == 136) reset_dut();
        end

        $display("TOTAL CYCLES: %0d", cycles);
        $display("TOTAL CHECKS: %0d", total_checks);
        $display("PASSED CHECKS: %0d", total_checks-failures);
        $display("FAILED CHECKS: %0d", failures);
        $display("RESET EVENTS: %0d", reset_events);
        $display("OVERLAP DETECTIONS: %0d", positive_overlap);
        $display("NONOVERLAP DETECTIONS: %0d", positive_nonoverlap);
        $display("OVERLAP NEGATIVE CYCLES: %0d", negative_overlap);
        $display("NONOVERLAP NEGATIVE CYCLES: %0d", negative_nonoverlap);
        $display("SUPPRESSED OVERLAP OPPORTUNITIES: %0d", suppressed_opportunities);
        $display("PROPER BORDER LENGTH: %0d", proper_border);

        if (failures != 0 || reset_events < 5 ||
            positive_overlap == 0 || positive_nonoverlap == 0 ||
            negative_overlap == 0 || negative_nonoverlap == 0 ||
            (proper_border > 0 && suppressed_opportunities == 0) ||
            (proper_border == 0 && suppressed_opportunities != 0) ||
            total_checks != 4*(cycles+reset_events)) begin
            $display("DAY 30 FSM INDEPENDENT COVERAGE: FAIL");
            $fatal(1, "Insufficient coverage or incorrect counters");
        end
        $display("DAY 30 FSM INDEPENDENT COVERAGE: PASS");
        $finish;
    end
endmodule
