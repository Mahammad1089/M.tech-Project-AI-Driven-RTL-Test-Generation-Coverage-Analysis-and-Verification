module fsm_1011 (
    input  wire clk,
    input  wire rst,
    input  wire din,
    output reg  detected
);

    localparam [1:0]
        IDLE = 2'b00,
        S1   = 2'b01,
        S10  = 2'b10,
        S101 = 2'b11;

    reg [1:0] current_state;
    reg [1:0] next_state;

    /*
     * State register
     *
     * Synchronous active-high reset.
     */
    always @(posedge clk) begin
        if (rst)
            current_state <= IDLE;
        else
            current_state <= next_state;
    end

    /*
     * Next-state and output logic.
     *
     * This is a Mealy-style detector.
     */
    always @(*) begin

        next_state = current_state;
        detected   = 1'b0;

        case (current_state)

            IDLE: begin
                if (din)
                    next_state = S1;
                else
                    next_state = IDLE;
            end

            S1: begin
                if (din)
                    next_state = S1;
                else
                    next_state = S10;
            end

            S10: begin
                if (din)
                    next_state = S101;
                else
                    next_state = IDLE;
            end

            S101: begin
                if (din) begin
                    next_state = S1;
                    detected   = 1'b1;
                end
                else begin
                    next_state = S10;
                end
            end

            default: begin
                next_state = IDLE;
                detected   = 1'b0;
            end

        endcase
    end

endmodule
