# motor_check.py
from machine import Pin, PWM
import time

pwma = PWM(Pin(2)); pwma.freq(1000)
ain1 = Pin(3, Pin.OUT); ain2 = Pin(4, Pin.OUT); stby = Pin(5, Pin.OUT)

def motor(duty, direction):
    if direction == 0:
        stby.value(0); pwma.duty_u16(0); ain1.value(0); ain2.value(0); return
    stby.value(1)
    ain1.value(1 if direction > 0 else 0)
    ain2.value(0 if direction > 0 else 1)
    pwma.duty_u16(int(65535 * duty / 100))

try:
    print("direction A, 30%")
    motor(30, +1); time.sleep(3); motor(0, 0); time.sleep(1)

    print("direction B, 30%")
    motor(30, -1); time.sleep(3); motor(0, 0); time.sleep(2)

    print("\nduty sweep — note the lowest that actually turns the wheels")
    for d in range(5, 41, 5):
        print("  {}%".format(d))
        motor(d, -1); time.sleep(2.5); motor(0, 0); time.sleep(1)
finally:
    motor(0, 0); print("stopped")
