`timescale 1ns/1ps

module alu_opt (
    input  wire [3:0] a,
    input  wire [3:0] b,
    input  wire [2:0] sel,
    output reg  [3:0] y
);

    // Shared arithmetic hardware for ADD and SUB.
    wire subtract;
    wire [3:0] modified_b;
    wire [3:0] arithmetic_result;

    assign subtract = sel[0];

    // SUB: invert B and add 1.
    // ADD: use B unchanged and add 0.
    assign modified_b = b ^ {4{subtract}};

    assign arithmetic_result =
        a + modified_b + {3'b000, subtract};

    // Other combinational ALU operations.
    wire [3:0] and_result;
    wire [3:0] or_result;
    wire [3:0] xor_result;
    wire [3:0] not_result;
    wire [3:0] shift_left_result;
    wire [3:0] shift_right_result;

    assign and_result         = a & b;
    assign or_result          = a | b;
    assign xor_result         = a ^ b;
    assign not_result         = ~a;
    assign shift_left_result  = a << 1;
    assign shift_right_result = a >> 1;

    always @(*) begin
        case (sel)
            3'b000: y = arithmetic_result;
            3'b001: y = arithmetic_result;
            3'b010: y = and_result;
            3'b011: y = or_result;
            3'b100: y = xor_result;
            3'b101: y = not_result;
            3'b110: y = shift_left_result;
            3'b111: y = shift_right_result;
            default: y = 4'b0000;
        endcase
    end

endmodule
