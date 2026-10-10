`timescale 1ns/1ps

module fifo #(
    parameter DATA_WIDTH = 8,
    parameter DEPTH      = 4,
    parameter ADDR_WIDTH = 2
)(
    input                       clk,
    input                       rst,

    input                       wr_en,
    input                       rd_en,

    input      [DATA_WIDTH-1:0] data_in,
    output reg [DATA_WIDTH-1:0] data_out,

    output                      full,
    output                      empty
);

    reg [DATA_WIDTH-1:0] memory [0:DEPTH-1];

    reg [ADDR_WIDTH-1:0] write_ptr;
    reg [ADDR_WIDTH-1:0] read_ptr;

    reg [ADDR_WIDTH:0] count;

    assign empty = (count == 0);
    assign full  = (count == DEPTH);

    integer i;

    always @(posedge clk) begin

        if (rst) begin

            write_ptr <= 0;
            read_ptr  <= 0;
            count     <= 0;
            data_out  <= 0;

            for (i = 0; i < DEPTH; i = i + 1) begin
                memory[i] <= 0;
            end

        end
        else begin

            case ({wr_en && !full, rd_en && !empty})

                2'b10: begin
                    memory[write_ptr] <= data_in;
                    write_ptr <= write_ptr + 1'b1;
                    count <= count + 1'b1;
                end

                2'b01: begin
                    data_out <= memory[read_ptr];
                    read_ptr <= read_ptr + 1'b1;
                    count <= count - 1'b1;
                end

                2'b11: begin
                    memory[write_ptr] <= data_in;
                    write_ptr <= write_ptr + 1'b1;

                    data_out <= memory[read_ptr];
                    read_ptr <= read_ptr + 1'b1;

                    count <= count;
                end

                default: begin
                    count <= count;
                end

            endcase
        end
    end

endmodule
