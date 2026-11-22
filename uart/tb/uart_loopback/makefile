# Hangi simülatör: Icarus Verilog
SIM ?= icarus

# Tasarım dili
TOPLEVEL_LANG = verilog

# Üst modül + içindeki TX, RX ve senkronizör (hepsi birlikte derlenmeli)
VERILOG_SOURCES = $(PWD)/../../rtl/uart_top.v \
                  $(PWD)/../../rtl/uart_tx.v \
                  $(PWD)/../../rtl/uart_rx.v \
                  $(PWD)/../../../common/rtl/basicff.v

# Test edilecek modülün adı (Verilog'daki "module uart_top")
COCOTB_TOPLEVEL = uart_top

# Python test dosyasının adı (.py olmadan)
COCOTB_TEST_MODULES = test_uart_loopback

# Simülasyonu hızlandırmak için küçük bölenler:
#   TX_CPB = 100e6 / 10e6 = 10
#   RX_CPB = 153e6 / 10e6 = 15.3 -> 15  (tamsayı yuvarlaması: RX ~%2 hızlı)
# Saat periyotları testte bu frekanslardan hesaplanıyor.
CLKA_HZ ?= 100000000
CLKB_HZ ?= 153000000
BAUD    ?= 10000000
COMPILE_ARGS += -Puart_top.CLKA_HZ=$(CLKA_HZ) \
                -Puart_top.CLKB_HZ=$(CLKB_HZ) \
                -Puart_top.BAUD=$(BAUD)

# cocotb'nin hazır kuralları
include $(shell cocotb-config --makefiles)/Makefile.sim
