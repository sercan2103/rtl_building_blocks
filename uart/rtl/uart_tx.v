module uart_tx #(
    parameter CLK_PER_BIT = 868  // 115200 baud rate with 100 MHz clock => 100000000 / 115200
) (
    input wire clk,
    input wire rst,
    input wire [7:0] tx_data,
    input wire tx_start,
    output wire tx_busy,
    output wire tx
);



// State Parameters
localparam IDLE = 2'b00 , 
           START = 2'b01 , 
           DATA = 2'b10 , 
           STOP = 2'b11 ;

reg [1:0] state, next_state;
reg [$clog2(CLK_PER_BIT)-1:0] clk_count; // width follows the parameter
reg [2:0] bit_idx; // 3 bits to count up to 7
reg [7:0] tx_data_reg;

always @(posedge clk or posedge rst) begin
    if (rst) begin
        state <= IDLE;
        clk_count <=0;
        bit_idx <= 0;
    end else begin
     state <= next_state;
        if (!(clk_count == CLK_PER_BIT - 1) && (state == START || state == DATA || state == STOP)) begin
            clk_count <= clk_count + 1;
        end else begin
            clk_count <= 0;
        end

        if (state == DATA && clk_count == CLK_PER_BIT - 1) begin
            bit_idx <= bit_idx + 1;
        end else if (state == IDLE) begin
            bit_idx <= 0;
        end
    if (state == IDLE && tx_start) begin
            tx_data_reg <= tx_data;
        end
    end
end

always @(*) begin
    case (state)
        IDLE : begin
            if (tx_start) begin
                next_state = START;
            end else begin
                next_state = IDLE;
            end
        end
        START : begin
            if (clk_count == CLK_PER_BIT - 1) begin
                next_state = DATA;
            end else begin
                next_state = START;
            end
        end
        DATA : begin
            if (clk_count == CLK_PER_BIT - 1 && bit_idx == 7) begin
                next_state = STOP;
            end else begin
                next_state = DATA;
            end
        end
        STOP : begin
            if (clk_count == CLK_PER_BIT - 1) begin
                next_state = IDLE;
            end else begin
                next_state = STOP;
            end
        end
        default : begin
            next_state = IDLE;
        end
    endcase
end

assign tx_busy = (state != IDLE);
assign tx = (state == IDLE) ? 1'b1 : 
            (state == START) ? 1'b0 : 
            (state == DATA) ? tx_data_reg[bit_idx] : 
            (state == STOP) ? 1'b1 : 1'b1;

endmodule
