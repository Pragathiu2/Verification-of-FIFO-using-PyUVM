`timescale 1ns / 1ps

module FIFO(input clk, rst, wr, rd,
            input [7:0] din, output [7:0] dout,
            output empty, full);
  
  // Pointers for write and read operations
  reg [3:0] wptr = 0, rptr = 0;
  
  // Counter for tracking the number of elements in the FIFO
  reg [4:0] cnt = 0;
  
  // Memory array to store data
  reg [7:0] mem [15:0];

  always @(posedge clk)
    begin
      if (rst == 1'b1)
        begin
          // Reset the pointers and counter when the reset signal is asserted
          wptr   <= 0;
          rptr   <= 0;
          cnt    <= 0;
        end
      else if (wr && !full)
        begin
          // Write data to the FIFO if it's not full
          mem[wptr] <= din;
          wptr      <= wptr + 1;
          cnt       <= cnt + 1;
        end
      else if (rd && !empty)
        begin
          // Read data from the FIFO if it's not empty
          dout_t <= mem[rptr];
          rptr   <= rptr + 1;
          cnt    <= cnt - 1;
        end
    end

  // Determine if the FIFO is empty or full
  assign empty = (cnt == 0) ? 1'b1 : 1'b0;
  assign full  = (cnt == 16) ? 1'b1 : 1'b0;
  
  initial begin
  $dumpfile("dump.vcd");
  $dumpvars(1,FIFO);
  end
endmodule
