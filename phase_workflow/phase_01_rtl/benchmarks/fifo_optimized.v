`timescale 1ns/1ps

// Externally cycle-compatible with rtl/fifo.v for supported configurations.
// Only FIFO control state/data_out are reset. Storage words are intentionally
// left unreset: occupancy prevents stale words from being read after reset.
module fifo_opt #(
    parameter DATA_WIDTH = 8,
    parameter DEPTH = 4,
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

    wire write_fire = wr_en && !full;
    wire read_fire  = rd_en && !empty;

    assign empty = (count == 0);
    assign full  = (count == DEPTH);

    // No reset on memory. All reads are conditioned on occupancy, so after
    // reset each address must have been written before it can be observed.
    always @(posedge clk) begin
        if (!rst && write_fire)
            memory[write_ptr] <= data_in;
    end

    always @(posedge clk) begin
        if (rst) begin
            write_ptr <= 0;
            read_ptr  <= 0;
            count     <= 0;
            data_out  <= 0;
        end else begin
            if (write_fire)
                write_ptr <= write_ptr + 1'b1;
            if (read_fire) begin
                data_out <= memory[read_ptr];
                read_ptr <= read_ptr + 1'b1;
            end
            case ({write_fire, read_fire})
                2'b10: count <= count + 1'b1;
                2'b01: count <= count - 1'b1;
                default: count <= count;
            endcase
        end
    end
endmodule
