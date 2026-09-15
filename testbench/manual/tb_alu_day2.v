`timescale 1ns/1ps

module tb_alu_day2;

reg  [3:0] a;
reg  [3:0] b;
reg  [2:0] sel;

wire [3:0] y;

alu dut (
    .a(a),
    .b(b),
    .sel(sel),
    .y(y)
);

initial begin

    $dumpfile("results/alu/day2/alu_day2.vcd");
    $dumpvars(0, tb_alu_day2);

    $display("====================================");
    $display("DAY 2 - 4-BIT ALU VALIDATION");
    $display("====================================");

    a = 4'b0101;
    b = 4'b0011;

    sel = 3'b000;
    #10;
    $display("ADD         : y=%b", y);

    sel = 3'b001;
    #10;
    $display("SUB         : y=%b", y);

    sel = 3'b010;
    #10;
    $display("AND         : y=%b", y);

    sel = 3'b011;
    #10;
    $display("OR          : y=%b", y);

    sel = 3'b100;
    #10;
    $display("XOR         : y=%b", y);

    sel = 3'b101;
    #10;
    $display("NOT         : y=%b", y);

    sel = 3'b110;
    #10;
    $display("SHIFT LEFT  : y=%b", y);

    sel = 3'b111;
    #10;
    $display("SHIFT RIGHT : y=%b", y);

    $display("====================================");
    $display("DAY 2 ALU TEST FINISHED");
    $display("====================================");

    $finish;

end

endmodule
