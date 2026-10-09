`timescale 1ns/1ps
module uart_tx #(
    parameter integer CLKS_PER_BIT = 16
)(
    input wire clk,
    input wire rst,
    input wire start,
    input wire [7:0] data_in,
    output reg tx,
    output reg busy,
    output reg done
);
    localparam [1:0] IDLE=0, START=1, DATA=2, STOP=3;
    localparam integer CW = (CLKS_PER_BIT <= 1) ? 1 : $clog2(CLKS_PER_BIT);
    reg [1:0] state;
    reg [CW-1:0] tick;
    reg [2:0] bit_idx;
    reg [7:0] payload;
    always @(posedge clk) begin
        if (rst) begin
            state<=IDLE; tick<=0; bit_idx<=0; payload<=0;
            tx<=1'b1; busy<=0; done<=0;
        end else begin
            done<=0;
            case (state)
                IDLE: begin
                    tx<=1; busy<=0; tick<=0;
                    if (start) begin
                        payload<=data_in; busy<=1; tx<=0; state<=START;
                    end
                end
                START: begin
                    if (tick == CLKS_PER_BIT-1) begin
                        tick<=0; bit_idx<=0; tx<=payload[0]; state<=DATA;
                    end else tick<=tick+1'b1;
                end
                DATA: begin
                    if (tick == CLKS_PER_BIT-1) begin
                        tick<=0;
                        if (bit_idx==7) begin tx<=1; state<=STOP; end
                        else begin bit_idx<=bit_idx+1'b1; tx<=payload[bit_idx+1'b1]; end
                    end else tick<=tick+1'b1;
                end
                STOP: begin
                    if (tick == CLKS_PER_BIT-1) begin
                        tick<=0; state<=IDLE; busy<=0; done<=1; tx<=1;
                    end else tick<=tick+1'b1;
                end
                default: state<=IDLE;
            endcase
        end
    end
endmodule
