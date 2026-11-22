import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge


# ---------------------------------------------------------------------------
# Yardımcı fonksiyon: saati başlat ve reset uygula.
# TX testindekiyle aynı; tek fark, sürdüğümüz giriş artık rx.
# ---------------------------------------------------------------------------
async def reset_dut(dut):
    # Saat: 10 ns periyot = 100 MHz
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    # UART hattı boştayken 1'dir. 0 bırakırsak RX bunu start biti sanar.
    dut.rx.value = 1

    dut.rst.value = 1
    await ClockCycles(dut.clk, 5)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 2)


# ---------------------------------------------------------------------------
# Yardımcı fonksiyon: rx hattından bir bayt gönder (TX'in yaptığı işi Python yapıyor).
# stop_bit=0 verirsek bilerek hatalı çerçeve üretiriz.
# ---------------------------------------------------------------------------
async def send_byte(dut, byte, stop_bit=1):
    clks = int(dut.CLK_PER_BIT.value)

    # Start biti
    dut.rx.value = 0
    await ClockCycles(dut.clk, clks)

    # 8 veri biti, LSB önce
    for i in range(8):
        dut.rx.value = (byte >> i) & 1
        await ClockCycles(dut.clk, clks)

    # Stop biti
    dut.rx.value = stop_bit
    await ClockCycles(dut.clk, clks)

    # Hattı boşa bırak
    dut.rx.value = 1


# ---------------------------------------------------------------------------
# Monitör: arka planda sürekli çalışır, her saat kenarında çıkışlara bakar.
# rx_valid gelirse baytı, rx_frame_err gelirse bir işareti listeye ekler.
# Böylece testler "ne geldi?" sorusunu listelere bakarak cevaplar.
# rx_valid 1 çevrimlik darbe olduğu için her bayt listeye tam bir kez girer;
# darbe uzun olsaydı aynı bayt birden çok kez eklenir ve test yakalardı.
# ---------------------------------------------------------------------------
async def monitor(dut, received, errors):
    while True:
        await RisingEdge(dut.clk)
        if dut.rx_valid.value == 1:
            received.append(int(dut.rx_data.value))
        if dut.rx_frame_err.value == 1:
            errors.append(1)


# ---------------------------------------------------------------------------
# TEST 1: Reset'ten sonra çıkışlar sessiz olmalı
# ---------------------------------------------------------------------------
@cocotb.test()
async def test_idle_after_reset(dut):
    await reset_dut(dut)

    assert dut.rx_valid.value == 0, "Reset sonrası rx_valid 0 olmalı"
    assert dut.rx_frame_err.value == 0, "Reset sonrası rx_frame_err 0 olmalı"


# ---------------------------------------------------------------------------
# TEST 2: Tek bayt gönder, rx_valid'i bekle, rx_data'yı kontrol et
# ---------------------------------------------------------------------------
@cocotb.test()
async def test_single_byte(dut):
    await reset_dut(dut)
    gonderilen = 0x41  # 'A'

    # send_byte'ı arka planda başlat: o hattı sürerken biz çıkışı bekleyebilelim.
    # (await send_byte(...) deseydik, gönderim bitene kadar burada beklerdik ve
    #  rx_valid darbesini kaçırırdık; çünkü darbe stop bitinin ortasında geliyor.)
    cocotb.start_soon(send_byte(dut, gonderilen))

    await RisingEdge(dut.rx_valid)
    alinan = int(dut.rx_data.value)

    assert alinan == gonderilen, f"Gönderilen 0x{gonderilen:02X}, alınan 0x{alinan:02X}"
    dut._log.info(f"Başarılı: 0x{alinan:02X} doğru alındı")


# ---------------------------------------------------------------------------
# TEST 3: Rastgele 20 baytı arada boşluk bırakmadan arka arkaya gönder.
# STOP'u yarım bitte bitirmeseydik bu test kaymanın birikmesini yakalardı.
# ---------------------------------------------------------------------------
@cocotb.test()
async def test_back_to_back(dut):
    await reset_dut(dut)
    clks = int(dut.CLK_PER_BIT.value)

    received, errors = [], []
    cocotb.start_soon(monitor(dut, received, errors))

    gonderilenler = [random.randint(0, 255) for _ in range(20)]
    for b in gonderilenler:
        await send_byte(dut, b)  # biri bitince hemen diğeri başlıyor

    # Son baytın çıkışa ulaşması için biraz bekle
    await ClockCycles(dut.clk, 2 * clks)

    assert errors == [], f"Beklenmeyen frame error: {len(errors)} adet"
    assert received == gonderilenler, (
        f"\nGönderilen: {[hex(b) for b in gonderilenler]}"
        f"\nAlınan:     {[hex(b) for b in received]}"
    )
    dut._log.info(f"Başarılı: {len(received)} bayt sırayla doğru alındı")


# ---------------------------------------------------------------------------
# TEST 4: Kısa bir 0 darbesi (glitch) start biti sanılmamalı
# ---------------------------------------------------------------------------
@cocotb.test()
async def test_glitch(dut):
    await reset_dut(dut)
    clks = int(dut.CLK_PER_BIT.value)

    received, errors = [], []
    cocotb.start_soon(monitor(dut, received, errors))

    # 2 çevrimlik 0 darbesi: yarım bitten kısa, START ortasında hat 1'e dönmüş olacak
    dut.rx.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rx.value = 1

    # Bir tam çerçeveden uzun bekle; hiçbir şey çıkmamalı
    await ClockCycles(dut.clk, 12 * clks)

    assert received == [], f"Glitch bayt olarak alındı: {[hex(b) for b in received]}"
    assert errors == [], "Glitch frame error üretti"

    # Glitch'ten sonra RX hâlâ normal çalışıyor mu?
    await send_byte(dut, 0x5A)
    await ClockCycles(dut.clk, 2 * clks)
    assert received == [0x5A], f"Glitch sonrası bayt alınamadı: {received}"


# ---------------------------------------------------------------------------
# TEST 5: Stop biti 0 gelirse rx_frame_err vermeli, rx_valid vermemeli
# ---------------------------------------------------------------------------
@cocotb.test()
async def test_frame_error(dut):
    await reset_dut(dut)
    clks = int(dut.CLK_PER_BIT.value)

    received, errors = [], []
    cocotb.start_soon(monitor(dut, received, errors))

    await send_byte(dut, 0x3C, stop_bit=0)
    await ClockCycles(dut.clk, 3 * clks)

    assert len(errors) == 1, f"1 frame error bekleniyordu, {len(errors)} geldi"
    assert received == [], f"Hatalı çerçeve geçerli sayıldı: {[hex(b) for b in received]}"
