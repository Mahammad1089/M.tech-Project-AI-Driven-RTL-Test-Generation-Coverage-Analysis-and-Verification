`timescale 1ns/1ps
module tb_day30_fsm_functional_audit;
  reg clk=0, rst=0, din=0;
  always #5 clk=~clk;
  wire original_detected, mealy_overlap, mealy_no_overlap;
  wire moore_overlap, moore_no_overlap;
  fsm_1011 original_dut(.clk(clk),.rst(rst),.din(din),.detected(original_detected));
  fsm_mealy_ext #(.LENGTH(4),.PATTERN(4'b1011),.OVERLAP(1)) mealy_ov(.clk(clk),.rst(rst),.din(din),.detected(mealy_overlap));
  fsm_mealy_ext #(.LENGTH(4),.PATTERN(4'b1011),.OVERLAP(0)) mealy_no(.clk(clk),.rst(rst),.din(din),.detected(mealy_no_overlap));
  fsm_moore_ext #(.LENGTH(4),.PATTERN(4'b1011),.OVERLAP(1)) moore_ov(.clk(clk),.rst(rst),.din(din),.detected(moore_overlap));
  fsm_moore_ext #(.LENGTH(4),.PATTERN(4'b1011),.OVERLAP(0)) moore_no(.clk(clk),.rst(rst),.din(din),.detected(moore_no_overlap));
  integer checks=0, failures=0, cycles=0, matches_ov=0, matches_no=0;
  integer len_ov=0, len_no=0;
  reg [3:0] history_ov=0, history_no=0;
  reg expected_ov, expected_no;
  integer seed=32'h4c2910ab;
  integer n;
  task check;
    input [255:0] label;
    input actual, expected;
    begin
      checks=checks+1;
      if (actual !== expected) begin
        failures=failures+1;
        $display("[FAIL] cycle=%0d %0s actual=%b expected=%b din=%b rst=%b",cycles,label,actual,expected,din,rst);
      end
    end
  endtask
  task reset_duts;
    begin
      @(negedge clk); rst=1; din=0;
      @(posedge clk); #1;
      history_ov=0; history_no=0; len_ov=0; len_no=0;
      check("reset original",original_detected,0);
      check("reset extended Mealy overlap",mealy_overlap,0);
      check("reset extended Mealy nonoverlap",mealy_no_overlap,0);
      check("reset Moore overlap",moore_overlap,0);
      check("reset Moore nonoverlap",moore_no_overlap,0);
      @(negedge clk); rst=0;
    end
  endtask
  task send_bit;
    input bit_value;
    begin
      // All stimulus changes on falling edges, well before sampling.
      din=bit_value;
      expected_ov=(len_ov>=3 && {history_ov[2:0],bit_value}==4'b1011);
      expected_no=(len_no>=3 && {history_no[2:0],bit_value}==4'b1011);
      #1;
      cycles=cycles+1;
      check("original Mealy",original_detected,expected_ov);
      check("extended Mealy overlap",mealy_overlap,expected_ov);
      check("extended Mealy nonoverlap",mealy_no_overlap,expected_no);
      @(posedge clk); #1;
      check("extended Moore overlap",moore_overlap,expected_ov);
      check("extended Moore nonoverlap",moore_no_overlap,expected_no);
      if(expected_ov) matches_ov=matches_ov+1;
      if(expected_no) matches_no=matches_no+1;
      history_ov={history_ov[2:0],bit_value};
      if(len_ov<4) len_ov=len_ov+1;
      if(expected_no) begin history_no=0; len_no=0; end
      else begin
        history_no={history_no[2:0],bit_value};
        if(len_no<4) len_no=len_no+1;
      end
      @(negedge clk);
    end
  endtask
  task send_word;
    input [31:0] bits;
    input integer length;
    integer i;
    begin for(i=length-1;i>=0;i=i-1) send_bit(bits[i]); end
  endtask
  initial begin
    $display("DAY 30 STEP 4C - FSM FUNCTIONAL AUDIT");
    reset_duts();
    send_word(4'b1011,4);
    send_word(7'b1011011,7);
    send_word(8'b11101011,8);
    send_word(8'b00000000,8);
    reset_duts();
    send_word(12'b101101110110,12);
    for(n=0;n<512;n=n+1) send_bit($random(seed)&1);
    $display("========================================");
    $display("TOTAL CHECKS: %0d",checks);
    $display("PASSED CHECKS: %0d",checks-failures);
    $display("FAILED CHECKS: %0d",failures);
    $display("CYCLES: %0d",cycles);
    $display("REFERENCE OVERLAP MATCHES: %0d",matches_ov);
    $display("REFERENCE NONOVERLAP MATCHES: %0d",matches_no);
    if(failures==0) $display("DAY 30 STEP 4C: PASS");
    else $display("DAY 30 STEP 4C: FAIL");
    $finish;
  end
endmodule
