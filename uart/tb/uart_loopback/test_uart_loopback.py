import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, RisingEdge, Timer


# ---------------------------------------------------------------------------
# Saat periyodunu frekanstan hesapla (ps cinsinden).
# Çift sayıya yuvarlıyoruz: Clock periyodu yarıya bölüp high/low yapıyor,
# tek sayı olursa yarım ps gerekir ve cocotb hata verir.
# ---------------------------------------------------------------------------
def period_ps(hz):
    return 2 * round(1e12 / hz / 2)


# ---------------------------------------------------------------------------
# Yardımcı fonksiyon: iki saati başlat ve reset uygula.
# clka (TX) ve clkb (RX) birbirinden bağımsız: farklı frekans, farklı faz.
# ---------------------------------------------------------------------------
async def reset_dut(dut):
    clka_hz = int(dut.CLKA_HZ.value)
    clkb_hz = int(dut.CLKB_HZ.value)
    baud = int(dut.BAUD.value)

    cocotb.start_soon(Clock(dut.clka, period_ps(clka_hz), unit="ps").start())
    # clkb'yi rastgele bir gecikmeyle başlat: iki saatin kenarları hizalı olmasın
    await Timer(random.randint(1, 1000), unit="ps")
    cocotb.start_soon(Clock(dut.clkb, period_ps(clkb_hz), unit="ps").start())

    # Bölenleri ve gerçek baud farkını logla (tolerans için önemli)
    tx_cpb = clka_hz // baud
    rx_cpb = clkb_hz // baud
    tx_bit = tx_cpb / clka_hz
    rx_bit = rx_cpb / clkb_hz
    dut._log.info(
        f"TX_CPB={tx_cpb}, RX_CPB={rx_cpb}, "
        f"baud farkı: %{100 * (tx_bit - rx_bit) / tx_bit:+.2f}"
    )

    dut.tx_start.value = 0
    dut.tx_data.value = 0

    # Reset her iki saatin de birkaç kenarını kapsasın
    dut.rst.value = 1
    await ClockCycles(dut.clka, 5)
    await ClockCycles(dut.clkb, 5)
    dut.rst.value = 0
    await ClockCycles(dut.clka, 2)


# ---------------------------------------------------------------------------
# Yardımcı fonksiyon: TX'e bir bayt ver.
# Girişleri clka'nın DÜŞEN kenarında değiştiriyoruz; böylece TX onları bir
# sonraki yükselen kenarda kararlı görür (yarış durumu yok).
# tx_busy 0 olana kadar bekler, sonra tx_start'ı 1 çevrim 1 yapar.
# ---------------------------------------------------------------------------
async def tx_send(dut, byte):
    await FallingEdge(dut.clka)
    while dut.tx_busy.value == 1:
        await FallingEdge(dut.clka)

    dut.tx_data.value = byte
    dut.tx_start.value = 1
    await FallingEdge(dut.clka)  # arada bir yükselen kenar geçti: TX baytı aldı
    dut.tx_start.value = 0


# ---------------------------------------------------------------------------
# Monitör: RX tarafında (clkb) arka planda çalışır.
# RX testindekiyle aynı mantık; sadece saat artık clkb.
# ---------------------------------------------------------------------------
async def monitor(dut, received, errors):
    while True:
        await RisingEdge(dut.clkb)
        if dut.rx_valid.value == 1:
            received.append(int(dut.rx_data.value))
        if dut.rx_frame_err.value == 1:
            errors.append(1)


# ---------------------------------------------------------------------------
# Son bayt RX'ten çıkana kadar bekle: TX boşalsın + bir çerçeve kadar daha.
# ---------------------------------------------------------------------------
async def wait_drain(dut):
    tx_cpb = int(dut.CLKA_HZ.value) // int(dut.BAUD.value)
    await FallingEdge(dut.clka)
    while dut.tx_busy.value == 1:
        await FallingEdge(dut.clka)
    await ClockCycles(dut.clka, 2 * tx_cpb)


def check(dut, sent, received, errors):
    assert errors == [], f"Beklenmeyen frame error: {len(errors)} adet"
    assert received == sent, (
        f"\nGönderilen: {[hex(b) for b in sent]}"
        f"\nAlınan:     {[hex(b) for b in received]}"
    )


# ---------------------------------------------------------------------------
# TEST 1: Reset sonrası hat 1 (boş), çıkışlar sessiz; sonra tek bayt
# ---------------------------------------------------------------------------
@cocotb.test()
async def test_single_byte(dut):
    await reset_dut(dut)

    # İç wire'a hiyerarşik erişim: uart_top içindeki "tx"
    assert dut.tx.value == 1, "Reset sonrası seri hat 1 (idle) olmalı"
    assert dut.tx_busy.value == 0, "Reset sonrası tx_busy 0 olmalı"

    received, errors = [], []
    cocotb.start_soon(monitor(dut, received, errors))

    await tx_send(dut, 0xA5)
    await wait_drain(dut)

    check(dut, [0xA5], received, errors)
    dut._log.info("Başarılı: 0xA5 TX -> RX döngüsünü tamamladı")


# ---------------------------------------------------------------------------
# TEST 2: 0..255 tüm değerler, arka arkaya (TX boşalır boşalmaz yeni bayt).
# Çerçeveler arasında boşluk yok: RX'in STOP'u yarım bitte bitirmesi ve
# baud farkının birikmemesi burada sınanıyor.
# ---------------------------------------------------------------------------
@cocotb.test()
async def test_all_values_back_to_back(dut):
    await reset_dut(dut)

    received, errors = [], []
    cocotb.start_soon(monitor(dut, received, errors))

    sent = list(range(256))
    for b in sent:
        await tx_send(dut, b)
    await wait_drain(dut)

    check(dut, sent, received, errors)
    dut._log.info(f"Başarılı: {len(received)} bayt sırayla doğru alındı")


# ---------------------------------------------------------------------------
# TEST 3: Rastgele baytlar, aralarında rastgele boşluklar.
# Boşluklar bit süresinin katı değil: start biti RX saatine göre her seferinde
# farklı fazda geliyor (asenkron saat alanları).
# ---------------------------------------------------------------------------
@cocotb.test()
async def test_random_gaps(dut):
    await reset_dut(dut)
    tx_cpb = int(dut.CLKA_HZ.value) // int(dut.BAUD.value)

    received, errors = [], []
    cocotb.start_soon(monitor(dut, received, errors))

    sent = [random.randint(0, 255) for _ in range(50)]
    for b in sent:
        await tx_send(dut, b)
        if random.random() < 0.5:
            await ClockCycles(dut.clka, random.randint(1, 3 * tx_cpb))
    await wait_drain(dut)

    check(dut, sent, received, errors)
    dut._log.info(f"Başarılı: {len(received)} bayt (rastgele boşluklu) doğru alındı")
