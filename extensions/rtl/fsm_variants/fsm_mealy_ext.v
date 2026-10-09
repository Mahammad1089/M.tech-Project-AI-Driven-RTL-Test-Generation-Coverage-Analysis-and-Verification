`timescale 1ns/1ps

module fsm_mealy_ext #(
    parameter integer LENGTH = 4,
    parameter [LENGTH-1:0] PATTERN = 4'b1011,
    parameter integer OVERLAP = 1
)(
    input wire clk,
    input wire rst,
    input wire din,
    output reg detected
);

    localparam integer STATE_WIDTH =
        (LENGTH <= 1) ? 1 : $clog2(LENGTH);

    reg [STATE_WIDTH-1:0] state;
    reg [STATE_WIDTH-1:0] next_state;

    reg [LENGTH-1:0] sequence_bits;

    integer candidate_len;
    integer idx;
    integer k;
    integer j;
    integer prefix_ok;
    integer selected;

    // Combinational next-state and Mealy output logic.
    always @(*) begin

        sequence_bits = {LENGTH{1'b0}};
        candidate_len = 0;

        // Reconstruct the prefix represented by the state.
        // Bits are inserted in chronological order.
        for (idx = 0; idx < LENGTH; idx = idx + 1) begin
            if (idx < state) begin
                sequence_bits =
                    (sequence_bits << 1) |
                    PATTERN[LENGTH-1-idx];

                candidate_len = candidate_len + 1;
            end
        end

        // Append the current input bit.
        sequence_bits = (sequence_bits << 1) | din;
        candidate_len = candidate_len + 1;

        // Detect a complete pattern.
        detected = 1'b0;

        if ((candidate_len == LENGTH) &&
            (sequence_bits == PATTERN) &&
            !rst) begin
            detected = 1'b1;
        end

        // Default next state: no prefix matched.
        next_state = {STATE_WIDTH{1'b0}};
        selected = 0;
        prefix_ok = 0;

        // In non-overlapping mode, discard the completed
        // match and restart from state zero.
        if (!(detected && (OVERLAP == 0))) begin

            // Find the longest candidate suffix that
            // equals a prefix of PATTERN.
            for (k = LENGTH - 1; k >= 1; k = k - 1) begin

                if ((k <= candidate_len) && !selected) begin

                    prefix_ok = 1;

                    for (j = 0; j < k; j = j + 1) begin
                        if (sequence_bits[k-1-j] !=
                            PATTERN[LENGTH-1-j]) begin
                            prefix_ok = 0;
                        end
                    end

                    if (prefix_ok) begin
                        next_state = k;
                        selected = 1;
                    end
                end
            end
        end

        if (rst)
            next_state = {STATE_WIDTH{1'b0}};
    end

    // Synchronous active-high reset.
    always @(posedge clk) begin
        if (rst)
            state <= {STATE_WIDTH{1'b0}};
        else
            state <= next_state;
    end

endmodule
