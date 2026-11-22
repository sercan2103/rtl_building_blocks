# UART

8N1 UART transmitter and receiver in Verilog, verified with cocotb.

## Files

| File | Description |
|---|---|
| `rtl/uart_tx.v` | Transmitter |
| `rtl/uart_rx.v` | Receiver (2-FF synchronizer, mid-bit sampling) |
| `rtl/uart_top.v` | TX → RX loopback on separate clocks |
| `../common/rtl/basicff.v` | Synchronizer flip-flop (shared) |

## Running the tests

Requires Icarus Verilog and cocotb.

```bash
cd tb/uart_rx   # or tb/uart_tx, tb/uart_loopback
make
```

## Results

| Testbench | Result |
|---|---|
| `uart_tx` | 2/2 pass |
| `uart_rx` | 5/5 pass |
| `uart_loopback` | 3/3 pass |
