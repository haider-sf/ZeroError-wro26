# senses_bringup.py — 5x VL53L1X + BNO055 IMU, calibration restored from saved offsets
from machine import Pin, I2C
import time
from PiicoDev_VL53L1X import PiicoDev_VL53L1X
import bno055

SHUT_PINS = [10, 11, 12, 13, 14]
TOF_ADDRS = [0x30, 0x31, 0x32, 0x33, 0x34]
BUS_FREQ  = 100000

# saved IMU calibration (captured once with sensor_offsets())
IMU_OFFSETS = bytearray(b'\xf7\xff\xeb\xff\x14\x00\x00\x00\x00\x00\x00\x00\x00\x00\xfc\xff\xff\xff\xe8\x03\x00\x00')

# ---------- 1. All ToF OFF ----------
shut = [Pin(p, Pin.OUT) for p in SHUT_PINS]
for s in shut:
    s.value(0)
time.sleep_ms(100)

i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=BUS_FREQ)
print("bus with all ToF off:", [hex(a) for a in i2c.scan()])

# ---------- 2. Wake the ToF sensors ----------
tofs = []
for i in range(len(shut)):
    shut[i].value(1)
    time.sleep_ms(100)
    s = PiicoDev_VL53L1X(bus=0, freq=BUS_FREQ, sda=8, scl=9, address=0x29)
    s.change_addr(TOF_ADDRS[i])
    time.sleep_ms(50)
    tofs.append(s)
    print("  ToF", i, "->", hex(TOF_ADDRS[i]))

i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=BUS_FREQ)
print("final ToF bus:", [hex(a) for a in i2c.scan()])

# ---------- 3. Bring up the IMU LAST, then load calibration ----------
# IMU comes up after ToF so the bus is already settled — no re-init dance.
imu = bno055.BNO055(i2c, address=0x28)
imu.mode(bno055.IMUPLUS_MODE)
time.sleep_ms(100)

imu.set_offsets(IMU_OFFSETS)        # restore saved calibration
time.sleep_ms(100)
imu.mode(bno055.IMUPLUS_MODE)       # ensure still in fusion mode after offset write
time.sleep_ms(100)

c = imu.cal_status()
print("IMU up, mode:", imu.mode(), "cal:", list(c))

# ---------- 4. Read everything ----------
print("\nrunning\n")
try:
    while True:
        h, r, p = imu.euler()
        c = imu.cal_status()
        parts = []
        for i, t in enumerate(tofs):
            d = t.read()
            flag = "" if t.status == "OK" else "!"
            parts.append("S{}:{}{}".format(i, d, flag))
        print("hdg:{:6.1f} [g{} a{}]   {}".format(h, c[1], c[2], "  ".join(parts)))
        time.sleep(0.1)
except KeyboardInterrupt:
    print("stopped")