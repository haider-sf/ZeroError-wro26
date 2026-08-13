from machine import Pin, I2C
import time
from PiicoDev_VL53L1X import PiicoDev_VL53L1X

SHUT_PINS = [10, 11, 12, 13, 14]
ADDRS     = [0x30, 0x31, 0x32, 0x33, 0x34]   # each sensor's final address
BUS_FREQ  = 100000                           # 100 kHz for reliable bring-up

shut = [Pin(p, Pin.OUT) for p in SHUT_PINS]

# 1. hold ALL sensors in reset
for s in shut:
    s.value(0)
time.sleep_ms(100)

# sanity: bus should be empty with everything off
i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=BUS_FREQ)
print("all off:", [hex(a) for a in i2c.scan()])   # expect []

# 2. bring up one at a time — each is ALONE at 0x29 when woken, so rename is unambiguous
tofs = []
for i in range(len(shut)):
    shut[i].value(1)                             # wake ONLY sensor i
    time.sleep_ms(100)
    s = PiicoDev_VL53L1X(bus=0, freq=BUS_FREQ, sda=8, scl=9, address=0x29)
    s.change_addr(ADDRS[i])
    time.sleep_ms(50)
    tofs.append(s)
    print("sensor", i, "->", hex(ADDRS[i]))

# 3. confirm all five present at distinct addresses
i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=BUS_FREQ)
print("bus now:", [hex(a) for a in i2c.scan()])   # expect ['0x30','0x31','0x32','0x33','0x34']
try:
    while True:
        out = []
        for i, t in enumerate(tofs):
            d = t.read()
            flag = "" if t.status == "OK" else "!" + t.status
            out.append("S{}:{}{}".format(i, d, flag))
        print("  ".join(out))
        time.sleep(0.1)
except KeyboardInterrupt:
    print("stopped")