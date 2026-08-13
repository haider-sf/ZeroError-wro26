# motor_smoke.py — does it spin, which way is forward, does it get hot
from machine import Pin, PWM
import time

pwma = PWM(Pin(2)); pwma.freq(1000)
ain1 = Pin(3, Pin.OUT)
ain2 = Pin(4, Pin.OUT)
stby = Pin(5, Pin.OUT)

def motor(duty_pct, direction):
    """direction: +1, -1, or 0 for standby (driver off)."""
    if direction == 0:
        stby.value(0); pwma.duty_u16(0)
        ain1.value(0); ain2.value(0)
        return
    stby.value(1)
    ain1.value(1 if direction > 0 else 0)
    ain2.value(0 if direction > 0 else 1)
    pwma.duty_u16(int(65535 * duty_pct / 100))

try:
    print("30% direction A — watch which way the wheels turn")
    motor(30, +1); time.sleep(3)

    motor(0, 0); time.sleep(1)

    print("30% direction B")
    motor(30, -1); time.sleep(3)

finally:
    motor(0, 0)
    print("stopped")