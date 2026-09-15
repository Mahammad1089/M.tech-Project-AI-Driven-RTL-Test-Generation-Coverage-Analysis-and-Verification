`timescale 1ns/1ps

module day1_test;

reg a;
reg b;

wire y;

assign y = a & b;

initial begin
    
    $dumpfile("results/day1_test.vcd");
    $dumpvars(0, day1_test);

    $display("==========================");
    $display("DAY 1 VERILOG TEST");
    $display("==========================");

    a = 0;
    b = 0;

    #10;

    $display(
        "a=%b b=%b y=%b",
        a,
        b,
        y
    );

    a = 1;
    b = 1;

    #10;

    $display(
        "a=%b b=%b y=%b",
        a,
        b,
        y
    );

    if (y == 1'b1)
        $display("SIMULATION PASS");
    else
        $display("SIMULATION FAIL");

    $finish;

end

endmodule
