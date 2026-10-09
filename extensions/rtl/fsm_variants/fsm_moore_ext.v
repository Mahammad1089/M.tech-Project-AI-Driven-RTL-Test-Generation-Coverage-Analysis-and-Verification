`timescale 1ns/1ps

module fsm_moore_ext #(
    parameter integer LENGTH = 4,
    parameter [LENGTH-1:0] PATTERN = 4'b1011,
    parameter integer OVERLAP = 1
)(
    input wire clk,
    input wire rst,
    input wire din,
    output wire detected
);

    localparam integer STATE_WIDTH =
        (LENGTH <= 1) ? 1 : $clog2(LENGTH + 1);

    reg [STATE_WIDTH-1:0] state;
    reg [STATE_WIDTH-1:0] next_state;

    reg [LENGTH:0] candidate_bits;

    integer effective_length;
    integer i;
    integer k;
    integer j;
    integer prefix_match;
    integer selected;

    // State LENGTH represents a complete detection.
    // Therefore the output depends only on registered state.
    assign detected = (state == LENGTH);

    always @(*) begin
        candidate_bits = {(LENGTH+1){1'b0}};
        effective_length = 0;

        next_state = {STATE_WIDTH{1'b0}};
        selected = 0;
        prefix_match = 0;

        // After detection:
        // OVERLAP=1: preserve the matched pattern history.
        // OVERLAP=0: start matching a new sequence.
        if (state == LENGTH) begin
            if (OVERLAP != 0)
                effective_length = LENGTH;
            else
                effective_length = 0;
        end
        else begin
            effective_length = state;
        end

        // Reconstruct the recognized prefix.
        for (i = 0; i < LENGTH; i = i + 1) begin
            if (i < effective_length) begin
                candidate_bits =
                    (candidate_bits << 1) |
                    PATTERN[LENGTH-1-i];
            end
        end

        // Append the current input.
        candidate_bits = (candidate_bits << 1) | din;
        effective_length = effective_length + 1;

        // Search for the longest suffix matching
        // a prefix of the configured pattern.
        // Include LENGTH so complete matches enter
        // the Moore detection state.
        for (k = LENGTH; k >= 1; k = k - 1) begin

            if ((k <= effective_length) && !selected) begin

                prefix_match = 1;

                for (j = 0; j < LENGTH; j = j + 1) begin
                    if (j < k) begin
                        if (candidate_bits[k-1-j] !=
                            PATTERN[LENGTH-1-j]) begin
                            prefix_match = 0;
                        end
                    end
                end

                if (prefix_match) begin
                    next_state = k;
                    selected = 1;
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
