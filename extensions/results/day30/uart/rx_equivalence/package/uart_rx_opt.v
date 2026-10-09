`timescale 1ns/1ps
// Candidate UART RX optimization: replace indexed payload writes with
// an LSB-first receive shift register. All externally visible timing
// intentionally matches uart_rx.v. No PPA improvement is assumed.
module uart_rx_opt #(
    parameter integer CLKS_PER_BIT = 16
)(
    input  wire       clk,
    input  wire       rst,
    input  wire       rx,
    output reg  [7:0] data_out,
    output reg        valid,
    output reg        busy,
    output reg        framing_error
);
    localparam [1:0] IDLE=0, START=1, DATA=2, STOP=3;
    localparam integer CW = (CLKS_PER_BIT <= 1) ? 1 : $clog2(CLKS_PER_BIT);
    reg [1:0] state;
    reg [CW-1:0] tick;
    reg [2:0] bit_idx;
    reg [7:0] payload;
    reg rx_meta, rx_sync;

    always @(posedge clk) begin
        if (rst) begin
            state <= IDLE;
            tick <= 0;
            bit_idx <= 0;
            payload <= 0;
            rx_meta <= 1'b1;
            rx_sync <= 1'b1;
            data_out <= 0;
            valid <= 0;
            busy <= 0;
            framing_error <= 0;
        end else begin
            rx_meta <= rx;
            rx_sync <= rx_meta;
            valid <= 0;
            framing_error <= 0;
            case (state)
                IDLE: begin
                    busy <= 0;
                    tick <= 0;
                    if (!rx_sync) begin
                        busy <= 1;
                        state <= START;
                    end
                end
                START: begin
                    if (tick == (CLKS_PER_BIT/2)-1) begin
                        tick <= 0;
                        if (!rx_sync)
                            state <= DATA;
                        else begin
                            state <= IDLE;
                            busy <= 0;
                        end
                    end else
                        tick <= tick + 1'b1;
                end
                DATA: begin
                    if (tick == CLKS_PER_BIT-1) begin
                        tick <= 0;
                        // LSB-first serial input shifts into MSB position.
                        // After 8 samples, payload[7:0] = input byte[7:0].
                        payload <= {rx_sync, payload[7:1]};
                        if (bit_idx == 7) begin
                            bit_idx <= 0;
                            state <= STOP;
                        end else
                            bit_idx <= bit_idx + 1'b1;
                    end else
                        tick <= tick + 1'b1;
                end
                STOP: begin
                    if (tick == CLKS_PER_BIT-1) begin
                        tick <= 0;
                        state <= IDLE;
                        busy <= 0;
                        if (rx_sync) begin
                            data_out <= payload;
                            valid <= 1;
                        end else
                            framing_error <= 1;
                    end else
                        tick <= tick + 1'b1;
                end
                default: state <= IDLE;
            endcase
        end
    end
endmodule
