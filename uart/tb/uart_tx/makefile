# Hangi simülatör: Icarus Verilog
SIM ?= icarus

# Tasarım dili
TOPLEVEL_LANG = verilog

# Test edilecek Verilog dosyası (bu klasörden iki üst klasöre çık, rtl'e in)
VERILOG_SOURCES = $(PWD)/../../rtl/uart_tx.v

# Test edilecek modülün adı (Verilog'daki "module uart_tx")
COCOTB_TOPLEVEL = uart_tx

# Python test dosyasının adı (.py olmadan)
COCOTB_TEST_MODULES = test_uart_tx

# Simülasyonu hızlandırmak için: CLK_PER_BIT parametresini 868 yerine 8 yap
COMPILE_ARGS += -Puart_tx.CLK_PER_BIT=8

# cocotb'nin hazır kuralları (make komutunun asıl işini yapan kısım)
include $(shell cocotb-config --makefiles)/Makefile.sim
