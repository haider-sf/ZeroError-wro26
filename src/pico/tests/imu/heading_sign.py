# heading_sign.py — confirm the convention on the rebuilt car
from machine import Pin, I2C
import time, bno055

IMU_OFFSETS = bytearray(b'\xf7\xff\xeb\xff\x14\x00\x00\x00\x00\x00\x00\x00'
                        b'\x00\x00\xfc\xff\xff\xff\xe8\x03\x00\x00')

def ang_diff(new, old):
    """Wrap-safe. Folds the difference into ±180 so a 359.9 -> 0.1
    transition reads as +0.2, not -359.8."""
    d = new - old
    if d > 180:  d -= 360
    if d < -180: d += 360
    return d

Pin(10, Pin.OUT).value(0)          # ToF in reset, quiet bus
time.sleep_ms(100)
i2c = I2C(1, sda=Pin(6), scl=Pin(7), freq=100_000)
imu = bno055.BNO055(i2c, address=0x28)
imu.mode(bno055.IMUPLUS_MODE); time.sleep_ms(100)
imu.set_offsets(IMU_OFFSETS);  time.sleep_ms(100)
imu.mode(bno055.IMUPLUS_MODE); time.sleep_ms(500)

zero = imu.euler()[0]
print("zero = {:.2f}".format(zero))
print("\nTurn the car slowly RIGHT, stop, then LEFT past the start.\n")

for _ in range(150):               # 30 s
    h = imu.euler()[0]
    print("  raw={:7.2f}   change={:+7.2f}".format(h, ang_diff(h, zero)))
    time.sleep_ms(200)
