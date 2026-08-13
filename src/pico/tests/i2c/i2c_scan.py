# i2c_scan.py — verify both devices and prove the XSHUT line works
from machine import Pin, I2C
import time

shut = Pin(10, Pin.OUT)          # GP10 = physical pin 14
i2c  = I2C(0, sda=Pin(8), scl=Pin(9), freq=100_000)

shut.value(0)                    # ToF held in reset
time.sleep_ms(150)
print("XSHUT low :", [hex(a) for a in i2c.scan()])

shut.value(1)                    # ToF released, boots at 0x29
time.sleep_ms(150)
print("XSHUT high:", [hex(a) for a in i2c.scan()])