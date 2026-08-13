# sign_test.py — does heading go UP or DOWN when the car turns right?
from machine import Pin, I2C
import time, bno055

IMU_OFFSETS = bytearray(b'\xf7\xff\xeb\xff\x14\x00\x00\x00\x00\x00\x00\x00'
                        b'\x00\x00\xfc\xff\xff\xff\xe8\x03\x00\x00')

def ang_diff(new, old):
    d = new - old
    if d > 180:  d -= 360
    if d < -180: d += 360
    return d

Pin(10, Pin.OUT).value(0)
time.sleep_ms(100)
i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=100_000)
imu = bno055.BNO055(i2c, address=0x28)
imu.mode(bno055.IMUPLUS_MODE); time.sleep_ms(100)
imu.set_offsets(IMU_OFFSETS);  time.sleep_ms(100)
imu.mode(bno055.IMUPLUS_MODE); time.sleep_ms(500)

zero = imu.euler()[0]
print("zero =", round(zero, 2))
print("\nNow slowly turn the car to the RIGHT and stop.\n")

for i in range(150):                 # 30 seconds
    h = imu.euler()[0]
    print("  change from start: {:+7.2f}".format(ang_diff(h, zero)))
    time.sleep_ms(200)