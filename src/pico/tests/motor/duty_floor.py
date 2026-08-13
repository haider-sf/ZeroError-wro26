# duty_floor.py — lowest duty that actually turns the wheels, in the chassis
from machine import Pin, PWM
import time

FORWARD = -1

pwma = PWM(Pin(2)); pwma.freq(1000)
ain1 = Pin(3, Pin.OUT); ain2 = Pin(4, Pin.OUT); stby = Pin(5, Pin.OUT)

def motor(duty_pct, direction):
    if direction == 0:
        stby.value(0); pwma.duty_u16(0); ain1.value(0); ain2.value(0); return
    stby.value(1)
    ain1.value(1 if direction > 0 else 0)
    ain2.value(0 if direction > 0 else 1)
    pwma.duty_u16(int(65535 * duty_pct / 100))

try:
    for d in range(5, 41, 5):
        print("duty {}% — turning?".format(d))
        motor(d, FORWARD)
        time.sleep(2.5)
        motor(0, 0)
        time.sleep(1)
finally:
    motor(0, 0)
    print("done")