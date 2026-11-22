module uart_rx #(
    parameter CLK_PER_BIT = 868
) (
    input  wire       clk,
    input  wire       rst,
    input  wire       rx,
    output wire       rx_ready,
    output reg  [7:0] rx_data,
    output reg        rx_valid,
    output reg        rx_frame_err
);

localparam IDLE = 2'b00 ,
           START = 2'b01 ,
           DATA = 2'b10 ,
           STOP = 2'b11 ;

reg [1:0] state, next_state;
reg [$clog2(CLK_PER_BIT)-1:0] clk_count;
reg [2:0] bit_idx;
reg [7:0] rx_data_reg;
wire rx_sync ;
wire rx_ff ;
sync_FF #(.WIDTH(1)) rx_sync_ff1 (
    .clk(clk),
    .rst(rst),
    .d(rx),
    .q(rx_ff)
);
sync_FF #(.WIDTH(1)) rx_sync_ff2 (
    .clk(clk),
    .rst(rst),
    .d(rx_ff),
    .q(rx_sync)
);

always @(posedge clk or posedge rst) begin
    if (rst) begin
        state <= IDLE;
        clk_count <= 0;
        bit_idx <= 0;
        rx_data <= 0;
        rx_valid <= 0;
        rx_frame_err <= 0;
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
        if (state == DATA && clk_count == (CLK_PER_BIT>>1)) begin
            rx_data_reg[bit_idx] <= rx_sync;
        end
        if ((state == STOP) && (clk_count == (CLK_PER_BIT>>1)) && (rx_sync)) begin
            rx_data <= rx_data_reg;
            rx_valid <= 1;
            rx_frame_err <= 0;
        end else if (state == STOP && (clk_count == (CLK_PER_BIT>>1)) && (!rx_sync)) begin
            rx_valid <= 0;
            rx_frame_err <= 1;
        end else begin
            rx_valid <= 0;
            rx_frame_err <= 0;
        end
    end
end

always @(*) begin
    case (state)
        IDLE : begin
            if (!rx_sync) begin
                next_state = START;
            end else begin
                next_state = IDLE;
            end
        end
        START : begin
            if (clk_count == CLK_PER_BIT - 1) begin
                next_state = DATA;
            end else if (clk_count == (CLK_PER_BIT>>1) && rx_sync) begin
                next_state = IDLE;
            end else begin
                next_state = START;
            end
        end
        DATA : begin
            if ((clk_count == CLK_PER_BIT - 1)&& (bit_idx == 7)) begin
                next_state = STOP;
            end else begin
                next_state = DATA;
            end
        end
        STOP : begin
            if (clk_count == CLK_PER_BIT>>1) begin
                next_state = IDLE;
            end else begin
                next_state = STOP;
            end
        end
        default : next_state = IDLE;
    endcase
end

assign rx_ready = (state == IDLE) && (rx_sync);

endmodule