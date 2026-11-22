import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, RisingEdge


# ---------------------------------------------------------------------------
# Yardımcı fonksiyon: saati başlat ve reset uygula.
# Her testin başında aynı işi yaptığımız için bir kez yazıp tekrar kullanıyoruz.
# ---------------------------------------------------------------------------
async def reset_dut(dut):
    # Saat: 10 ns periyot = 100 MHz. start_soon -> arka planda sürekli çalışır.
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    # Girişlere başlangıç değeri ver (yoksa simülasyonda 'x' = bilinmiyor olurlar)
    dut.tx_start.value = 0
    dut.tx_data.value = 0

    # Reset'i 5 çevrim boyunca 1 tut, sonra bırak
    dut.rst.value = 1
    await ClockCycles(dut.clk, 5)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 2)


# ---------------------------------------------------------------------------
# TEST 1: Reset'ten sonra hat boşta (idle) olmalı -> tx = 1, tx_busy = 0
# ---------------------------------------------------------------------------
@cocotb.test()
async def test_idle_after_reset(dut):
    await reset_dut(dut)

    assert dut.tx.value == 1, "Reset sonrası tx 1 olmalı (idle)"
    assert dut.tx_busy.value == 0, "Reset sonrası tx_busy 0 olmalı"


# ---------------------------------------------------------------------------
# TEST 2: Bir bayt gönder, tx hattını izleyerek baytı geri oku
# ---------------------------------------------------------------------------
@cocotb.test()
async def test_send_byte(dut):
    await reset_dut(dut)

    # Bit süresini Verilog'daki parametreden oku (Makefile'da 8 yaptık)
    clks = int(dut.CLK_PER_BIT.value)
    gonderilen = 0x41  # 'A' karakteri

    # --- Gönderimi başlat: veriyi koy ve tx_start'ı 1 yap ---
    await RisingEdge(dut.clk)
    dut.tx_data.value = gonderilen
    dut.tx_start.value = 1

    # --- Start bitinin başlamasını bekle (tx: 1 -> 0) ---
    await FallingEdge(dut.tx)
    dut.tx_start.value = 0  # darbe bitti, tx_start'ı geri çek

    # --- Start bitinin ORTASINA git ve kontrol et ---
    await ClockCycles(dut.clk, clks // 2)
    assert dut.tx.value == 0, "Start biti 0 olmalı"

    # --- 8 veri biti: her seferinde 1 bit süresi ilerle, bitin ortasında oku ---
    alinan = 0
    for i in range(8):
        await ClockCycles(dut.clk, clks)
        bit = int(dut.tx.value)
        alinan = alinan | (bit << i)  # LSB önce geldiği için i. bit konumuna yerleştir

    # --- Stop biti ---
    await ClockCycles(dut.clk, clks)
    assert dut.tx.value == 1, "Stop biti 1 olmalı"

    # --- Sonuç: gönderilen ile okunan aynı mı? ---
    assert alinan == gonderilen, f"Gönderilen 0x{gonderilen:02X}, okunan 0x{alinan:02X}"
    dut._log.info(f"Başarılı: 0x{alinan:02X} doğru alındı")
