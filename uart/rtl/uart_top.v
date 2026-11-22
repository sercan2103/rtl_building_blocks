module uart_top #(
parameter CLKA_HZ = 100_000_000, CLKB_HZ = 50_000_000, BAUD = 115_200
)( 
    input wire clka,
    input wire clkb,
    input wire rst,
    input wire [7:0] tx_data,
    input wire tx_start,
    output wire tx_busy,
    output wire [7:0] rx_data,
    output wire rx_ready,
    output wire rx_valid,
    output wire rx_frame_err,
    output wire serial_out 
);

wire tx;
localparam TX_CPB = CLKA_HZ / BAUD;
localparam RX_CPB = CLKB_HZ / BAUD;
uart_tx #(
    .CLK_PER_BIT(TX_CPB)
) uart_tx_inst (
    .clk(clka),
    .rst(rst),
    .tx_data(tx_data),
    .tx_start(tx_start),
    .tx_busy(tx_busy),
    .tx(tx)
);
uart_rx #(
    .CLK_PER_BIT(RX_CPB)
) uart_rx_inst (
    .clk(clkb),
    .rst(rst),
    .rx(tx),
    .rx_data(rx_data),
    .rx_ready(rx_ready),
    .rx_valid(rx_valid),
    .rx_frame_err(rx_frame_err)
);
assign serial_out = tx;

endmodule