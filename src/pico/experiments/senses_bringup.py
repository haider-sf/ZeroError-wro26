# senses_bringup.py — 5x VL53L1X + BNO055 IMU on one I2C bus
#
# Bus: I2C0, SDA=GP8, SCL=GP9
# ToF SHUT pins: GP10..GP14  ->  addresses 0x30..0x34
# IMU: fixed at 0x28 (ADR soldered to GND)

from machine import Pin, I2C
import time
from PiicoDev_VL53L1X import PiicoDev_VL53L1X
import bno055

SHUT_PINS = [10, 11, 12, 13, 14]
TOF_ADDRS = [0x30, 0x31, 0x32, 0x33, 0x34]
BUS_FREQ  = 100000

# ---------- 1. Hold ALL ToF sensors in reset ----------
shut = [Pin(p, Pin.OUT) for p in SHUT_PINS]
for s in shut:
    s.value(0)
time.sleep_ms(100)

i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=BUS_FREQ)
print("bus with all ToF off:", [hex(a) for a in i2c.scan()])
# expect ['0x28'] — the IMU alone. If 0x29 appears here, a ToF isn't held off.

# ---------- 2. Bring up the IMU first ----------
# The IMU is at 0x28, so it never conflicts with the 0x29 readdressing workspace.
imu = bno055.BNO055(i2c, address=0x28)
imu.mode(bno055.IMUPLUS_MODE)      # gyro + accel, no magnetometer
time.sleep_ms(100)
print("IMU up at 0x28, mode=IMUPLUS")

# ---------- 3. Bring up ToF sensors one at a time ----------
# Each is alone at 0x29 when woken, so its rename is unambiguous.
tofs = []
for i in range(len(shut)):
    shut[i].value(1)
    time.sleep_ms(100)
    s = PiicoDev_VL53L1X(bus=0, freq=BUS_FREQ, sda=8, scl=9, address=0x29)
    s.change_addr(TOF_ADDRS[i])
    time.sleep_ms(50)
    tofs.append(s)
    print("  ToF", i, "->", hex(TOF_ADDRS[i]))

# ---------- 4. Confirm everyone is present ----------
i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=BUS_FREQ)
found = [hex(a) for a in i2c.scan()]
print("final bus:", found)
# expect ['0x28','0x30','0x31','0x32','0x33','0x34']

# ---------- 5. Wait for IMU calibration ----------
print("\nCalibrate IMU: hold STILL (gyro), then TILT through faces (accel)...")
while True:
    c = imu.cal_status()
    print("  gyro:{} accel:{}   (sys:{} mag:{} - ignore)".format(c[1], c[2], c[0], c[3]))
    if c[1] == 3 and c[2] == 3:
        print("IMU calibrated.\n")
        break
    time.sleep(0.5)

# ---------- 6. Read everything together ----------
try:
    while True:
        heading = imu.euler()[0]
        parts = []
        for i, t in enumerate(tofs):
            d = t.read()
            flag = "" if t.status == "OK" else "!"
            parts.append("S{}:{}{}".format(i, d, flag))
        print("hdg:{:6.1f}   {}".format(heading, "  ".join(parts)))
        time.sleep(0.1)
except KeyboardInterrupt:
    print("stopped")