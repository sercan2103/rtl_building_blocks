# Hangi simülatör: Icarus Verilog
SIM ?= icarus

# Tasarım dili
TOPLEVEL_LANG = verilog

# RX modülü + içinde kullandığı senkronizör (iki dosya birlikte derlenmeli)
VERILOG_SOURCES = $(PWD)/../../rtl/uart_rx.v \
                  $(PWD)/../../../common/rtl/basicff.v

# Test edilecek modülün adı (Verilog'daki "module uart_rx")
COCOTB_TOPLEVEL = uart_rx

# Python test dosyasının adı (.py olmadan)
COCOTB_TEST_MODULES = test_uart_rx

# Simülasyonu hızlandırmak için: CLK_PER_BIT parametresini 868 yerine 8 yap
COMPILE_ARGS += -Puart_rx.CLK_PER_BIT=8

# cocotb'nin hazır kuralları
include $(shell cocotb-config --makefiles)/Makefile.sim
