# 3_range.py — VL53L1X range verify
from machine import Pin, I2C
import time
import VL53L1X

i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=100000)   # back to 100 kHz
tof = VL53L1X.VL53L1X(i2c)      # constructor inits + starts ranging

try:
    while True:
        d = tof.read()          # distance in mm
        print(d, "mm")
        time.sleep(0.1)
except KeyboardInterrupt:
    print("stopped") 