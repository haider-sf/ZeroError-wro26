# motor_minimal.py — no PWM, just prove the driver conducts.
# Wheels OFF the ground. Buck 5V on VM. Grounds common.

from machine import Pin
import time

STBY = Pin(5, Pin.OUT)
AIN1 = Pin(3, Pin.OUT)
AIN2 = Pin(4, Pin.OUT)
PWMA = Pin(2, Pin.OUT)   # driven as a plain HIGH, not PWM, for this test

def run():
    STBY.value(1)   # wake the driver
    AIN1.value(1)   # direction: forward
    AIN2.value(0)
    PWMA.value(1)   # full speed (PWMA high = 100% on)

def stop():
    PWMA.value(0)
    AIN1.value(0)
    AIN2.value(0)
    STBY.value(0)

try:
    print("driver ON — motor should spin now")
    run()
    time.sleep(2)
finally:
    stop()
    print("stopped")